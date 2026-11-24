export function findComparison<T extends { id: string }>(
  documents: readonly T[],
  leftId: string | null,
  rightId: string | null,
) {
  if (leftId === rightId) return null
  const left = documents.find(({ id }) => id === leftId)
  const right = documents.find(({ id }) => id === rightId)
  return left && right ? { left, right } : null
}

export function paneNavigation<T extends { id: string }>(
  documents: readonly T[],
  currentId: string,
  otherId: string,
) {
  const options = documents.filter(({ id }) => id !== otherId)
  const index = options.findIndex(({ id }) => id === currentId)
  return { options, previous: options[index - 1], next: options[index + 1] }
}
