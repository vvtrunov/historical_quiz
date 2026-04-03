import { useState } from 'react'
import { login } from '../api'

const TOKEN_KEY = 'hq_token'
const NAME_KEY  = 'hq_name'

export function loadPlayer() {
  const token = localStorage.getItem(TOKEN_KEY)
  const name  = localStorage.getItem(NAME_KEY)
  return token && name ? { token, name } : null
}

function savePlayer(token, name) {
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(NAME_KEY, name)
}

export default function AuthGate({ children }) {
  const [player, setPlayer] = useState(() => loadPlayer())
  const [inputName, setInputName] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    const trimmed = inputName.trim()
    if (!trimmed) return
    setLoading(true)
    setError(null)
    try {
      const data = await login(trimmed)
      savePlayer(data.token, data.name)
      setPlayer({ token: data.token, name: data.name })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  if (!player) {
    return (
      <div className="auth-gate">
        <div className="auth-card">
          <h1 className="auth-card__title">Historical Quiz</h1>
          <p className="auth-card__subtitle">Enter your name to play</p>
          <form className="auth-card__form" onSubmit={handleSubmit}>
            <input
              className="auth-card__input"
              type="text"
              placeholder="Your name"
              maxLength={50}
              value={inputName}
              onChange={e => setInputName(e.target.value)}
              autoFocus
            />
            <button
              className="btn btn--primary"
              type="submit"
              disabled={loading || !inputName.trim()}
            >
              {loading ? 'Entering…' : 'Play'}
            </button>
          </form>
          {error && <p className="auth-card__error">{error}</p>}
        </div>
      </div>
    )
  }

  return children(player)
}
