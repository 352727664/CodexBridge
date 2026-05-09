const BASE = '';

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  // Providers
  listProviders: () => request('/api/providers'),
  createProvider: (data) => request('/api/providers', { method: 'POST', body: JSON.stringify(data) }),
  updateProvider: (id, data) => request(`/api/providers/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteProvider: (id) => request(`/api/providers/${id}`, { method: 'DELETE' }),
  enableProvider: (id) => request(`/api/providers/${id}/enable`, { method: 'POST' }),
  duplicateProvider: (id) => request(`/api/providers/${id}/duplicate`, { method: 'POST' }),

  // Testing
  testConnection: (data) => request('/api/test', { method: 'POST', body: JSON.stringify(data) }),
  fetchModels: (data) => request('/api/fetch-models', { method: 'POST', body: JSON.stringify(data) }),

  // Settings
  getSettings: () => request('/api/settings'),
  updateSettings: (data) => request('/api/settings', { method: 'PUT', body: JSON.stringify(data) }),

  // Health
  health: () => request('/health'),

  // Raw config
  getRawConfig: () => request('/api/config/raw'),
};
