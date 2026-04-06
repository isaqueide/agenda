const state = {
  filter: 'all',
  tasks: []
};

const elements = {
  form: document.querySelector('#task-form'),
  taskId: document.querySelector('#task-id'),
  title: document.querySelector('#title'),
  description: document.querySelector('#description'),
  dueDateTime: document.querySelector('#dueDateTime'),
  formTitle: document.querySelector('#form-title'),
  cancelEdit: document.querySelector('#cancel-edit'),
  formError: document.querySelector('#form-error'),
  taskList: document.querySelector('#task-list'),
  template: document.querySelector('#task-template'),
  refresh: document.querySelector('#refresh'),
  toggleTheme: document.querySelector('#toggle-theme')
};

function fmtDate(value) {
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? 'sem data'
    : date.toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' });
}

function statusLabel(status) {
  if (status === 'completed') return 'Concluída';
  if (status === 'overdue') return 'Atrasada';
  if (status === 'archived') return 'Arquivada';
  return 'Pendente';
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...options
  });

  if (response.status === 204) return null;

  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || 'Erro na requisição');
  return payload;
}

async function loadTasks() {
  const { tasks } = await api(`/api/tasks?filter=${state.filter}&includeArchived=true`);
  state.tasks = tasks;
  renderTasks();
}

function renderTasks() {
  elements.taskList.innerHTML = '';

  if (!state.tasks.length) {
    elements.taskList.innerHTML = '<p>Nenhuma tarefa nesse filtro.</p>';
    return;
  }

  for (const task of state.tasks) {
    const clone = elements.template.content.cloneNode(true);
    const card = clone.querySelector('.task-card');
    const title = clone.querySelector('.task-title');
    const description = clone.querySelector('.task-description');
    const meta = clone.querySelector('.task-meta');
    const badge = clone.querySelector('.badge');
    const actions = clone.querySelector('.card-actions');

    card.dataset.id = task.id;
    const classMap = {
      completed: 'done',
      pending: 'pending',
      overdue: 'overdue',
      archived: 'archived'
    };
    card.classList.add(classMap[task.status] || 'pending');

    title.textContent = task.title;
    description.textContent = task.description || 'Sem descrição';
    meta.textContent = `Criada em ${fmtDate(task.createdAt)} · Prazo ${fmtDate(task.dueDateTime)}`;
    badge.textContent = statusLabel(task.status);

    const editBtn = createActionButton('Editar', () => startEdit(task));
    const deleteBtn = createActionButton('Excluir', () => removeTask(task.id));
    const completeBtn = createActionButton(task.completedAt ? 'Reabrir' : 'Concluir', async () => {
      await toggleComplete(task.id);
      card.classList.add('completed-animate');
      setTimeout(() => card.classList.remove('completed-animate'), 500);
    });

    actions.append(editBtn, completeBtn, deleteBtn);

    if (task.completedAt) {
      const archiveBtn = createActionButton(task.archivedAt ? 'Desarquivar' : 'Arquivar', () => toggleArchive(task.id));
      actions.append(archiveBtn);
    }

    elements.taskList.append(clone);
  }
}

function createActionButton(label, onClick) {
  const btn = document.createElement('button');
  btn.className = 'btn';
  btn.type = 'button';
  btn.textContent = label;
  btn.addEventListener('click', async () => {
    try {
      await onClick();
      await loadTasks();
    } catch (error) {
      alert(error.message);
    }
  });
  return btn;
}

function startEdit(task) {
  elements.formTitle.textContent = 'Editar tarefa';
  elements.cancelEdit.hidden = false;
  elements.taskId.value = task.id;
  elements.title.value = task.title;
  elements.description.value = task.description || '';
  elements.dueDateTime.value = new Date(task.dueDateTime).toISOString().slice(0, 16);
  elements.title.focus();
}

function resetForm() {
  elements.form.reset();
  elements.formTitle.textContent = 'Nova tarefa';
  elements.cancelEdit.hidden = true;
  elements.taskId.value = '';
  elements.formError.textContent = '';
}

async function submitTask(event) {
  event.preventDefault();
  elements.formError.textContent = '';

  const payload = {
    title: elements.title.value,
    description: elements.description.value,
    dueDateTime: elements.dueDateTime.value
  };

  try {
    if (elements.taskId.value) {
      await api(`/api/tasks/${elements.taskId.value}`, {
        method: 'PUT',
        body: JSON.stringify(payload)
      });
    } else {
      await api('/api/tasks', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
    }

    resetForm();
    await loadTasks();
  } catch (error) {
    elements.formError.textContent = error.message;
  }
}

async function toggleComplete(id) {
  await api(`/api/tasks/${id}/complete`, { method: 'PATCH' });
}

async function toggleArchive(id) {
  await api(`/api/tasks/${id}/archive`, { method: 'PATCH' });
}

async function removeTask(id) {
  if (!confirm('Tem certeza que deseja excluir esta tarefa?')) return;
  await api(`/api/tasks/${id}`, { method: 'DELETE' });
}

function setupFilters() {
  const buttons = document.querySelectorAll('.filter-btn');
  buttons.forEach((btn) => {
    btn.addEventListener('click', async () => {
      buttons.forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      state.filter = btn.dataset.filter;
      await loadTasks();
    });
  });
}

function setupTheme() {
  const savedTheme = localStorage.getItem('theme') || 'light';
  document.documentElement.dataset.theme = savedTheme;

  elements.toggleTheme.addEventListener('click', () => {
    const next = document.documentElement.dataset.theme === 'light' ? 'dark' : 'light';
    document.documentElement.dataset.theme = next;
    localStorage.setItem('theme', next);
  });
}

elements.form.addEventListener('submit', submitTask);
elements.cancelEdit.addEventListener('click', resetForm);
elements.refresh.addEventListener('click', loadTasks);

setupFilters();
setupTheme();
loadTasks().catch((error) => {
  elements.taskList.innerHTML = `<p class="error">${error.message}</p>`;
});
