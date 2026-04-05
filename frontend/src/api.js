function authHeaders(token) {
  return token ? { Authorization: `Token ${token}` } : {}
}

export async function login(name) {
  const response = await fetch('/api/auth/login/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  })
  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    throw new Error(data.error || `Server responded with ${response.status}`)
  }
  return response.json()
}

export async function fetchQuiz(date, token) {
  const response = await fetch(`/api/quiz/?date=${date}`, {
    headers: authHeaders(token),
  })
  if (!response.ok) {
    throw new Error(`Server responded with ${response.status}`)
  }
  return response.json()
}

export async function submitResult(date, score, total, token) {
  const response = await fetch('/api/quiz/submit/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders(token) },
    body: JSON.stringify({ date, score, total }),
  })
  if (!response.ok) {
    throw new Error(`Failed to submit result: ${response.status}`)
  }
  return response.json()
}

export async function fetchLeaderboard(scope, date) {
  const params = new URLSearchParams({ scope })
  if (scope === 'daily' && date) params.set('date', date)
  const response = await fetch(`/api/leaderboard/?${params}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch leaderboard: ${response.status}`)
  }
  return response.json()
}
