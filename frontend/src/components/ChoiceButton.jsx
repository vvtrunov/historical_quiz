export default function ChoiceButton({ choice, onClick, state }) {
  // state: null | 'correct' | 'wrong' | 'missed'
  const base = 'choice-btn'
  const cls = state ? `${base} ${base}--${state}` : base

  return (
    <button className={cls} onClick={onClick} disabled={state !== null}>
      {choice.text}
    </button>
  )
}
