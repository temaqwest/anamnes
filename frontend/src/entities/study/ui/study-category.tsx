import {File, FileText, ScanLine, TestTubeDiagonal} from "lucide-react"
import {cn} from "@/shared/lib/cn"
import type {StudyCategory} from "../model/types"
import {Badge} from "@/shared/ui/badge";

export const studyCategories = {
  "": { label: "Без категории", icon: File, accent: "bg-muted text-muted-foreground" },
  doctor_report: { label: "Заключение врача", icon: FileText, accent: "bg-green-500 text-green-100 dark:bg-green-950 dark:text-green-200" },
  examination: { label: "Обследование", icon: ScanLine, accent: "bg-sky-500 text-sky-100 dark:bg-sky-950 dark:text-sky-200" },
  lab: { label: "Анализ", icon: TestTubeDiagonal, accent: "bg-purple-500 text-purple-100 dark:bg-purple-950 dark:text-purple-200" },
} as const

export function StudyCategoryIcon({ category }: { category: StudyCategory }) {
  const { icon: Icon, accent } = studyCategories[category] ?? studyCategories[""]
  return (
    <span aria-hidden="true" className={cn("grid size-9 shrink-0 place-items-center rounded-lg", accent)}>
      <Icon size={18} />
    </span>
  )
}

export function StudyCategoryLabel({ category }: { category: StudyCategory }) {
  const { label, accent, icon: Icon } = studyCategories[category] ?? studyCategories[""]
  return <Badge className={accent} variant="default" color={accent}><Icon/>{label}</Badge>
}
