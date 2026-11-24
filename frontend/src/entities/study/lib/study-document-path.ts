import type { StudyDocument } from "../model/types"

export function studyDocumentPath(study: Pick<StudyDocument, "id" | "search_match">): string {
  return "/documents/" + study.id + (study.search_match ? "?page=" + study.search_match.page : "")
}
