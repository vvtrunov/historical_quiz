export default function FeedbackBanner({ wasCorrect, correctText, onNext }) {
  return (
    <div className={`feedback-banner feedback-banner--${wasCorrect ? 'correct' : 'wrong'}`}>
      <p className="feedback-banner__message">
        {wasCorrect ? 'Correct!' : `Wrong — the correct answer was: "${correctText}"`}
      </p>
      <button className="btn btn--next" onClick={onNext}>
        Next
      </button>
    </div>
  )
}
