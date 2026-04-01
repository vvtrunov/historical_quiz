export default function ScoreScreen({ score, total, onPlayAgain }) {
  const pct = total > 0 ? Math.round((score / total) * 100) : 0

  function getMessage() {
    if (pct === 100) return 'Perfect score!'
    if (pct >= 70) return 'Great job!'
    if (pct >= 40) return 'Not bad!'
    return 'Better luck next time!'
  }

  return (
    <div className="score-screen">
      <h2 className="score-screen__title">Quiz complete!</h2>
      <p className="score-screen__message">{getMessage()}</p>
      <p className="score-screen__score">
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
