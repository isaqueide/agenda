# Agenda de Tarefas (Task Manager)

Aplicação web completa para gerenciamento de tarefas com dashboard responsivo e alertas via Telegram.

## Funcionalidades

- Criar tarefa com título, descrição opcional, data de criação automática e prazo com data/hora.
- Listar tarefas e filtrar por: pendentes, concluídas, atrasadas e histórico (arquivadas).
- Marcar tarefa como concluída/reaberta.
- Arquivar e desarquivar tarefas concluídas.
- Editar e excluir tarefas.
- Layout moderno com cards, animação suave ao concluir e dark mode.
- Cores por status:
  - ✅ Verde: concluída
  - 🟡 Amarelo: pendente
  - 🔴 Vermelho: atrasada

## Alertas Telegram

Serviço em segundo plano (cron job) verifica tarefas periodicamente para:

- Notificar **antes do prazo** (padrão: 60 minutos).
- Notificar quando a tarefa está **atrasada**.

Configure no arquivo `.env`:

```env
PORT=3000
TELEGRAM_BOT_TOKEN=seu_token
TELEGRAM_CHAT_ID=seu_chat_id
REMINDER_MINUTES_BEFORE=60
CRON_SCHEDULE=*/5 * * * *
```

> Se `TELEGRAM_BOT_TOKEN` ou `TELEGRAM_CHAT_ID` não forem informados, o app continua funcionando sem envio de mensagens.

## Executar localmente

```bash
npm install
cp .env.example .env
npm start
```

Abra: `http://localhost:3000`

## Endpoints principais

- `GET /api/tasks?filter=all|pending|completed|overdue|archived&includeArchived=true|false`
- `POST /api/tasks`
- `PUT /api/tasks/:id`
- `PATCH /api/tasks/:id/complete`
- `PATCH /api/tasks/:id/archive`
- `DELETE /api/tasks/:id`

## Deploy no GitHub

1. Suba o código no seu repositório GitHub.
2. Configure variáveis de ambiente no provedor de hospedagem (Render, Railway, Fly.io etc).
3. Use `npm start` como comando de execução.
