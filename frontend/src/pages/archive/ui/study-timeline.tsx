import { ChevronLeft, ChevronRight } from "lucide-react"
import { useMemo } from "react"
import { Link, useSearchParams } from "react-router-dom"
import { formatStudyDate, StudyCategoryIcon, StudyCategoryLabel, studyDocumentPath, type StudyDocument } from "@/entities/study"
import { cn } from "@/shared/lib/cn"
import { Button } from "@/shared/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/ui/select"
import { groupStudyMonths } from "../model/study-timeline"

const monthLabel = new Intl.DateTimeFormat("ru", { month: "long", year: "numeric", timeZone: "UTC" })

export function StudyTimeline({ documents, returnTo }: { documents: StudyDocument[]; returnTo: string }) {
  const months = useMemo(() => groupStudyMonths(documents), [documents])
  const [params, setParams] = useSearchParams()
  const indexForMonth = (key: string | null) => Math.max(0, months.findIndex((month) => month.key === key))
  const monthIndex = indexForMonth(params.get("month"))
  const month = months[monthIndex]
  const active = month.days.find(({ date }) => date === params.get("day")) ?? month.days.at(-1)!
  const byNumber = new Map(month.days.map((day) => [Number(day.date.slice(8)), day]))

  function selectDate(monthKey: string, date?: string) {
    const updated = new URLSearchParams(window.location.search)
    updated.set("month", monthKey)
    if (date) updated.set("day", date)
    else updated.delete("day")
    setParams(updated, { replace: true })
  }

  function moveMonth(offset: number) {
    const current = new URLSearchParams(window.location.search).get("month")
    const target = months[indexForMonth(current) + offset]
    if (target) selectDate(target.key)
  }

  return (
    <div className="space-y-4 p-4 sm:p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-lg font-semibold">Таймлайн исследований</h2>
        <div className="flex min-w-0 items-center gap-2">
          <Button type="button" variant="outline" size="icon" disabled={monthIndex === months.length - 1}
            aria-label="Предыдущий месяц" title="Предыдущий месяц" onClick={() => moveMonth(1)}>
            <ChevronLeft />
          </Button>
          <Select value={month.key} onValueChange={(key) => selectDate(key)}>
            <SelectTrigger aria-label="Месяц"><SelectValue /></SelectTrigger>
            <SelectContent>
              {months.map(({ key }) => (
                <SelectItem key={key} value={key}>{monthLabel.format(new Date(key + "-01T00:00:00Z"))}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button type="button" variant="outline" size="icon" disabled={monthIndex === 0}
            aria-label="Следующий месяц" title="Следующий месяц" onClick={() => moveMonth(-1)}>
            <ChevronRight />
          </Button>
        </div>
      </div>
      <div className="overflow-x-auto rounded-lg border bg-muted/45 px-2 py-3"
        tabIndex={0} aria-label="Календарная шкала" role="region">
        <ol className="relative grid min-w-[48rem] items-center text-center before:pointer-events-none before:absolute before:inset-x-2 before:top-9 before:border-t before:border-input"
          style={{ gridTemplateColumns: "repeat(" + month.dayCount + ", minmax(0, 1fr))" }}>
          {Array.from({ length: month.dayCount }, (_, index) => {
            const number = index + 1
            const day = byNumber.get(number)
            return (
              <li key={number} className="relative flex min-w-0 flex-col items-center gap-1">
                <span className="text-xs tabular-nums text-muted-foreground" aria-hidden="true">{number}</span>
                {day ? (
                  <button type="button" aria-pressed={day.date === active.date}
                    aria-label={formatStudyDate(day.date) + " · Исследований: " + day.studies.length}
                    title={formatStudyDate(day.date) + " · " + day.studies.length}
                    onClick={() => selectDate(month.key, day.date)}
                    className={cn("grid size-6 place-items-center rounded-full border border-primary/40 text-xs font-medium focus-visible:outline-2 focus-visible:outline-ring",
                      day.date === active.date ? "bg-primary text-primary-foreground" : "bg-card text-primary hover:bg-accent")}>
                    {day.studies.length > 1 ? day.studies.length : <span className="size-1.5 rounded-full bg-current" />}
                  </button>
                ) : <span className="grid size-6 place-items-center"><span className="size-1 rounded-full bg-input" /></span>}
              </li>
            )
          })}
        </ol>
      </div>
      <section aria-label="Исследования выбранного дня">
        <h3 className="mb-2 text-sm font-medium"><time dateTime={active.date}>{formatStudyDate(active.date)}</time></h3>
        <ul className="space-y-2">
          {active.studies.map((study) => (
            <li key={study.id} className="flex items-start gap-3 rounded-lg border p-3">
              <StudyCategoryIcon category={study.category} />
              <div className="min-w-0 space-y-1">
                <Link to={studyDocumentPath(study)} state={{ returnTo }}
                  className="block font-medium break-words text-primary hover:underline">{study.title}</Link>
                <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
                  <StudyCategoryLabel category={study.category} />
                  {study.search_match && <span className="text-sm text-muted-foreground">Страница {study.search_match.page}</span>}
                </div>
              </div>
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}
