const BASE_URL = window.location.origin;

const API = {
  async fetchJSON(path, options = {}) {
    const res = await fetch(`${BASE_URL}${path}`, {
      headers: { 'Content-Type': 'application/json', ...options.headers },
      ...options,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Request failed');
    }
    return res.json();
  },

  listSessions() {
    return this.fetchJSON('/api/sessions');
  },

  createSession(name, mode) {
    return this.fetchJSON('/api/sessions', {
      method: 'POST',
      body: JSON.stringify({ name, mode }),
    });
  },

  getSession(id) {
    return this.fetchJSON(`/api/sessions/${id}`);
  },

  updateSession(id, payload) {
    return this.fetchJSON(`/api/sessions/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  },

  deleteSession(id) {
    return fetch(`${BASE_URL}/api/sessions/${id}`, { method: 'DELETE' });
  },

  getMessages(sessionId) {
    return this.fetchJSON(`/api/sessions/${sessionId}/messages`);
  },

  exportSession(sessionId) {
    return this.fetchJSON(`/api/sessions/${sessionId}/export`);
  },

  getModes() {
    return this.fetchJSON('/api/config/modes');
  },

  getLLMConfig() {
    return this.fetchJSON('/api/config/llm');
  },

  checkHealth() {
    return this.fetchJSON('/api/config/health');
  },
};

class WebSocketClient {
  constructor(sessionId, onMessage, onClose) {
    this.sessionId = sessionId;
    this.onMessage = onMessage;
    this.onClose = onClose;
    this.ws = null;
    this.pingInterval = null;
  }

  connect() {
    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    const url = `${proto}://${location.host}/ws/${this.sessionId}`;
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      this.pingInterval = setInterval(() => {
        if (this.ws.readyState === WebSocket.OPEN) {
          this.ws.send(JSON.stringify({ type: 'ping' }));
        }
      }, 25000);
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.onMessage(data);
      } catch {}
    };

    this.ws.onclose = () => {
      clearInterval(this.pingInterval);
      this.onClose && this.onClose();
    };

    this.ws.onerror = () => {
      this.ws.close();
    };
  }

  send(payload) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(payload));
      return true;
    }
    return false;
  }

  disconnect() {
    clearInterval(this.pingInterval);
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  isConnected() {
    return this.ws && this.ws.readyState === WebSocket.OPEN;
  }
}
