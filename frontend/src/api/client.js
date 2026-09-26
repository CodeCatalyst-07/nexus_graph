const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '') + '/api';

export async function sendChatMessage(email, message, sessionId = 'session-1') {
  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, message, session_id: sessionId })
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: 'Network error' }));
    throw new Error(err.detail || 'Failed to send message');
  }
  return response.json();
}

export async function fetchCustomerGraph(email) {
  const response = await fetch(`${API_BASE}/graph/${encodeURIComponent(email)}`);
  if (!response.ok) {
    throw new Error('Failed to fetch graph subgraph');
  }
  return response.json();
}

export async function seedDemoCustomer(email = 'alice@techcorp.io') {
  const response = await fetch(`${API_BASE}/demo/seed`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email })
  });
  if (!response.ok) {
    throw new Error('Failed to seed demo customer');
  }
  return response.json();
}

export async function resetDemoState(email = 'alice@techcorp.io') {
  const response = await fetch(`${API_BASE}/demo/reset`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email })
  });
  if (!response.ok) {
    throw new Error('Failed to reset demo state');
  }
  return response.json();
}
