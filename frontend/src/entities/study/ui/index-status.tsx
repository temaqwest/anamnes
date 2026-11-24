import { Badge } from "@/shared/ui/badge"
import type { StudyDocument } from "../model/types"

const labels = {
  pending: "Текст в очереди",
  processing: "Извлекаем текст",
  no_text: "Текст не найден",
  failed: "Ошибка извлечения текста",
}

export function StudyIndexStatus({ status }: { status: StudyDocument["index_status"] }) {
  if (status === "ready") return null
  return <Badge variant="outline" className="text-muted-foreground">{labels[status]}</Badge>
}
