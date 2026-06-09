/**
 * Garden — Frontend Application
 * Vanilla JS · Single-page experience via view switching
 */

// ═══════════════════════════════════════════════════════════════════════
// State
// ═══════════════════════════════════════════════════════════════════════
const state = {
  userId: localStorage.getItem('garden_user_id') || null,
  email: localStorage.getItem('garden_email') || null,
  currentView: 'garden',
  contacts: [],
  garden: [],
  reminders: [],
  activeChatContact: null,
};

const API = '';  // same origin

// ═══════════════════════════════════════════════════════════════════════
// Helpers
// ═══════════════════════════════════════════════════════════════════════
async function api(url, opts = {}) {
  const res = await fetch(`${API}${url}`, {
    headers: { 'Content-Type': 'application/json', ...opts.headers },
    ...opts,
  });
  let data;
  try {
    data = await res.json();
  } catch {
    throw new Error('Сервер повернув некоректну відповідь');
  }
  if (res.status === 401 && url !== '/login' && url !== '/register') {
    // Сесія застаріла (БД скинулась після перезапуску) — перелогін
    logout();
    showToast('Сесія закінчилась. Увійдіть знову.', 'error');
    throw new Error('Session expired');
  }
  if (!res.ok) throw new Error(data.error || 'Щось пішло не так');
  return data;
}

function $(sel, ctx = document) { return ctx.querySelector(sel); }
function $$(sel, ctx = document) { return [...ctx.querySelectorAll(sel)]; }

function showToast(message, type = 'success') {
  const container = $('#toast-container');
  const el = document.createElement('div');
  el.className = `toast toast--${type}`;
  el.textContent = message;
  container.appendChild(el);
  setTimeout(() => el.remove(), 4000);
}

function formatDate(isoStr) {
  if (!isoStr) return '—';
  const d = new Date(isoStr);
  const now = new Date();
  const diff = Math.floor((now - d) / 86400000);
  if (diff === 0) return 'Сьогодні';
  if (diff === 1) return 'Вчора';
  if (diff < 7) return `${diff} дн. тому`;
  return d.toLocaleDateString('uk-UA', { day: 'numeric', month: 'short' });
}

function formatTime(isoStr) {
  if (!isoStr) return '';
  const d = new Date(isoStr);
  return d.toLocaleTimeString('uk-UA', { hour: '2-digit', minute: '2-digit' });
}

// ═══════════════════════════════════════════════════════════════════════
// Plant visual logic
// ═══════════════════════════════════════════════════════════════════════
function getPlantEmoji(growthLevel) {
  if (growthLevel >= 9) return '🌳';
  if (growthLevel >= 7) return '🌻';
  if (growthLevel >= 5) return '🌿';
  if (growthLevel >= 3) return '🌱';
  if (growthLevel >= 1) return '🫘';
  return '🥀';
}

function getPlantStatus(growthLevel, lastWatering, frequencyDays) {
  if (!lastWatering) return { status: 'withered', healthPct: 0, daysOverdue: 999 };

  const now = new Date();
  const last = new Date(lastWatering);
  const daysSince = Math.floor((now - last) / 86400000);
  const daysOverdue = Math.max(0, daysSince - (frequencyDays || 7));

  const baseHealth = 100;
  const penalty = daysOverdue * 15;
  const healthPct = Math.max(0, baseHealth - penalty);

  let status;
  if (healthPct >= 80) status = 'thriving';
  else if (healthPct >= 50) status = 'healthy';
  else if (healthPct > 0) status = 'wilting';
  else status = 'withered';

  return { status, healthPct, daysOverdue };
}

function getStatusLabel(status) {
  const labels = {
    thriving: '🌟 Квітуча',
    healthy:  '✅ Здорова',
    wilting:  '⚠️ В\'яне',
    withered: '💀 Зів\'яла',
  };
  return labels[status] || status;
}

function getContactEmoji(name) {
  const emojis = ['🌸', '🌺', '🌼', '🌷', '🌹', '💐', '🌻', '🌾', '🍀', '🍃', '🪻', '🪷'];
  let hash = 0;
  for (let i = 0; i < name.length; i++) hash = ((hash << 5) - hash + name.charCodeAt(i)) | 0;
  return emojis[Math.abs(hash) % emojis.length];
}

// ═══════════════════════════════════════════════════════════════════════
// Auth
// ═══════════════════════════════════════════════════════════════════════
function showAuth(mode = 'login') {
  const authPage = $('#auth-page');
  const appMain = $('#app-main');
  authPage.classList.remove('hidden');
  appMain.classList.add('hidden');

  const isLogin = mode === 'login';
  $('#auth-title').textContent = isLogin ? 'Ласкаво просимо!' : 'Створіть акаунт';
  $('#auth-subtitle').textContent = isLogin
    ? 'Увійдіть, щоб доглядати свій сад'
    : 'Почніть вирощувати свій сад стосунків';
  $('#auth-submit').textContent = isLogin ? 'Увійти' : 'Зареєструватися';
  $('#auth-switch-link').textContent = isLogin ? 'Зареєструватися' : 'Увійти';
  $('#auth-switch-text').textContent = isLogin ? 'Немає акаунту? ' : 'Є акаунт? ';
  $('#auth-form').dataset.mode = mode;
  $('#auth-error').textContent = '';
  $('#auth-email').value = '';
  $('#auth-password').value = '';
}

async function handleAuth(e) {
  e.preventDefault();
  const mode = $('#auth-form').dataset.mode;
  const email = $('#auth-email').value.trim();
  const password = $('#auth-password').value;

  if (!email || !password) {
    $('#auth-error').textContent = 'Заповніть усі поля';
    return;
  }

  try {
    if (mode === 'register') {
      const data = await api('/register', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });
      state.userId = data.user_id;
      state.email = data.email;
      showToast('Акаунт створено! 🎉');
    } else {
      const data = await api('/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });
      state.userId = data.user_id;
      state.email = data.email;
      showToast('Ласкаво просимо! 🌱');
    }

    localStorage.setItem('garden_user_id', state.userId);
    localStorage.setItem('garden_email', state.email);
    enterApp();
  } catch (err) {
    $('#auth-error').textContent = err.message;
  }
}

function logout() {
  state.userId = null;
  state.email = null;
  localStorage.removeItem('garden_user_id');
  localStorage.removeItem('garden_email');
  showAuth('login');
}

// ═══════════════════════════════════════════════════════════════════════
// Views
// ═══════════════════════════════════════════════════════════════════════
function enterApp() {
  $('#auth-page').classList.add('hidden');
  $('#app-main').classList.remove('hidden');

  // Set avatar
  if (state.email) {
    $('#user-avatar').textContent = state.email[0].toUpperCase();
    $('#user-email').textContent = state.email;
  }

  switchView('garden');
}

function switchView(view) {
  state.currentView = view;

  // Nav active state
  $$('.bottom-nav__item').forEach(el => {
    el.classList.toggle('active', el.dataset.view === view);
  });

  // Hide all views
  $$('.view-section').forEach(el => el.classList.add('hidden'));

  // Show target
  const target = $(`#view-${view}`);
  if (target) {
    target.classList.remove('hidden');
    target.style.animation = 'none';
    target.offsetHeight; // reflow
    target.style.animation = 'fadeInUp var(--dur-slow) var(--ease-smooth)';
  }

  // Load data
  if (view === 'garden') loadGarden();
  else if (view === 'contacts') loadContacts();
  else if (view === 'chat') loadChatContacts();
  else if (view === 'reminders') loadReminders();
}

// ═══════════════════════════════════════════════════════════════════════
// Garden View
// ═══════════════════════════════════════════════════════════════════════
async function loadGarden() {
  const container = $('#garden-grid');
  container.innerHTML = '<div class="loader"><div class="loader__spinner"></div></div>';

  try {
    const [gardenData, contactsData] = await Promise.all([
      api(`/garden/${state.userId}`),
      api(`/contacts/${state.userId}`),
    ]);

    state.garden = gardenData;
    state.contacts = contactsData;

    // Contacts map for frequency info
    const contactMap = {};
    contactsData.forEach(c => { contactMap[c.contact_id] = c; });

    // Stats
    const totalPlants = gardenData.length;
    let thriving = 0, wilting = 0;

    if (totalPlants === 0) {
      container.innerHTML = `
        <div class="empty-state" style="grid-column:1/-1">
          <div class="empty-state__icon">🏡</div>
          <div class="empty-state__title">Ваш сад порожній</div>
          <div class="empty-state__text">Додайте першого контакту, і тут з'явиться його рослина!</div>
          <button class="btn btn--primary" onclick="switchView('contacts')">
            ➕ Додати контакт
          </button>
        </div>`;
      renderStats(0, 0, 0);
      return;
    }

    let html = '';
    gardenData.forEach((plant, idx) => {
      const contact = contactMap[plant.contact_id] || {};
      const freq = contact.reminder_frequency_days || 7;
      const ps = getPlantStatus(plant.growth_level, plant.last_watering, freq);

      if (ps.status === 'thriving' || ps.status === 'healthy') thriving++;
      if (ps.status === 'wilting' || ps.status === 'withered') wilting++;

      html += `
        <div class="plant-card" onclick="openPlantDetail('${plant.contact_id}')"
             style="animation-delay: ${idx * 60}ms; --plant-glow: ${
               ps.status === 'thriving' ? 'hsla(145,60%,40%,0.15)' :
               ps.status === 'wilting' ? 'hsla(38,50%,45%,0.12)' :
               ps.status === 'withered' ? 'hsla(0,50%,40%,0.12)' :
               'hsla(145,40%,35%,0.10)'
             }">
          <div class="plant-card__emoji">${getPlantEmoji(plant.growth_level)}</div>
          <div class="plant-card__name">${plant.contact_name || '?'}</div>
          <div class="plant-card__status">${getStatusLabel(ps.status)}</div>
          <div class="health-bar">
            <div class="health-bar__fill health-bar__fill--${ps.status}"
                 style="width: ${ps.healthPct}%"></div>
          </div>
        </div>`;
    });

    container.innerHTML = html;
    renderStats(totalPlants, thriving, wilting);
  } catch (err) {
    container.innerHTML = `<div class="empty-state" style="grid-column:1/-1">
      <div class="empty-state__icon">😿</div>
      <div class="empty-state__title">Помилка завантаження</div>
      <div class="empty-state__text">${err.message}</div>
    </div>`;
  }
}

function renderStats(total, thriving, wilting) {
  $('#stat-total').textContent = total;
  $('#stat-thriving').textContent = thriving;
  $('#stat-wilting').textContent = wilting;
}

// ═══════════════════════════════════════════════════════════════════════
// Plant Detail Modal
// ═══════════════════════════════════════════════════════════════════════
async function openPlantDetail(contactId) {
  const plant = state.garden.find(p => p.contact_id === contactId);
  const contact = state.contacts.find(c => c.contact_id === contactId);
  if (!plant || !contact) return;

  const ps = getPlantStatus(plant.growth_level, plant.last_watering, contact.reminder_frequency_days);

  const modal = $('#modal-overlay');
  const sheet = $('#modal-sheet');

  // Load interaction history
  let historyHtml = '<div class="loader"><div class="loader__spinner"></div></div>';
  try {
    const interactions = await api(`/interactions/${contactId}`);
    if (interactions.length === 0) {
      historyHtml = '<p class="text-muted text-center mt-md" style="font-size:0.85rem">Ще немає взаємодій</p>';
    } else {
      historyHtml = interactions.slice(0, 10).map(i => `
        <div class="history-item">
          <div class="history-dot"></div>
          <div>
            <div class="history-item__time">${formatDate(i.timestamp)}</div>
            <div class="history-item__text">${i.media_path ? '📷 Надіслано фото' : '💬 Взаємодія'}</div>
          </div>
        </div>`).join('');
    }
  } catch {
    historyHtml = '<p class="text-muted text-center">Не вдалося завантажити</p>';
  }

  sheet.innerHTML = `
    <div class="modal-handle"></div>
    <div style="text-align:center; margin-bottom: var(--space-lg)">
      <div style="font-size: 4rem; margin-bottom: var(--space-sm)">${getPlantEmoji(plant.growth_level)}</div>
      <div class="modal-title" style="margin-bottom:4px">${contact.name}</div>
      <div class="text-muted" style="font-size:0.85rem">${getStatusLabel(ps.status)} · Рівень ${plant.growth_level}/10</div>
    </div>

    <div class="health-bar" style="height:8px; margin-bottom: var(--space-lg)">
      <div class="health-bar__fill health-bar__fill--${ps.status}"
           style="width: ${ps.healthPct}%"></div>
    </div>

    <div class="stats-row">
      <div class="stat-chip">
        <div class="stat-chip__value">${ps.healthPct}%</div>
        <div class="stat-chip__label">Здоров'я</div>
      </div>
      <div class="stat-chip">
        <div class="stat-chip__value">${contact.reminder_frequency_days}д</div>
        <div class="stat-chip__label">Частота</div>
      </div>
      <div class="stat-chip">
        <div class="stat-chip__value">${ps.daysOverdue}</div>
        <div class="stat-chip__label">Прострочено</div>
      </div>
    </div>

    <div style="display:flex; gap:var(--space-sm)">
      <button class="btn btn--primary" style="flex:1" onclick="waterPlant('${contactId}')">
        🌊 Полити рослину
      </button>
      <button class="btn btn--secondary" style="flex:1" onclick="closeModal(); openChat('${contactId}')">
        💬 Написати
      </button>
    </div>

    <div class="section-title" style="font-size:1.1rem; margin-top: var(--space-lg)">
      <span class="emoji">📜</span> Історія взаємодій
    </div>
    ${historyHtml}

    <button class="btn btn--ghost btn--full mt-lg" onclick="closeModal()">Закрити</button>
  `;

  modal.classList.add('show');
}

async function waterPlant(contactId) {
  try {
    const formData = new FormData();
    formData.append('contact_id', contactId);

    const res = await fetch(`${API}/send_media`, { method: 'POST', body: formData });
    const data = await res.json();

    if (!res.ok) throw new Error(data.error);

    showToast(`Рослина підросла! Рівень: ${data.new_growth_level} 🌱`);
    closeModal();
    loadGarden();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function closeModal() {
  $('#modal-overlay').classList.remove('show');
}

// ═══════════════════════════════════════════════════════════════════════
// Contacts View
// ═══════════════════════════════════════════════════════════════════════
async function loadContacts() {
  const container = $('#contacts-list');
  container.innerHTML = '<div class="loader"><div class="loader__spinner"></div></div>';

  try {
    const contacts = await api(`/contacts/${state.userId}`);
    state.contacts = contacts;

    if (contacts.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-state__icon">👤</div>
          <div class="empty-state__title">Немає контактів</div>
          <div class="empty-state__text">Додайте першу людину, з якою хочете підтримувати зв'язок</div>
        </div>`;
      return;
    }

    container.innerHTML = contacts.map(c => `
      <div class="contact-item" id="contact-${c.contact_id}">
        <div class="contact-avatar">${getContactEmoji(c.name)}</div>
        <div class="contact-info" onclick="openPlantDetail('${c.contact_id}')">
          <div class="contact-info__name">${c.name}</div>
          <div class="contact-info__meta">Нагадування: кожні ${c.reminder_frequency_days} дн.</div>
        </div>
        <div class="contact-actions">
          <button class="btn btn--ghost btn--icon" title="Чат"
                  onclick="openChat('${c.contact_id}')">💬</button>
          <button class="btn btn--ghost btn--icon" title="Полити"
                  onclick="waterPlant('${c.contact_id}')">🌊</button>
          <button class="btn btn--ghost btn--icon" title="Видалити"
                  onclick="deleteContact('${c.contact_id}', '${c.name}')">🗑️</button>
        </div>
      </div>
    `).join('');
  } catch (err) {
    container.innerHTML = `<div class="empty-state">
      <div class="empty-state__icon">😿</div>
      <div class="empty-state__text">${err.message}</div>
    </div>`;
  }
}

function showAddContactModal() {
  const modal = $('#modal-overlay');
  const sheet = $('#modal-sheet');

  sheet.innerHTML = `
    <div class="modal-handle"></div>
    <div class="modal-title">➕ Новий контакт</div>

    <form id="add-contact-form" onsubmit="handleAddContact(event)">
      <div class="form-group">
        <label class="form-label" for="contact-name">Ім'я</label>
        <input class="form-input" type="text" id="contact-name"
               placeholder="Мама, Тато, Олена…" required maxlength="100" autocomplete="off">
      </div>

      <div class="form-group">
        <label class="form-label">Частота нагадувань</label>
        <div class="range-group">
          <input type="range" id="contact-freq" min="1" max="30" value="7"
                 oninput="$('#freq-value').textContent = this.value + ' дн.'">
          <span class="range-value" id="freq-value">7 дн.</span>
        </div>
        <div class="form-hint">Як часто нагадувати про зв'язок</div>
      </div>

      <div id="add-contact-error" class="form-error"></div>

      <button type="submit" class="btn btn--primary btn--full mt-md">
        🌱 Додати контакт
      </button>
    </form>

    <button class="btn btn--ghost btn--full mt-md" onclick="closeModal()">Скасувати</button>
  `;

  modal.classList.add('show');
  setTimeout(() => $('#contact-name').focus(), 400);
}

async function handleAddContact(e) {
  e.preventDefault();
  const name = $('#contact-name').value.trim();
  const freq = parseInt($('#contact-freq').value);

  if (!name) {
    $('#add-contact-error').textContent = "Введіть ім'я контакту";
    return;
  }

  try {
    await api('/contacts', {
      method: 'POST',
      body: JSON.stringify({
        user_id: state.userId,
        name,
        reminder_frequency_days: freq,
      }),
    });

    showToast(`${name} додано до вашого саду! 🌱`);
    closeModal();
    loadContacts();
    loadGarden();
  } catch (err) {
    $('#add-contact-error').textContent = err.message;
  }
}

async function deleteContact(contactId, name) {
  if (!confirm(`Видалити контакт "${name}"? Рослина зникне з саду.`)) return;

  try {
    await api(`/contacts/${contactId}`, { method: 'DELETE' });
    showToast(`${name} видалено`);
    loadContacts();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// ═══════════════════════════════════════════════════════════════════════
// Chat View
// ═══════════════════════════════════════════════════════════════════════
async function loadChatContacts() {
  const container = $('#chat-contacts-list');
  container.innerHTML = '<div class="loader"><div class="loader__spinner"></div></div>';

  try {
    const contacts = await api(`/contacts/${state.userId}`);
    state.contacts = contacts;

    if (contacts.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-state__icon">💬</div>
          <div class="empty-state__title">Немає контактів</div>
          <div class="empty-state__text">Спочатку додайте контакти на вкладці "Контакти"</div>
          <button class="btn btn--primary" onclick="switchView('contacts')">
            👥 Перейти до контактів
          </button>
        </div>`;
      return;
    }

    container.innerHTML = contacts.map(c => `
      <div class="contact-item" onclick="openChat('${c.contact_id}')">
        <div class="contact-avatar">${getContactEmoji(c.name)}</div>
        <div class="contact-info">
          <div class="contact-info__name">${c.name}</div>
          <div class="contact-info__meta">Натисніть, щоб відкрити чат</div>
        </div>
        <span style="font-size:1.2rem; opacity:0.5">›</span>
      </div>
    `).join('');
  } catch (err) {
    container.innerHTML = `<div class="empty-state">
      <div class="empty-state__icon">😿</div>
      <div class="empty-state__text">${err.message}</div>
    </div>`;
  }
}

async function openChat(contactId) {
  const contact = state.contacts.find(c => c.contact_id === contactId);
  if (!contact) {
    // Reload contacts first
    const contacts = await api(`/contacts/${state.userId}`);
    state.contacts = contacts;
  }
  const c = state.contacts.find(c => c.contact_id === contactId);
  if (!c) return;

  state.activeChatContact = c;

  // Switch to chat view and replace content with chat UI
  $$('.bottom-nav__item').forEach(el => {
    el.classList.toggle('active', el.dataset.view === 'chat');
  });
  $$('.view-section').forEach(el => el.classList.add('hidden'));
  const chatView = $('#view-chat');
  chatView.classList.remove('hidden');

  chatView.innerHTML = `
    <div class="chat-container">
      <div class="chat-header">
        <button class="chat-header__back" onclick="switchView('chat')" title="Назад">⬅</button>
        <div class="contact-avatar" style="width:36px;height:36px;font-size:1.1rem">${getContactEmoji(c.name)}</div>
        <div>
          <div class="chat-header__name">${c.name}</div>
          <div class="chat-header__status">Garden Chat</div>
        </div>
      </div>
      <div class="chat-messages" id="chat-messages">
        <div class="loader"><div class="loader__spinner"></div></div>
      </div>
      <div class="chat-input-bar">
        <input type="text" id="chat-input" placeholder="Введіть повідомлення…"
               autocomplete="off" onkeydown="if(event.key==='Enter')sendChatMessage()">
        <button class="chat-send-btn" onclick="sendChatMessage()" title="Надіслати">➤</button>
      </div>
    </div>
  `;

  await loadMessages(contactId);
  setTimeout(() => $('#chat-input').focus(), 200);
}

async function loadMessages(contactId) {
  const container = $('#chat-messages');
  try {
    const messages = await api(`/messages/${contactId}`);

    if (messages.length === 0) {
      container.innerHTML = `
        <div class="empty-state" style="flex:1; justify-content:center">
          <div class="empty-state__icon" style="font-size:2.5rem">💬</div>
          <div class="empty-state__title" style="font-size:1rem">Почніть розмову</div>
          <div class="empty-state__text" style="font-size:0.82rem">Напишіть перше повідомлення!</div>
        </div>`;
      return;
    }

    container.innerHTML = messages.map(m => `
      <div class="chat-bubble chat-bubble--${m.sender === 'user' ? 'user' : 'contact'}">
        ${escapeHtml(m.content)}
        <span class="chat-bubble__time">${formatTime(m.timestamp)}</span>
      </div>
    `).join('');

    // Scroll to bottom
    container.scrollTop = container.scrollHeight;
  } catch (err) {
    container.innerHTML = `<p class="text-muted text-center">Помилка: ${err.message}</p>`;
  }
}

async function sendChatMessage() {
  const input = $('#chat-input');
  const content = input.value.trim();
  if (!content || !state.activeChatContact) return;

  const contactId = state.activeChatContact.contact_id;
  input.value = '';

  try {
    // Send user message
    await api('/messages', {
      method: 'POST',
      body: JSON.stringify({ contact_id: contactId, content, sender: 'user' }),
    });

    // Simulate a simple auto-reply from the contact (for demo purposes)
    const autoReplies = [
      `Дякую! 💚`,
      `Як справи? 😊`,
      `Дуже рада тебе чути!`,
      `Скучила! Давай зустрінемось 🌸`,
      `Супер! Передаю привіт! 👋`,
      `Люблю тебе! ❤️`,
      `Обіймаю! 🤗`,
      `Ой, як гарно! 🌻`,
    ];
    const reply = autoReplies[Math.floor(Math.random() * autoReplies.length)];

    // Small delay before auto-reply
    setTimeout(async () => {
      await api('/messages', {
        method: 'POST',
        body: JSON.stringify({ contact_id: contactId, content: reply, sender: 'contact' }),
      });
      await loadMessages(contactId);
    }, 800);

    await loadMessages(contactId);
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// ═══════════════════════════════════════════════════════════════════════
// Reminders View
// ═══════════════════════════════════════════════════════════════════════
async function loadReminders() {
  const container = $('#reminders-list');
  container.innerHTML = '<div class="loader"><div class="loader__spinner"></div></div>';

  try {
    const data = await api(`/check_reminders/${state.userId}`, { method: 'POST' });
    state.reminders = data.reminders_sent || [];

    if (state.reminders.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-state__icon">🎉</div>
          <div class="empty-state__title">Все добре!</div>
          <div class="empty-state__text">Немає прострочених нагадувань. Ви чудово підтримуєте зв'язок!</div>
        </div>`;
      return;
    }

    container.innerHTML = state.reminders.map(r => `
      <div class="reminder-item">
        <div class="reminder-item__icon">🌱</div>
        <div style="flex:1">
          <div class="reminder-item__text">${r.message}</div>
          <div class="reminder-item__days">Контакт: ${r.contact}</div>
        </div>
        <button class="btn btn--primary btn--sm" onclick="openChat('${r.contact_id || ''}')">
          💬
        </button>
      </div>
    `).join('');
  } catch (err) {
    container.innerHTML = `<div class="empty-state">
      <div class="empty-state__icon">😿</div>
      <div class="empty-state__text">${err.message}</div>
    </div>`;
  }
}

// ═══════════════════════════════════════════════════════════════════════
// Particles (decorative)
// ═══════════════════════════════════════════════════════════════════════
function initParticles() {
  const container = $('#garden-particles');
  if (!container) return;
  const leaves = ['🍃', '🌿', '🍀', '🌸', '✨', '🌼'];
  for (let i = 0; i < 12; i++) {
    const span = document.createElement('span');
    span.textContent = leaves[i % leaves.length];
    span.style.left = `${Math.random() * 100}%`;
    span.style.animationDuration = `${15 + Math.random() * 20}s`;
    span.style.animationDelay = `${Math.random() * 15}s`;
    span.style.fontSize = `${0.8 + Math.random() * 0.8}rem`;
    container.appendChild(span);
  }
}

// ═══════════════════════════════════════════════════════════════════════
// Init
// ═══════════════════════════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
  // Particles
  initParticles();

  // Auth form
  $('#auth-form').addEventListener('submit', handleAuth);
  $('#auth-switch-link').addEventListener('click', (e) => {
    e.preventDefault();
    const current = $('#auth-form').dataset.mode;
    showAuth(current === 'login' ? 'register' : 'login');
  });

  // Bottom nav
  $$('.bottom-nav__item').forEach(el => {
    el.addEventListener('click', () => switchView(el.dataset.view));
  });

  // Modal overlay close
  $('#modal-overlay').addEventListener('click', (e) => {
    if (e.target === e.currentTarget) closeModal();
  });

  // Logout
  $('#btn-logout').addEventListener('click', logout);

  // Check session
  if (state.userId) {
    enterApp();
  } else {
    showAuth('login');
  }
});
