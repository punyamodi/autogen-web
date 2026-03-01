const App = {
  sessions: [],
  currentSessionId: null,
  activeMode: 'pair_coder',
  modes: [],
  wsClient: null,
  isAgentRunning: false,

  async init() {
    Chat.init();
    Settings.init();

    this.bindEvents();
    this.applyStoredTheme();

    await this.loadModes();
    await this.loadSessions();
    this.checkLLMStatus();

    setInterval(() => this.checkLLMStatus(), 60000);

    this.restoreLastSession();
  },

  bindEvents() {
    document.getElementById('btn-new-chat').addEventListener('click', () => this.newChat());
    document.getElementById('btn-sidebar-toggle').addEventListener('click', () => this.toggleSidebar());
    document.getElementById('btn-close-panel').addEventListener('click', () => this.toggleAgentPanel());
    document.getElementById('btn-theme').addEventListener('click', () => this.cycleTheme());
    document.getElementById('btn-rename').addEventListener('click', () => this.openRename());
    document.getElementById('btn-close-rename').addEventListener('click', () => this.closeRename());
    document.getElementById('btn-cancel-rename').addEventListener('click', () => this.closeRename());
    document.getElementById('btn-confirm-rename').addEventListener('click', () => this.confirmRename());
    document.getElementById('btn-export').addEventListener('click', () => this.exportConversation());
    document.getElementById('btn-clear').addEventListener('click', () => this.clearCurrentChat());
    document.getElementById('btn-send').addEventListener('click', () => this.sendMessage());

    const input = document.getElementById('user-input');
    input.addEventListener('input', () => this.onInputChange());
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && e.ctrlKey) {
        e.preventDefault();
        this.sendMessage();
      }
    });
  },

  onInputChange() {
    const input = document.getElementById('user-input');
    const val = input.value;
    document.getElementById('char-count').textContent = `${val.length} / 8000`;
    document.getElementById('btn-send').disabled = val.trim().length === 0 || this.isAgentRunning;

    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 200) + 'px';
  },

  async loadModes() {
    try {
      this.modes = await API.getModes();
    } catch {
      this.modes = [
        { id: 'pair_coder', name: 'Pair Coder', description: 'CTO + Executor coding pair', agents: ['CTO', 'Executor'], icon: 'code' },
        { id: 'coding_team', name: 'Coding Team', description: '6-agent research and coding team', agents: ['Admin', 'Planner', 'Engineer', 'Scientist', 'Executor', 'Critic'], icon: 'users' },
        { id: 'jarvis', name: 'Jarvis', description: 'Comprehensive multi-agent assistant', agents: ['Jarvis', 'PythonCoder', 'CppCoder', 'Coder', 'Critic', 'CTO', 'Advisor', 'Friend', 'Aggregator'], icon: 'cpu' },
        { id: 'research', name: 'Research Team', description: 'Research, analysis, and writing team', agents: ['Admin', 'Researcher', 'Analyst', 'Writer', 'Executor', 'FactChecker'], icon: 'search' },
      ];
    }

    this.renderModeList();
    this.renderWelcomeModes();
  },

  renderModeList() {
    const list = document.getElementById('mode-list');
    list.innerHTML = '';
    this.modes.forEach((mode) => {
      const btn = document.createElement('button');
      btn.className = `mode-item ${mode.id === this.activeMode ? 'active' : ''}`;
      btn.dataset.mode = mode.id;
      btn.innerHTML = `${this.getModeIcon(mode.icon)}<span>${mode.name}</span>`;
      btn.addEventListener('click', () => this.selectMode(mode.id));
      list.appendChild(btn);
    });
  },

  renderWelcomeModes() {
    const container = document.getElementById('welcome-modes');
    container.innerHTML = '';
    this.modes.forEach((mode) => {
      const card = document.createElement('button');
      card.className = 'welcome-mode-card';
      card.innerHTML = `<div class="wmc-title">${mode.name}</div><div class="wmc-desc">${mode.description}</div>`;
      card.addEventListener('click', () => {
        this.selectMode(mode.id);
        this.newChat();
      });
      container.appendChild(card);
    });
  },

  getModeIcon(icon) {
    const icons = {
      code: '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline></svg>',
      users: '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>',
      cpu: '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="4" width="16" height="16" rx="2"></rect><rect x="9" y="9" width="6" height="6"></rect><line x1="9" y1="1" x2="9" y2="4"></line><line x1="15" y1="1" x2="15" y2="4"></line><line x1="9" y1="20" x2="9" y2="23"></line><line x1="15" y1="20" x2="15" y2="23"></line><line x1="20" y1="9" x2="23" y2="9"></line><line x1="20" y1="14" x2="23" y2="14"></line><line x1="1" y1="9" x2="4" y2="9"></line><line x1="1" y1="14" x2="4" y2="14"></line></svg>',
      search: '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>',
    };
    return icons[icon] || icons.code;
  },

  selectMode(modeId) {
    this.activeMode = modeId;
    localStorage.setItem('agentforge_mode', modeId);

    document.querySelectorAll('.mode-item').forEach((btn) => {
      btn.classList.toggle('active', btn.dataset.mode === modeId);
    });

    const modeInfo = this.modes.find((m) => m.id === modeId);
    const label = modeInfo ? modeInfo.name : modeId;
    document.getElementById('active-mode-label').textContent = `Mode: ${label}`;

    if (modeInfo) {
      this.renderAgentPanel(modeInfo.agents);
    }

    if (this.currentSessionId) {
      API.updateSession(this.currentSessionId, { mode: modeId }).catch(() => {});
    }
  },

  renderAgentPanel(agents) {
    const list = document.getElementById('agent-list');
    list.innerHTML = '';
    agents.forEach((name) => {
      const col = typeof getAgentColor !== 'undefined' ? getAgentColor(name) : { bg: 'var(--bg-hover)', color: 'var(--text-secondary)' };
      const card = document.createElement('div');
      card.className = 'agent-card';
      card.id = `agent-card-${name}`;
      card.innerHTML = `
        <div class="agent-card-name" style="color:${col.color}">${name}</div>
        <div class="agent-card-role">Ready</div>
      `;
      list.appendChild(card);
    });
  },

  highlightAgent(name) {
    document.querySelectorAll('.agent-card').forEach((c) => c.classList.remove('active'));
    const card = document.getElementById(`agent-card-${name}`);
    if (card) {
      card.classList.add('active');
      card.querySelector('.agent-card-role').textContent = 'Speaking';
    }
  },

  resetAgentHighlights() {
    document.querySelectorAll('.agent-card').forEach((c) => {
      c.classList.remove('active');
      const roleEl = c.querySelector('.agent-card-role');
      if (roleEl) roleEl.textContent = 'Ready';
    });
  },

  async loadSessions() {
    try {
      this.sessions = await API.listSessions();
    } catch {
      this.sessions = [];
    }
    this.renderSessionList();
  },

  renderSessionList() {
    const list = document.getElementById('session-list');
    list.innerHTML = '';
    if (this.sessions.length === 0) {
      list.innerHTML = '<div style="padding:8px 10px;font-size:0.78rem;color:var(--text-muted)">No sessions yet</div>';
      return;
    }
    this.sessions.forEach((s) => {
      const item = document.createElement('div');
      item.className = `session-item ${s.id === this.currentSessionId ? 'active' : ''}`;
      item.dataset.id = s.id;
      item.innerHTML = `
        <span class="session-item-name">${s.name}</span>
        <button class="session-item-del" title="Delete session" data-id="${s.id}">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"></path></svg>
        </button>
      `;
      item.addEventListener('click', (e) => {
        if (e.target.closest('.session-item-del')) {
          this.deleteSession(s.id);
        } else {
          this.loadSession(s.id);
        }
      });
      list.appendChild(item);
    });
  },

  async newChat() {
    if (this.wsClient) {
      this.wsClient.disconnect();
      this.wsClient = null;
    }

    try {
      const modeInfo = this.modes.find((m) => m.id === this.activeMode);
      const name = modeInfo ? `${modeInfo.name} Chat` : 'New Chat';
      const session = await API.createSession(name, this.activeMode);
      this.sessions.unshift(session);
      this.renderSessionList();
      this.activateSession(session);
    } catch (e) {
      this.showToast('Failed to create session', 'error');
    }
  },

  async loadSession(sessionId) {
    if (this.wsClient) {
      this.wsClient.disconnect();
      this.wsClient = null;
    }
    try {
      const session = await API.getSession(sessionId);
      const messages = await API.getMessages(sessionId);
      this.activateSession(session);
      Chat.loadMessages(messages);
    } catch {
      this.showToast('Failed to load session', 'error');
    }
  },

  activateSession(session) {
    this.currentSessionId = session.id;
    localStorage.setItem('agentforge_last_session', session.id);
    document.getElementById('session-title').textContent = session.name;
    this.selectMode(session.mode);

    document.querySelectorAll('.session-item').forEach((el) => {
      el.classList.toggle('active', el.dataset.id === session.id);
    });

    this.connectWebSocket(session.id);
  },

  connectWebSocket(sessionId) {
    if (this.wsClient) {
      this.wsClient.disconnect();
    }

    this.wsClient = new WebSocketClient(
      sessionId,
      (msg) => this.handleWsMessage(msg),
      () => {
        this.isAgentRunning = false;
        this.setInputEnabled(true);
      }
    );
    this.wsClient.connect();
  },

  handleWsMessage(msg) {
    if (msg.type === 'connected') return;
    if (msg.type === 'pong') return;

    if (msg.type === 'thinking') {
      Chat.showTyping(msg.content || 'Agents are working...');
      return;
    }

    if (msg.type === 'agent_message') {
      this.highlightAgent(msg.sender);
      Chat.appendAgentMessage(msg.sender, msg.content);
      return;
    }

    if (msg.type === 'done') {
      Chat.removeTyping();
      this.resetAgentHighlights();
      this.isAgentRunning = false;
      this.setInputEnabled(true);
      this.loadSessions();
      return;
    }

    if (msg.type === 'error') {
      Chat.appendError(msg.content || 'An error occurred.');
      this.isAgentRunning = false;
      this.setInputEnabled(true);
      return;
    }
  },

  async sendMessage() {
    const input = document.getElementById('user-input');
    const content = input.value.trim();
    if (!content || this.isAgentRunning) return;

    if (!this.currentSessionId) {
      await this.newChat();
    }

    if (!this.wsClient || !this.wsClient.isConnected()) {
      this.connectWebSocket(this.currentSessionId);
      await new Promise((r) => setTimeout(r, 600));
    }

    Chat.appendUserMessage(content);
    input.value = '';
    input.style.height = 'auto';
    this.onInputChange();

    this.isAgentRunning = true;
    this.setInputEnabled(false);

    const config = Settings.getConfig();
    const sent = this.wsClient.send({
      type: 'message',
      content,
      mode: this.activeMode,
      config,
    });

    if (!sent) {
      Chat.appendError('Could not send message. Check your connection.');
      this.isAgentRunning = false;
      this.setInputEnabled(true);
    }
  },

  setInputEnabled(enabled) {
    const input = document.getElementById('user-input');
    const btn = document.getElementById('btn-send');
    input.disabled = !enabled;
    if (!enabled) {
      btn.disabled = true;
    } else {
      btn.disabled = input.value.trim().length === 0;
    }
  },

  async deleteSession(sessionId) {
    try {
      await API.deleteSession(sessionId);
      this.sessions = this.sessions.filter((s) => s.id !== sessionId);
      this.renderSessionList();

      if (this.currentSessionId === sessionId) {
        this.currentSessionId = null;
        if (this.wsClient) {
          this.wsClient.disconnect();
          this.wsClient = null;
        }
        document.getElementById('session-title').textContent = 'New Chat';
        Chat.showWelcome();
      }

      this.showToast('Session deleted', 'info');
    } catch {
      this.showToast('Failed to delete session', 'error');
    }
  },

  clearCurrentChat() {
    Chat.clear();
    Chat.showWelcome();
  },

  openRename() {
    if (!this.currentSessionId) return;
    const title = document.getElementById('session-title').textContent;
    document.getElementById('rename-input').value = title;
    document.getElementById('rename-modal').style.display = 'flex';
    document.getElementById('rename-input').select();
  },

  closeRename() {
    document.getElementById('rename-modal').style.display = 'none';
  },

  async confirmRename() {
    const name = document.getElementById('rename-input').value.trim();
    if (!name || !this.currentSessionId) return;

    try {
      const updated = await API.updateSession(this.currentSessionId, { name });
      document.getElementById('session-title').textContent = updated.name;
      const idx = this.sessions.findIndex((s) => s.id === this.currentSessionId);
      if (idx !== -1) this.sessions[idx].name = updated.name;
      this.renderSessionList();
      this.closeRename();
      this.showToast('Renamed successfully', 'success');
    } catch {
      this.showToast('Rename failed', 'error');
    }
  },

  async exportConversation() {
    if (!this.currentSessionId) {
      this.showToast('No active session', 'error');
      return;
    }

    try {
      const data = await API.exportSession(this.currentSessionId);
      const lines = [
        `# ${data.session_name}`,
        `Mode: ${data.mode}`,
        `Exported: ${new Date(data.exported_at).toLocaleString()}`,
        '',
        '---',
        '',
      ];
      data.messages.forEach((m) => {
        lines.push(`**${m.sender}**: ${m.content}`);
        lines.push('');
      });

      const blob = new Blob([lines.join('\n')], { type: 'text/markdown' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${data.session_name.replace(/\s+/g, '_')}.md`;
      a.click();
      URL.revokeObjectURL(url);
      this.showToast('Exported', 'success');
    } catch {
      this.showToast('Export failed', 'error');
    }
  },

  async checkLLMStatus() {
    const dot = document.querySelector('.status-dot');
    const text = document.getElementById('llm-status-text');
    try {
      const health = await API.checkHealth();
      if (health.llm_reachable) {
        dot.className = 'status-dot online';
        text.textContent = 'LLM Online';
      } else {
        dot.className = 'status-dot offline';
        text.textContent = 'LLM Offline';
      }
    } catch {
      dot.className = 'status-dot offline';
      text.textContent = 'LLM Offline';
    }
  },

  toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('collapsed');
  },

  toggleAgentPanel() {
    document.getElementById('agent-panel').classList.toggle('hidden');
  },

  setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('agentforge_theme', theme);
    const sun = document.getElementById('icon-sun');
    const moon = document.getElementById('icon-moon');
    if (theme === 'dark') {
      sun.style.display = '';
      moon.style.display = 'none';
    } else {
      sun.style.display = 'none';
      moon.style.display = '';
    }
  },

  cycleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || 'dark';
    this.setTheme(current === 'dark' ? 'light' : 'dark');
  },

  applyStoredTheme() {
    const theme = localStorage.getItem('agentforge_theme') || 'dark';
    this.setTheme(theme);
    const stored = localStorage.getItem('agentforge_mode');
    if (stored) this.activeMode = stored;
  },

  async restoreLastSession() {
    const lastId = localStorage.getItem('agentforge_last_session');
    if (lastId && this.sessions.find((s) => s.id === lastId)) {
      await this.loadSession(lastId);
    } else if (this.sessions.length === 0) {
      Chat.showWelcome();
    } else {
      Chat.showWelcome();
    }
  },

  showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3500);
  },
};

document.addEventListener('DOMContentLoaded', () => App.init());
