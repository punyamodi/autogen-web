const AGENT_COLORS = {
  CTO: { bg: 'var(--purple-dim)', color: 'var(--purple)' },
  Engineer: { bg: 'var(--accent-dim)', color: 'var(--accent)' },
  Planner: { bg: 'var(--warning-dim)', color: 'var(--warning)' },
  Critic: { bg: 'var(--error-dim)', color: 'var(--error)' },
  Scientist: { bg: 'var(--success-dim)', color: 'var(--success)' },
  Executor: { bg: 'var(--orange-dim)', color: 'var(--orange)' },
  Admin: { bg: 'var(--bg-hover)', color: 'var(--text-secondary)' },
  Jarvis: { bg: 'var(--accent-dim)', color: 'var(--accent)' },
  PythonCoder: { bg: 'var(--purple-dim)', color: 'var(--purple)' },
  CppCoder: { bg: 'var(--warning-dim)', color: 'var(--warning)' },
  Coder: { bg: 'var(--success-dim)', color: 'var(--success)' },
  Advisor: { bg: 'var(--orange-dim)', color: 'var(--orange)' },
  Friend: { bg: 'var(--success-dim)', color: 'var(--success)' },
  Aggregator: { bg: 'var(--cyan-dim)', color: '#39d353' },
  Researcher: { bg: 'var(--accent-dim)', color: 'var(--accent)' },
  Analyst: { bg: 'var(--purple-dim)', color: 'var(--purple)' },
  Writer: { bg: 'var(--warning-dim)', color: 'var(--warning)' },
  FactChecker: { bg: 'var(--error-dim)', color: 'var(--error)' },
};

const DEFAULT_COLOR = { bg: 'var(--bg-hover)', color: 'var(--text-secondary)' };

function getAgentColor(name) {
  return AGENT_COLORS[name] || DEFAULT_COLOR;
}

function renderMarkdown(text) {
  try {
    return marked.parse(text, { breaks: true, gfm: true });
  } catch {
    return text.replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
}

function highlightCodeBlocks(el) {
  el.querySelectorAll('pre code').forEach((block) => {
    hljs.highlightElement(block);
  });
}

function addCopyButtons(el) {
  el.querySelectorAll('pre').forEach((pre) => {
    const code = pre.querySelector('code');
    if (!code) return;
    const btn = document.createElement('button');
    btn.className = 'copy-btn';
    btn.textContent = 'Copy';
    btn.onclick = () => {
      navigator.clipboard.writeText(code.textContent).then(() => {
        btn.textContent = 'Copied!';
        setTimeout(() => (btn.textContent = 'Copy'), 2000);
      });
    };
    pre.style.position = 'relative';
    btn.style.position = 'absolute';
    btn.style.top = '6px';
    btn.style.right = '6px';
    btn.style.opacity = '1';
    pre.appendChild(btn);
  });
}

const Chat = {
  messagesEl: null,
  welcomeEl: null,
  typingEl: null,

  init() {
    this.messagesEl = document.getElementById('messages');
    this.welcomeEl = document.getElementById('welcome-screen');
  },

  showWelcome() {
    this.welcomeEl.style.display = 'flex';
    this.welcomeEl.style.flexDirection = 'column';
    this.messagesEl.style.display = 'none';
    this.messagesEl.innerHTML = '';
  },

  showMessages() {
    this.welcomeEl.style.display = 'none';
    this.messagesEl.style.display = 'flex';
  },

  clear() {
    this.messagesEl.innerHTML = '';
    this.removeTyping();
  },

  appendUserMessage(content) {
    this.showMessages();
    const div = document.createElement('div');
    div.className = 'message user-message';
    div.innerHTML = `
      <div class="message-meta" style="justify-content: flex-end;">
        <span class="agent-badge" style="background:var(--accent-dim);color:var(--accent);">You</span>
        <button class="copy-btn" onclick="navigator.clipboard.writeText(${JSON.stringify(content)})">Copy</button>
      </div>
      <div class="message-bubble">${content.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</div>
    `;
    this.messagesEl.appendChild(div);
    this.scrollToBottom();
  },

  appendAgentMessage(sender, content) {
    this.showMessages();
    this.removeTyping();

    const col = getAgentColor(sender);
    const div = document.createElement('div');
    div.className = 'message agent-message';

    const rendered = renderMarkdown(content);

    div.innerHTML = `
      <div class="message-meta">
        <span class="agent-badge" style="background:${col.bg};color:${col.color};">${sender}</span>
        <button class="copy-btn" onclick="navigator.clipboard.writeText(${JSON.stringify(content)})">Copy</button>
      </div>
      <div class="message-bubble">${rendered}</div>
    `;

    const bubble = div.querySelector('.message-bubble');
    highlightCodeBlocks(bubble);
    addCopyButtons(bubble);

    this.messagesEl.appendChild(div);
    this.scrollToBottom();
  },

  showTyping(label = 'Agents are working...') {
    this.removeTyping();
    this.showMessages();
    const div = document.createElement('div');
    div.id = 'typing-indicator';
    div.className = 'message agent-message';
    div.innerHTML = `
      <div class="message-meta">
        <span class="agent-badge" style="background:var(--bg-hover);color:var(--text-muted);">System</span>
      </div>
      <div class="typing-indicator">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <span style="margin-left:6px;font-size:0.78rem;color:var(--text-muted)">${label}</span>
      </div>
    `;
    this.messagesEl.appendChild(div);
    this.scrollToBottom();
  },

  removeTyping() {
    const el = document.getElementById('typing-indicator');
    if (el) el.remove();
  },

  appendError(msg) {
    this.removeTyping();
    const div = document.createElement('div');
    div.className = 'message agent-message';
    div.innerHTML = `
      <div class="message-meta">
        <span class="agent-badge" style="background:var(--error-dim);color:var(--error);">Error</span>
      </div>
      <div class="message-bubble" style="border-color:var(--error);color:var(--error);">${msg}</div>
    `;
    this.messagesEl.appendChild(div);
    this.scrollToBottom();
  },

  loadMessages(messages) {
    this.clear();
    if (!messages || messages.length === 0) {
      this.showWelcome();
      return;
    }
    this.showMessages();
    messages.forEach((m) => {
      if (m.msg_type === 'user_message') {
        this.appendUserMessage(m.content);
      } else {
        this.appendAgentMessage(m.sender, m.content);
      }
    });
  },

  scrollToBottom() {
    const container = document.getElementById('chat-container');
    container.scrollTop = container.scrollHeight;
  },
};
