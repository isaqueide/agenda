require('dotenv').config();

const express = require('express');
const fs = require('fs/promises');
const path = require('path');
const cron = require('node-cron');
const { v4: uuidv4 } = require('uuid');

const app = express();

const PORT = Number(process.env.PORT || 3000);
const DATA_FILE = path.join(__dirname, 'data', 'tasks.json');
const REMINDER_MINUTES_BEFORE = Number(process.env.REMINDER_MINUTES_BEFORE || 60);
const CRON_SCHEDULE = process.env.CRON_SCHEDULE || '*/5 * * * *';
const TELEGRAM_BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN || '';
const TELEGRAM_CHAT_ID = process.env.TELEGRAM_CHAT_ID || '';

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

const DEFAULT_DB = {
  tasks: []
};

async function ensureDb() {
  try {
    await fs.access(DATA_FILE);
  } catch {
    await fs.mkdir(path.dirname(DATA_FILE), { recursive: true });
    await fs.writeFile(DATA_FILE, JSON.stringify(DEFAULT_DB, null, 2));
  }
}

async function readDb() {
  await ensureDb();
  const raw = await fs.readFile(DATA_FILE, 'utf-8');
  return JSON.parse(raw);
}

async function writeDb(db) {
  await fs.writeFile(DATA_FILE, JSON.stringify(db, null, 2));
}

function computeStatus(task, now = new Date()) {
  if (task.archivedAt) return 'archived';
  if (task.completedAt) return 'completed';

  const due = new Date(task.dueDateTime);
  if (Number.isNaN(due.getTime())) return 'pending';
  if (due < now) return 'overdue';
  return 'pending';
}

function formatTelegramMessage(task, type) {
  const dueText = new Date(task.dueDateTime).toLocaleString('pt-BR', {
    dateStyle: 'short',
    timeStyle: 'short'
  });

  if (type === 'before_due') {
    return [
      '⏰ *Lembrete de tarefa*',
      `A tarefa *${task.title}* vence em breve.`,
      `Prazo: ${dueText}`,
      task.description ? `Descrição: ${task.description}` : ''
    ].filter(Boolean).join('\n');
  }

  return [
    '🚨 *Tarefa atrasada*',
    `A tarefa *${task.title}* está atrasada.`,
    `Prazo: ${dueText}`,
    task.description ? `Descrição: ${task.description}` : ''
  ].filter(Boolean).join('\n');
}

async function sendTelegramMessage(message) {
  if (!TELEGRAM_BOT_TOKEN || !TELEGRAM_CHAT_ID) {
    return { sent: false, reason: 'Telegram desabilitado (faltam variáveis de ambiente).' };
  }

  const endpoint = `https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`;
  const response = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      chat_id: TELEGRAM_CHAT_ID,
      text: message,
      parse_mode: 'Markdown'
    })
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Erro ao enviar Telegram (${response.status}): ${body}`);
  }

  return { sent: true };
}

function validateTaskPayload(payload) {
  if (!payload || typeof payload !== 'object') {
    return 'Payload inválido.';
  }

  if (!payload.title || typeof payload.title !== 'string' || !payload.title.trim()) {
    return 'O título é obrigatório.';
  }

  if (!payload.dueDateTime || Number.isNaN(new Date(payload.dueDateTime).getTime())) {
    return 'Prazo inválido. Informe data e hora válidas.';
  }

  if (payload.description && typeof payload.description !== 'string') {
    return 'A descrição deve ser texto.';
  }

  return null;
}

async function processNotifications() {
  const db = await readDb();
  const now = new Date();

  for (const task of db.tasks) {
    if (task.completedAt || task.archivedAt) {
      continue;
    }

    const dueDate = new Date(task.dueDateTime);
    if (Number.isNaN(dueDate.getTime())) {
      continue;
    }

    const msBeforeDue = dueDate.getTime() - now.getTime();
    const minutesBeforeDue = msBeforeDue / (1000 * 60);

    const shouldWarnBeforeDue =
      minutesBeforeDue <= REMINDER_MINUTES_BEFORE &&
      minutesBeforeDue > 0 &&
      !task.notifiedBeforeDue;

    if (shouldWarnBeforeDue) {
      try {
        await sendTelegramMessage(formatTelegramMessage(task, 'before_due'));
        task.notifiedBeforeDue = true;
      } catch (error) {
        console.error('[Telegram] falha lembrete antes do prazo:', error.message);
      }
    }

    const isOverdue = minutesBeforeDue <= 0;
    if (isOverdue && !task.notifiedOverdue) {
      try {
        await sendTelegramMessage(formatTelegramMessage(task, 'overdue'));
        task.notifiedOverdue = true;
      } catch (error) {
        console.error('[Telegram] falha alerta atrasado:', error.message);
      }
    }
  }

  await writeDb(db);
}

app.get('/api/health', (_req, res) => {
  res.json({ ok: true, time: new Date().toISOString() });
});

app.get('/api/tasks', async (req, res, next) => {
  try {
    const { filter = 'all', includeArchived = 'false' } = req.query;
    const db = await readDb();
    const now = new Date();

    const tasks = db.tasks
      .map((task) => ({ ...task, status: computeStatus(task, now) }))
      .filter((task) => {
        if (includeArchived !== 'true' && task.archivedAt) return false;

        switch (filter) {
          case 'pending':
            return task.status === 'pending';
          case 'completed':
            return task.status === 'completed';
          case 'overdue':
            return task.status === 'overdue';
          case 'archived':
            return task.status === 'archived';
          default:
            return true;
        }
      })
      .sort((a, b) => new Date(a.dueDateTime) - new Date(b.dueDateTime));

    res.json({ tasks });
  } catch (error) {
    next(error);
  }
});

app.post('/api/tasks', async (req, res, next) => {
  try {
    const errorMessage = validateTaskPayload(req.body);
    if (errorMessage) return res.status(400).json({ error: errorMessage });

    const db = await readDb();

    const task = {
      id: uuidv4(),
      title: req.body.title.trim(),
      description: req.body.description?.trim() || '',
      createdAt: new Date().toISOString(),
      dueDateTime: new Date(req.body.dueDateTime).toISOString(),
      completedAt: null,
      archivedAt: null,
      notifiedBeforeDue: false,
      notifiedOverdue: false
    };

    db.tasks.push(task);
    await writeDb(db);

    res.status(201).json({ task: { ...task, status: computeStatus(task) } });
  } catch (error) {
    next(error);
  }
});

app.put('/api/tasks/:id', async (req, res, next) => {
  try {
    const errorMessage = validateTaskPayload(req.body);
    if (errorMessage) return res.status(400).json({ error: errorMessage });

    const db = await readDb();
    const task = db.tasks.find((item) => item.id === req.params.id);

    if (!task) return res.status(404).json({ error: 'Tarefa não encontrada.' });

    task.title = req.body.title.trim();
    task.description = req.body.description?.trim() || '';
    task.dueDateTime = new Date(req.body.dueDateTime).toISOString();

    const due = new Date(task.dueDateTime);
    const now = new Date();
    task.notifiedBeforeDue = due > now ? false : task.notifiedBeforeDue;
    task.notifiedOverdue = due > now ? false : task.notifiedOverdue;

    await writeDb(db);

    res.json({ task: { ...task, status: computeStatus(task) } });
  } catch (error) {
    next(error);
  }
});

app.patch('/api/tasks/:id/complete', async (req, res, next) => {
  try {
    const db = await readDb();
    const task = db.tasks.find((item) => item.id === req.params.id);

    if (!task) return res.status(404).json({ error: 'Tarefa não encontrada.' });
    if (task.archivedAt) return res.status(400).json({ error: 'Tarefa arquivada não pode ser alterada.' });

    task.completedAt = task.completedAt ? null : new Date().toISOString();
    await writeDb(db);

    res.json({ task: { ...task, status: computeStatus(task) } });
  } catch (error) {
    next(error);
  }
});

app.patch('/api/tasks/:id/archive', async (req, res, next) => {
  try {
    const db = await readDb();
    const task = db.tasks.find((item) => item.id === req.params.id);

    if (!task) return res.status(404).json({ error: 'Tarefa não encontrada.' });
    if (!task.completedAt) return res.status(400).json({ error: 'Conclua a tarefa antes de arquivar.' });

    task.archivedAt = task.archivedAt ? null : new Date().toISOString();
    await writeDb(db);

    res.json({ task: { ...task, status: computeStatus(task) } });
  } catch (error) {
    next(error);
  }
});

app.delete('/api/tasks/:id', async (req, res, next) => {
  try {
    const db = await readDb();
    const initialLength = db.tasks.length;
    db.tasks = db.tasks.filter((item) => item.id !== req.params.id);

    if (db.tasks.length === initialLength) {
      return res.status(404).json({ error: 'Tarefa não encontrada.' });
    }

    await writeDb(db);
    res.status(204).send();
  } catch (error) {
    next(error);
  }
});

app.use((err, _req, res, _next) => {
  console.error('[Erro interno]', err);
  res.status(500).json({ error: 'Erro interno no servidor.' });
});

async function start() {
  await ensureDb();

  cron.schedule(CRON_SCHEDULE, async () => {
    try {
      await processNotifications();
    } catch (error) {
      console.error('[Cron] falha ao processar notificações:', error.message);
    }
  });

  app.listen(PORT, () => {
    console.log(`Agenda disponível em http://localhost:${PORT}`);
    console.log(`Cron ativo (${CRON_SCHEDULE}) | alerta antes: ${REMINDER_MINUTES_BEFORE} min`);
  });
}

start().catch((error) => {
  console.error('Falha ao iniciar servidor:', error);
  process.exit(1);
});
