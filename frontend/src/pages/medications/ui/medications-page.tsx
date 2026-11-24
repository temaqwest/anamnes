import { CalendarDays, Pill } from "lucide-react"
import { useEffect, useState } from "react"
import { errorMessage } from "@/shared/api"
import { Badge } from "@/shared/ui/badge"
import { Button } from "@/shared/ui/button"
import { listMedications, type Medication } from "../api/medications"
import { AddMedicationDialog, ArchiveMedicationDialog } from "./medication-dialogs"

function dateLabel(date: string) {
  return date.split("-").reverse().join(".")
}

function MedicationRow({ medication, onArchived }: { medication: Medication; onArchived?: (saved: Medication) => void }) {
  const regular = medication.course_type === "regular"
  return (
    <li className="grid items-start gap-3 px-4 py-4 sm:grid-cols-[minmax(0,1fr)_auto] sm:px-5">
      <div className="flex min-w-0 gap-3">
        <span className="grid size-9 shrink-0 place-items-center rounded-lg bg-accent text-accent-foreground">
          <Pill size={17} aria-hidden="true" />
        </span>
        <div className="min-w-0 space-y-1.5">
          <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
            <h3 className="min-w-0 font-medium break-words">{medication.name}</h3>
            <Badge variant="secondary">{regular ? "Регулярный курс" : "Разовый приём"}</Badge>
          </div>
          {medication.dose && <p className="text-sm break-words">{medication.dose}</p>}
          {regular && <p className="text-sm break-words text-muted-foreground">{medication.schedule}</p>}
          <p className="flex items-start gap-1.5 text-sm text-muted-foreground tabular-nums">
            <CalendarDays size={15} aria-hidden="true" className="mt-0.5 shrink-0" />
            <span>
              {regular ? (
                <>С <time dateTime={medication.start_date}>{dateLabel(medication.start_date)}</time>
                  {medication.end_date && <> по <time dateTime={medication.end_date}>{dateLabel(medication.end_date)}</time></>}
                </>
              ) : (
                <><time dateTime={medication.intake_date}>{dateLabel(medication.intake_date)}</time>
                  {medication.intake_time && (
                    <>{" · "}<time dateTime={medication.intake_time}>{medication.intake_time.replace(/:00$/, "")}</time></>
                  )}
                </>
              )}
            </span>
          </p>
        </div>
      </div>
      {onArchived && <div className="justify-self-start pl-12 sm:pl-0"><ArchiveMedicationDialog medication={medication} onSaved={onArchived} /></div>}
    </li>
  )
}

export function MedicationsPage() {
  const [medications, setMedications] = useState<Medication[] | null>(null)
  const [error, setError] = useState("")
  const [reload, setReload] = useState(0)
  const [announcement, setAnnouncement] = useState("")

  useEffect(() => {
    const controller = new AbortController()
    listMedications(controller.signal)
      .then((records) => { if (!controller.signal.aborted) setMedications(records) })
      .catch((error) => { if (!controller.signal.aborted) setError(errorMessage(error)) })
    return () => controller.abort()
  }, [reload])

  function handleAdded(saved: Medication) {
    setMedications((current) => [saved, ...(current ?? [])])
    setAnnouncement(`Запись «${saved.name}» добавлена.`)
  }

  function handleArchived(saved: Medication) {
    setMedications((current) => current?.map((medication) => medication.id === saved.id ? saved : medication) ?? [])
    setAnnouncement(`Запись «${saved.name}» перенесена в историю.`)
  }

  const active = medications?.filter(({ archived_at }) => !archived_at) ?? []
  const history = (medications ?? [])
    .filter(({ archived_at }) => archived_at !== null)
    .sort((a, b) => Date.parse(b.archived_at ?? "") - Date.parse(a.archived_at ?? ""))

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-3xl font-semibold tracking-tight">Лекарства</h1>
        <AddMedicationDialog disabled={!medications} onSaved={handleAdded} />
      </header>
      <p role="status" className="sr-only">{announcement}</p>
      {error ? (
        <div className="space-y-4 rounded-xl border bg-card p-5">
          <p role="alert">{error}</p>
          <Button onClick={() => { setError(""); setReload((value) => value + 1) }}>Повторить</Button>
        </div>
      ) : !medications ? (
        <p role="status" className="rounded-xl border bg-card p-5">Загружаем лекарства…</p>
      ) : (
        <>
          <section aria-labelledby="active-medications" className="overflow-hidden rounded-xl border bg-card">
            <h2 id="active-medications" className="border-b px-4 py-3 font-semibold sm:px-5">Принимаю сейчас</h2>
            {active.length > 0 ? (
              <ul className="divide-y">
                {active.map((medication) => <MedicationRow key={medication.id} medication={medication} onArchived={handleArchived} />)}
              </ul>
            ) : <p className="px-4 py-5 text-sm text-muted-foreground sm:px-5">Активных записей пока нет.</p>}
          </section>
          <section aria-labelledby="medication-history" className="overflow-hidden rounded-xl border bg-card">
            <h2 id="medication-history" className="border-b px-4 py-3 font-semibold sm:px-5">История</h2>
            {history.length > 0 ? (
              <ul className="divide-y">
                {history.map((medication) => <MedicationRow key={medication.id} medication={medication} />)}
              </ul>
            ) : <p className="px-4 py-5 text-sm text-muted-foreground sm:px-5">История пока пуста.</p>}
          </section>
        </>
      )}
    </div>
  )
}
