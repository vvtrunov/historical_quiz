import { useState } from 'react'
import ChoiceButton from './ChoiceButton'
import FeedbackBanner from './FeedbackBanner'

export default function QuestionCard({ question, index, total, onNext }) {
  const [selected, setSelected] = useState(null)

  function handleChoiceClick(choice) {
    if (selected !== null) return
    setSelected(choice)
    onNext.onAnswer(choice.correct)
  }

  function getChoiceState(choice) {
    if (selected === null) return null
    if (choice.id === selected.id) return choice.correct ? 'correct' : 'wrong'
    if (choice.correct) return 'missed'
    return null
  }

  const correctChoice = question.choices.find(c => c.correct)

  return (
    <div className="question-card">
      <div className="question-card__header">
        <span className="question-card__progress">
          Question {index + 1} / {total}
        </span>
        <span className="question-card__year">{question.year}</span>
      </div>

      <p className="question-card__prompt">
        Which event happened on this day in <strong>{question.year}</strong>?
      </p>

      <div className="question-card__choices">
        {question.choices.map(choice => (
          <ChoiceButton
            key={choice.id}
            choice={choice}
            onClick={() => handleChoiceClick(choice)}
            state={getChoiceState(choice)}
          />
        ))}
      </div>

      {selected !== null && (
        <FeedbackBanner
          wasCorrect={selected.correct}
          correctText={correctChoice.text}
          onNext={() => {
            setSelected(null)
            onNext.advance()
          }}
        />
      )}
    </div>
  )
}
