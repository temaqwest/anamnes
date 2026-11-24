export function groupStudyMonths<T extends { study_date: string }>(studies: readonly T[]) {
  const grouped = new Map<string, Map<string, T[]>>()
  for (const study of studies) {
    const day = study.study_date
    const month = day.slice(0, 7)
    if (!grouped.has(month)) grouped.set(month, new Map())
    const days = grouped.get(month)!
    if (!days.has(day)) days.set(day, [])
    days.get(day)!.push(study)
  }

  return Array.from(grouped).sort(([a], [b]) => b.localeCompare(a)).map(([key, days]) => {
    const end = new Date(key + "-01T00:00:00Z")
    end.setUTCMonth(end.getUTCMonth() + 1, 0)
    return {
      key,
      dayCount: end.getUTCDate(),
      days: Array.from(days).sort(([a], [b]) => a.localeCompare(b)).map(([date, studies]) => ({ date, studies })),
    }
  })
}
