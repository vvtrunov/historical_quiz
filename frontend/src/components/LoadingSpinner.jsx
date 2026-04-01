export default function LoadingSpinner() {
  return (
    <div className="spinner-wrapper">
      <div className="spinner" role="status" aria-label="Loading" />
      <p className="spinner-label">Loading today&apos;s quiz…</p>
    </div>
  )
}
