import AuthGate from './components/AuthGate'
import QuizContainer from './components/QuizContainer'

function getTodayDate() {
  const now = new Date()
  const mm = String(now.getMonth() + 1).padStart(2, '0')
  const dd = String(now.getDate()).padStart(2, '0')
  return `${mm}-${dd}`
}

export default function App() {
  return (
    <AuthGate>
      {(player) => (
        <>
          <header className="app-header">
            <span className="app-header__name">👤 {player.name}</span>
          </header>
          <QuizContainer date={getTodayDate()} player={player} />
        </>
      )}
    </AuthGate>
  )
}
