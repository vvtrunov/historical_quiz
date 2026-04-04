import { useState, useEffect } from 'react'
import { fetchLeaderboard } from '../api'

export default function Leaderboard({ date, playerName }) {
  const [scope, setScope] = useState('daily')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    setData(null)
    fetchLeaderboard(scope, date)
      .then(setData)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [scope, date])

  return (
    <div className="leaderboard">
      <h3 className="leaderboard__title">Leaderboard</h3>
      <div className="leaderboard__tabs">
        <button
          className={`leaderboard__tab${scope === 'daily' ? ' leaderboard__tab--active' : ''}`}
          onClick={() => setScope('daily')}
        >
          Today
        </button>
        <button
          className={`leaderboard__tab${scope === 'alltime' ? ' leaderboard__tab--active' : ''}`}
          onClick={() => setScope('alltime')}
        >
          All Time
        </button>
      </div>

      {loading && <p className="leaderboard__status">Loading…</p>}
      {error   && <p className="leaderboard__status leaderboard__status--error">{error}</p>}

      {data && data.entries.length === 0 && (
        <p className="leaderboard__status">No results yet. Be the first!</p>
      )}

      {data && data.entries.length > 0 && (
        <table className="leaderboard__table">
          <thead>
            <tr>
              <th>#</th>
              <th>Name</th>
              {scope === 'daily'
                ? <><th>Score</th></>
                : <><th>Total</th><th>Quizzes</th></>
              }
            </tr>
          </thead>
          <tbody>
            {data.entries.map(entry => {
              const isMe = entry.name === playerName
              return (
                <tr key={entry.rank} className={isMe ? 'leaderboard__row--me' : ''}>
                  <td className="leaderboard__rank">{entry.rank}</td>
                  <td className="leaderboard__name">
                    {entry.name}{isMe ? ' ★' : ''}
                  </td>
                  {scope === 'daily'
                    ? <td className="leaderboard__score">{entry.score} / {entry.total}</td>
                    : <>
                        <td className="leaderboard__score">{entry.total_score}</td>
                        <td className="leaderboard__score">{entry.quizzes_played}</td>
                      </>
                  }
                </tr>
              )
            })}
          </tbody>
        </table>
      )}
    </div>
  )
}
