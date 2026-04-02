import { useEffect } from 'react'
import confetti from 'canvas-confetti'

export default function ScoreScreen({ score, total, onPlayAgain }) {
  const pct = total > 0 ? Math.round((score / total) * 100) : 0

  useEffect(() => {
    if (pct === 0) return
    const particleCount = Math.round(60 + pct * 1.4)  // 60–200 particles
    const spread = pct === 100 ? 100 : 60

    confetti({ particleCount, spread, origin: { y: 0.6 } })

    if (pct === 100) {
      // Extra side bursts for a perfect score
      setTimeout(() => confetti({ particleCount: 60, angle: 60,  spread: 55, origin: { x: 0 } }), 250)
      setTimeout(() => confetti({ particleCount: 60, angle: 120, spread: 55, origin: { x: 1 } }), 400)
    }
  }, [pct])

  function getMessage() {
    if (pct === 100) return 'Perfect score! 🎉'
    if (pct >= 70)  return 'Great job!'
    if (pct >= 40)  return 'Not bad!'
    return 'Better luck next time!'
  }

  return (
    <div className="score-screen">
      <h2 className="score-screen__title">Quiz complete!</h2>
      <p className="score-screen__message">{getMessage()}</p>
      <p className="score-screen__score score-screen__score--pop">
        <span className="score-screen__number">{score}</span>
        <span className="score-screen__divider"> / </span>
        <span className="score-screen__total">{total}</span>
      </p>
      <p className="score-screen__pct">{pct}%</p>
      <button className="btn btn--primary" onClick={onPlayAgain}>
        Play Again
      </button>
    </div>
  )
}
