import { useEffect, useReducer, useCallback } from 'react'
import { fetchQuiz } from '../api'
import QuestionCard from './QuestionCard'

function init() {
  return { phase: 'loading', questions: [], index: 0, score: 0, error: null }
}

function reducer(state, action) {
  switch (action.type) {
    case 'LOADED':
      if (action.questions.length === 0)
        return { ...state, phase: 'empty', questions: [] }
      return { ...state, phase: 'playing', questions: action.questions }
    case 'ERROR':
      return { ...state, phase: 'error', error: action.error }
    case 'ANSWER':
      return { ...state, score: state.score + (action.correct ? 1 : 0) }
    case 'ADVANCE': {
      const next = state.index + 1
      if (next >= state.questions.length)
        return { ...state, phase: 'done', index: next }
      return { ...state, index: next }
    }
    case 'RESET':
      return init()
    default:
      return state
  }
}

export default function QuizContainer({ date }) {
  const [state, dispatch] = useReducer(reducer, null, init)

  const load = useCallback(() => {
    dispatch({ type: 'RESET' })
    fetchQuiz(date)
      .then(data => dispatch({ type: 'LOADED', questions: data.questions }))
      .catch(err => dispatch({ type: 'ERROR', error: err.message }))
  }, [date])

  useEffect(() => { load() }, [load])

  const { phase, questions, index, score, error } = state

  if (phase === 'loading') {
    return (
      <div className="quiz-wrapper">
        <p className="status-msg">Loading today&apos;s quiz…</p>
      </div>
    )
  }

  if (phase === 'error') {
    return (
      <div className="quiz-wrapper">
        <p className="status-msg status-msg--error">Failed to load quiz: {error}</p>
        <button className="btn" onClick={load}>Retry</button>
      </div>
    )
  }

  if (phase === 'empty') {
    return (
      <div className="quiz-wrapper">
        <p className="status-msg">No events recorded for this date. Come back tomorrow!</p>
      </div>
    )
  }

  if (phase === 'done') {
    return (
      <div className="quiz-wrapper">
        <div className="score-screen">
          <h2 className="score-screen__title">Quiz complete!</h2>
          <p className="score-screen__score">
            You scored <strong>{score}</strong> / {questions.length}
          </p>
          <button className="btn btn--primary" onClick={load}>
            Play Again
          </button>
        </div>
      </div>
    )
  }

  // phase === 'playing'
  return (
    <div className="quiz-wrapper">
      <h1 className="quiz-title">On This Day — {date}</h1>
      <QuestionCard
        key={index}
        question={questions[index]}
        index={index}
        total={questions.length}
        onNext={{
          onAnswer: (correct) => dispatch({ type: 'ANSWER', correct }),
          advance: () => dispatch({ type: 'ADVANCE' }),
        }}
      />
    </div>
  )
}
