import { ChevronLeft, ChevronRight, ExternalLink } from "lucide-react"
import { formatStudyDate, type StudyDocument } from "@/entities/study"
import { Button } from "@/shared/ui/button"
import { PdfPage } from "@/shared/ui/pdf-page"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/ui/select"
import { paneNavigation } from "../model/comparison-pair"

export function ComparePanel({ side, study, other, documents, onChange }: {
  side: "Левый документ" | "Правый документ"
  study: StudyDocument
  other: StudyDocument
  documents: StudyDocument[]
  onChange: (id: string) => void
}) {
  const { options, previous, next } = paneNavigation(documents, study.id, other.id)

  return (
    <section aria-label={side}
      className="flex h-[calc(100dvh_-_11rem)] min-h-[430px] min-w-0 flex-col gap-3 rounded-xl border bg-card p-3">
      <div className="space-y-2">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <h2 title={study.title} className="truncate text-lg font-semibold">{study.title}</h2>
            <time dateTime={study.study_date} className="text-sm tabular-nums text-muted-foreground">
              {formatStudyDate(study.study_date)}
            </time>
          </div>
          <Button asChild size="icon" variant="ghost" className="shrink-0">
            <a href={study.file_url} target="_blank" rel="noreferrer" aria-label="Открыть оригинал PDF"
              title="Открыть оригинал PDF"><ExternalLink /></a>
          </Button>
        </div>
        <div className="flex items-center gap-2">
          <Button type="button" variant="outline" size="icon" disabled={!previous}
            aria-label="Предыдущий документ" title="Предыдущий документ" onClick={() => previous && onChange(previous.id)}>
            <ChevronLeft />
          </Button>
          <Select value={study.id} onValueChange={onChange}>
            <SelectTrigger aria-label={"Выбрать " + side.toLocaleLowerCase("ru")} className="flex-1">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {options.map((option) => (
                <SelectItem key={option.id} value={option.id}>{formatStudyDate(option.study_date)} · {option.title}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button type="button" variant="outline" size="icon" disabled={!next}
            aria-label="Следующий документ" title="Следующий документ" onClick={() => next && onChange(next.id)}>
            <ChevronRight />
          </Button>
        </div>
      </div>
      <PdfPage key={study.id} url={study.file_url} initialPage={study.search_match?.page ?? 1} panel />
    </section>
  )
}
