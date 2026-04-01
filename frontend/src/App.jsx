import QuizContainer from './components/QuizContainer'

function getTodayDate() {
  const now = new Date()
  const mm = String(now.getMonth() + 1).padStart(2, '0')
  const dd = String(now.getDate()).padStart(2, '0')
  return `${mm}-${dd}`
}

export default function App() {
  return <QuizContainer date={getTodayDate()} />
}
