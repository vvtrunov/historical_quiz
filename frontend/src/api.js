export async function fetchQuiz(date) {
  const response = await fetch(`/api/quiz/?date=${date}`)
  if (!response.ok) {
    throw new Error(`Server responded with ${response.status}`)
  }
  return response.json()
}
