const BASE_URL = 'http://localhost:8080'

async function fetchJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`)
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

export const api = {
  getStatus: () => fetchJSON('/api/status'),
  getCurrentGlucose: () => fetchJSON('/api/glucose/current'),
  getGlucoseHistory: (hours: number = 2) => fetchJSON(`/api/glucose/history?hours=${hours}`),
  getTimers: () => fetchJSON('/api/timers'),
  getSettings: () => fetchJSON('/api/settings'),
  getContacts: () => fetchJSON('/api/contacts'),
}
