import { useState } from "react"
import { createStudy, suggestStudyMetadata, type Area, type StudyAreaSuggestion, type StudyFields } from "@/entities/study"
import { errorMessage } from "@/shared/api"
import { initializeAreaSuggestions } from "./area-suggestions"

export const batchLimit = 10
type Entry = {
  id: string
  file: File
  fields: StudyFields
  areaSuggestions: StudyAreaSuggestion[]
  status: "draft" | "sending" | "saved" | "failed"
  issue?: string
  documentId?: string
}

export function useUploadBatch(preselected: string[], areas: Area[]) {
  const [entries, setEntries] = useState<Entry[]>([])
  const [error, setError] = useState("")
  const [suggesting, setSuggesting] = useState(false)
  const [sending, setSending] = useState(false)

  function update(id: string, patch: Partial<Entry> | ((entry: Entry) => Partial<Entry>)) {
    setEntries((current) => current.map((entry) => entry.id === id
      ? { ...entry, ...(typeof patch === "function" ? patch(entry) : patch) }
      : entry))
  }

  function selectArea(id: string, slug: string) {
    update(id, ({ fields }) => ({ fields: { ...fields, areas: [...new Set([...fields.areas, slug])] } }))
  }

  async function add(files: File[]) {
    if (suggesting || sending || !files.length) return
    setError("")
    if (files.length > batchLimit - entries.length) {
      setError("За одну загрузку можно выбрать до 10 PDF. Сократите список файлов.")
      return
    }
    const pending = files.map((file): Entry => ({
      id: crypto.randomUUID(), file, status: "draft",
      fields: { title: file.name.replace(/\.pdf$/i, ""), category: "", study_date: "", areas: preselected },
      areaSuggestions: [],
      issue: /\.pdf$/i.test(file.name) ? undefined : "Выберите файл в формате PDF.",
    }))
    setEntries((current) => [...current, ...pending])
    const pdfs = pending.filter((entry) => !entry.issue)
    if (!pdfs.length) return
    setSuggesting(true)
    try {
      const suggestions = await suggestStudyMetadata(pdfs.map(({ file }) => file.name))
      const allowedSlugs = new Set(areas.map(({ slug }) => slug))
      pdfs.forEach((entry, index) => {
        const suggestion = suggestions[index]
        if (!suggestion) return
        update(entry.id, ({ fields }) => {
          const areaMatches = initializeAreaSuggestions(fields.areas, allowedSlugs, suggestion.area_suggestions)
          return {
            fields: { ...fields, title: suggestion.title, study_date: suggestion.study_date ?? "", areas: areaMatches.selected },
            areaSuggestions: areaMatches.suggestions,
          }
        })
      })
    } catch (error) {
      setError("Не удалось заполнить поля из имени файла. Их можно заполнить вручную. " + errorMessage(error))
    } finally {
      setSuggesting(false)
    }
  }

  const pending = entries.filter((entry) => entry.status !== "saved" && /\.pdf$/i.test(entry.file.name))
  const savedCount = entries.filter(({ status }) => status === "saved").length

  async function save(batch: Entry[]) {
    if (sending || suggesting) return
    setSending(true)
    setError("")
    try {
      for (const entry of batch) {
        update(entry.id, { status: "sending", issue: undefined })
        try {
          const saved = await createStudy(entry.file, entry.fields, entry.id)
          update(entry.id, { status: "saved", documentId: saved.id })
        } catch (error) {
          update(entry.id, { status: "failed", issue: errorMessage(error) })
        }
      }
    } finally {
      setSending(false)
    }
  }

  function remove(id: string) {
    setEntries((current) => current.filter((entry) => entry.id !== id))
  }

  return { entries, error, suggesting, sending, pending, savedCount, add, save, update, selectArea, remove }
}
