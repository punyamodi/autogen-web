const Settings = {
  current: {
    base_url: 'http://localhost:1234/v1',
    api_key: 'NULL',
    model: 'local-model',
    temperature: 0.1,
    timeout: 600,
  },

  init() {
    const stored = localStorage.getItem('agentforge_settings');
    if (stored) {
      try {
        Object.assign(this.current, JSON.parse(stored));
      } catch {}
    }

    document.getElementById('btn-settings').addEventListener('click', () => this.open());
    document.getElementById('btn-close-settings').addEventListener('click', () => this.close());
    document.getElementById('btn-cancel-settings').addEventListener('click', () => this.close());
    document.getElementById('btn-save-settings').addEventListener('click', () => this.save());
    document.getElementById('btn-test-llm').addEventListener('click', () => this.testConnection());

    const tempInput = document.getElementById('s-temperature');
    const tempValue = document.getElementById('s-temp-value');
    tempInput.addEventListener('input', () => {
      tempValue.textContent = parseFloat(tempInput.value).toFixed(2);
    });

    document.querySelectorAll('input[name="theme"]').forEach((radio) => {
      radio.addEventListener('change', (e) => {
        App.setTheme(e.target.value);
      });
    });
  },

  open() {
    document.getElementById('s-base-url').value = this.current.base_url;
    document.getElementById('s-api-key').value = this.current.api_key;
    document.getElementById('s-model').value = this.current.model;
    document.getElementById('s-temperature').value = this.current.temperature;
    document.getElementById('s-temp-value').textContent = parseFloat(this.current.temperature).toFixed(2);
    document.getElementById('s-timeout').value = this.current.timeout;

    const theme = document.documentElement.getAttribute('data-theme') || 'dark';
    document.querySelector(`input[name="theme"][value="${theme}"]`).checked = true;

    document.getElementById('settings-modal').style.display = 'flex';
  },

  close() {
    document.getElementById('settings-modal').style.display = 'none';
    document.getElementById('llm-test-result').textContent = '';
  },

  save() {
    this.current.base_url = document.getElementById('s-base-url').value.trim() || 'http://localhost:1234/v1';
    this.current.api_key = document.getElementById('s-api-key').value.trim() || 'NULL';
    this.current.model = document.getElementById('s-model').value.trim() || 'local-model';
    this.current.temperature = parseFloat(document.getElementById('s-temperature').value);
    this.current.timeout = parseInt(document.getElementById('s-timeout').value, 10);

    localStorage.setItem('agentforge_settings', JSON.stringify(this.current));
    this.close();
    App.showToast('Settings saved', 'success');
    App.checkLLMStatus();
  },

  async testConnection() {
    const resultEl = document.getElementById('llm-test-result');
    resultEl.textContent = 'Testing...';
    resultEl.className = 'test-result';

    try {
      const res = await fetch(`${document.getElementById('s-base-url').value.trim()}/models`, {
        signal: AbortSignal.timeout(6000),
      });
      if (res.ok) {
        resultEl.textContent = 'Connected successfully';
        resultEl.className = 'test-result success';
      } else {
        resultEl.textContent = `HTTP ${res.status}`;
        resultEl.className = 'test-result error';
      }
    } catch (e) {
      resultEl.textContent = 'Connection failed';
      resultEl.className = 'test-result error';
    }
  },

  getConfig() {
    return { ...this.current };
  },
};
