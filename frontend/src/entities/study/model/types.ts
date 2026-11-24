export type Area = { slug: string; name: string; description: string }
export type StudyCategory = "" | "doctor_report" | "examination" | "lab"

export type StudyAreaSuggestion = { slug: string; matched_text: string; auto_select: boolean }

export type StudyFields = {
  title: string
  category: StudyCategory
  study_date: string
  areas: string[]
}

export type StudyDocument = StudyFields & {
  id: string
  original_name: string
  file_url: string
  index_status: "pending" | "processing" | "ready" | "no_text" | "failed"
  search_match: { page: number; excerpt: string } | null
}
