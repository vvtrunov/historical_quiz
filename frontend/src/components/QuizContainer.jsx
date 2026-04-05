import { useEffect, useReducer, useCallback } from 'react'
import { fetchQuiz, submitResult } from '../api'
import QuestionCard from './QuestionCard'
import ScoreScreen from './ScoreScreen'
import LoadingSpinner from './LoadingSpinner'

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
        return { ...state, phase: 'submitting', index: next }
      return { ...state, index: next }
    }
    case 'DONE':
      return { ...state, phase: 'done' }
    case 'RESET':
      return init()
    default:
      return state
  }
}

export default function QuizContainer({ date, player }) {
  const [state, dispatch] = useReducer(reducer, null, init)

  const load = useCallback(() => {
    dispatch({ type: 'RESET' })
    fetchQuiz(date, player?.token)
      .then(data => dispatch({ type: 'LOADED', questions: data.questions }))
      .catch(err => dispatch({ type: 'ERROR', error: err.message }))
  }, [date, player])

  useEffect(() => { load() }, [load])

  useEffect(() => {
    if (state.phase !== 'submitting') return
    submitResult(date, state.score, state.questions.length, player?.token)
      .catch(() => {}) // silently ignore submit errors
      .finally(() => dispatch({ type: 'DONE' }))
  }, [state.phase, date, state.score, state.questions.length, player])

  const { phase, questions, index, score, error } = state

  if (phase === 'loading' || phase === 'submitting') {
    return (
      <div className="quiz-wrapper">
        <LoadingSpinner />
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
        <ScoreScreen
          score={score}
          total={questions.length}
          date={date}
          player={player}
          onPlayAgain={load}
        />
      </div>
    )
  }

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
