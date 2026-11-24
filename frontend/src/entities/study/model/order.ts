import type { StudyDocument } from "./types"

const byTitle = new Intl.Collator("ru", { numeric: true })

export function orderStudies(documents: readonly StudyDocument[], order: string): StudyDocument[] {
  return [...documents].sort((a, b) => {
    if (order === "title") return byTitle.compare(a.title, b.title)
    return order === "oldest" ? a.study_date.localeCompare(b.study_date) : b.study_date.localeCompare(a.study_date)
  })
}
