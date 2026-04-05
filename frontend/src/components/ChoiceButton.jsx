function cleanText(text) {
  return text.replace(/\[[^\]]*\]/g, '').trim()
}

export default function ChoiceButton({ choice, onClick, state }) {
  // state: null | 'correct' | 'wrong' | 'missed'
  const base = 'choice-btn'
  const cls = state ? `${base} ${base}--${state}` : base

  return (
    <button className={cls} onClick={onClick} disabled={state !== null}>
      {cleanText(choice.text)}
    </button>
  )
}
