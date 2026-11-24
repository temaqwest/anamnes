import { api } from "@/shared/api"

export type Medication = {
  id: string
  name: string
  dose: string
  archived_at: string | null
} & (
  | { course_type: "regular"; schedule: string; start_date: string; end_date: string | null }
  | { course_type: "single"; intake_date: string; intake_time: string | null }
)

export type NewMedication = { name: string; dose: string } & (
  | { course_type: "regular"; schedule: string; start_date: string }
  | { course_type: "single"; intake_date: string; intake_time: string | null }
)

const fieldLabels = {
  name: "Название",
  dose: "Дозировка",
  course_type: "Тип приёма",
  schedule: "Режим приёма",
  start_date: "Дата начала",
  intake_date: "Дата приёма",
  intake_time: "Время приёма",
  end_date: "Дата окончания",
}

export function listMedications(signal: AbortSignal) {
  return api<Medication[]>("/medications/", { signal })
}

export function addMedication(record: NewMedication) {
  return api<Medication>("/medications/", { method: "POST", body: JSON.stringify(record) }, fieldLabels)
}

export function archiveMedication(id: string, endDate: string | null) {
  return api<Medication>(`/medications/${id}/archive/`, {
    method: "POST",
    body: JSON.stringify({ end_date: endDate }),
  }, fieldLabels)
}
