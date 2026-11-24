import { api } from "@/shared/api"
import type { Area, StudyAreaSuggestion, StudyDocument, StudyFields } from "../model/types"

const fieldLabels: Readonly<Record<string, string>> = {
  title: "Название процедуры",
  category: "Категория",
  study_date: "Дата исследования",
  areas: "Предметные области",
}

type Suggestion = { title: string; study_date: string | null; area_suggestions?: StudyAreaSuggestion[] }

export function listStudyAreas() {
  return api<Area[]>("/areas/")
}

type AreaFields = Pick<Area, "name" | "description">

export function createStudyArea(fields: AreaFields) {
  return api<Area>("/areas/", { method: "POST", body: JSON.stringify(fields) })
}

export function updateStudyArea(slug: string, fields: AreaFields) {
  return api<Area>("/areas/" + encodeURIComponent(slug) + "/", {
    method: "PATCH", body: JSON.stringify(fields),
  })
}

export function listStudies({ area, category, query, signal }: {
  area: string
  category: string
  query: string
  signal: AbortSignal
}) {
  const params = new URLSearchParams()
  if (area) params.set("area", area)
  if (category) params.set("category", category)
  if (query) params.set("q", query)
  return api<StudyDocument[]>("/documents/" + (params.size ? "?" + params.toString() : ""), { signal })
}

export function getStudy(id: string, signal?: AbortSignal) {
  return api<StudyDocument>("/documents/" + encodeURIComponent(id) + "/", { signal })
}

export function updateStudy(id: string, fields: StudyFields) {
  return api<StudyDocument>("/documents/" + encodeURIComponent(id) + "/", {
    method: "PATCH", body: JSON.stringify(fields),
  }, fieldLabels)
}

export function suggestStudyMetadata(names: string[]) {
  return api<Suggestion[]>("/documents/suggestions/", {
    method: "POST", body: JSON.stringify({ names }),
  })
}

export function createStudy(file: File, fields: StudyFields, uploadKey: string) {
  const body = new FormData()
  body.append("file", file)
  body.append("upload_key", uploadKey)
  body.append("title", fields.title)
  body.append("category", fields.category)
  body.append("study_date", fields.study_date)
  fields.areas.forEach((area) => body.append("areas", area))
  return api<StudyDocument>("/documents/", { method: "POST", body }, fieldLabels)
}

export type StudyDeletion = { ids: string[] } | { all: true }

export function deleteStudies(selection: StudyDeletion) {
  return api<{ deleted: number }>("/documents/bulk-delete/", { method: "POST", body: JSON.stringify(selection) })
}
