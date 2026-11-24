import { Archive, Plus } from "lucide-react"
import { Dialog } from "radix-ui"
import { type FormEvent, type ReactNode, useId, useRef, useState } from "react"
import { errorMessage } from "@/shared/api"
import { Button } from "@/shared/ui/button"
import { Input } from "@/shared/ui/input"
import { Label } from "@/shared/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/ui/select"
import { addMedication, archiveMedication, type Medication, type NewMedication } from "../api/medications"

function localToday() {
  const today = new Date()
  const pad = (value: number) => String(value).padStart(2, "0")
  return `${today.getFullYear()}-${pad(today.getMonth() + 1)}-${pad(today.getDate())}`
}

function MedicationDialogContent({ title, children }: { title: string; children: ReactNode }) {
  return (
    <Dialog.Portal>
      <Dialog.Overlay className="fixed inset-0 z-50 bg-black/40" />
      <Dialog.Content aria-describedby={undefined}
        className="fixed top-1/2 left-1/2 z-50 max-h-[calc(100dvh-2rem)] w-[calc(100%-2rem)] max-w-md -translate-1/2 overflow-y-auto rounded-xl border bg-card p-5 shadow-lg sm:p-6">
        <Dialog.Title className="text-lg font-semibold">{title}</Dialog.Title>
        {children}
      </Dialog.Content>
    </Dialog.Portal>
  )
}

function MedicationDialogActions({ saving, error, submitLabel }: {
  saving: boolean
  error: string
  submitLabel: string
}) {
  return (
    <>
      {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
      <div className="flex flex-wrap justify-end gap-2">
        <Dialog.Close asChild><Button variant="outline" type="button" disabled={saving}>Отмена</Button></Dialog.Close>
        <Button type="submit" disabled={saving}>{saving ? "Сохраняем…" : submitLabel}</Button>
      </div>
    </>
  )
}

export function AddMedicationDialog({ disabled, onSaved }: { disabled: boolean; onSaved: (saved: Medication) => void }) {
  const [open, setOpen] = useState(false)
  const [courseType, setCourseType] = useState<NewMedication["course_type"]>("regular")
  const [saving, setSaving] = useState(false)
  const submitting = useRef(false)
  const [error, setError] = useState("")
  const id = useId()

  function changeOpen(next: boolean) {
    if (submitting.current) return
    if (next) {
      setCourseType("regular")
      setError("")
    }
    setOpen(next)
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (submitting.current) return
    const form = new FormData(event.currentTarget)
    const read = (key: string) => String(form.get(key) ?? "").trim()
    const common = { name: read("name"), dose: read("dose") }
    const record: NewMedication = courseType === "regular"
      ? { ...common, course_type: "regular", schedule: read("schedule"), start_date: read("start_date") }
      : { ...common, course_type: "single", intake_date: read("intake_date"), intake_time: read("intake_time") || null }
    submitting.current = true
    setSaving(true)
    setError("")
    try {
      const saved = await addMedication(record)
      setOpen(false)
      onSaved(saved)
    } catch (error) {
      setError(errorMessage(error))
    } finally {
      submitting.current = false
      setSaving(false)
    }
  }

  return (
    <Dialog.Root open={open} onOpenChange={changeOpen}>
      <Dialog.Trigger asChild><Button disabled={disabled}><Plus />Добавить лекарство</Button></Dialog.Trigger>
      <MedicationDialogContent title="Добавить лекарство">
        <form className="mt-4 space-y-4" onSubmit={submit}>
          <fieldset className="min-w-0 space-y-4" disabled={saving}>
            <div className="space-y-2">
              <Label htmlFor={`${id}-name`}>Название</Label>
              <Input id={`${id}-name`} name="name" required maxLength={160} />
            </div>
            <div className="space-y-2">
              <Label htmlFor={`${id}-dose`}>Дозировка <span className="font-normal text-muted-foreground">(необязательно)</span></Label>
              <Input id={`${id}-dose`} name="dose" maxLength={120} />
            </div>
            <div className="space-y-2">
              <Label htmlFor={`${id}-course`}>Тип приёма</Label>
              <Select value={courseType} disabled={saving}
                onValueChange={(value) => setCourseType(value === "single" ? "single" : "regular")}>
                <SelectTrigger id={`${id}-course`} className="w-full"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="regular">Регулярный курс</SelectItem>
                  <SelectItem value="single">Разовый приём</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <fieldset className="min-w-0 space-y-4" hidden={courseType !== "regular"} disabled={courseType !== "regular"}>
              <div className="space-y-2">
                <Label htmlFor={`${id}-schedule`}>Режим приёма</Label>
                <Input id={`${id}-schedule`} name="schedule" required maxLength={240} />
              </div>
              <div className="space-y-2">
                <Label htmlFor={`${id}-start`}>Дата начала</Label>
                <Input id={`${id}-start`} name="start_date" type="date" required defaultValue={localToday()} />
              </div>
            </fieldset>
            <fieldset className="min-w-0" hidden={courseType !== "single"} disabled={courseType !== "single"}>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="min-w-0 space-y-2">
                  <Label htmlFor={`${id}-intake-date`}>Дата приёма</Label>
                  <Input id={`${id}-intake-date`} name="intake_date" type="date" required />
                </div>
                <div className="min-w-0 space-y-2">
                  <Label htmlFor={`${id}-intake-time`}>Время <span className="font-normal text-muted-foreground">(необязательно)</span></Label>
                  <Input id={`${id}-intake-time`} name="intake_time" type="time" />
                </div>
              </div>
            </fieldset>
          </fieldset>
          <MedicationDialogActions saving={saving} error={error} submitLabel="Добавить" />
        </form>
      </MedicationDialogContent>
    </Dialog.Root>
  )
}

export function ArchiveMedicationDialog({ medication, onSaved }: {
  medication: Medication
  onSaved: (saved: Medication) => void
}) {
  const [open, setOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const submitting = useRef(false)
  const [error, setError] = useState("")
  const dateId = useId()

  function changeOpen(next: boolean) {
    if (submitting.current) return
    if (next) setError("")
    setOpen(next)
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (submitting.current) return
    const form = new FormData(event.currentTarget)
    const endDate = form.get("end_date")
    submitting.current = true
    setSaving(true)
    setError("")
    try {
      const saved = await archiveMedication(medication.id, typeof endDate === "string" ? endDate : null)
      setOpen(false)
      onSaved(saved)
    } catch (error) {
      setError(errorMessage(error))
    } finally {
      submitting.current = false
      setSaving(false)
    }
  }

  return (
    <Dialog.Root open={open} onOpenChange={changeOpen}>
      <Dialog.Trigger asChild>
        <Button type="button" variant="outline" size="sm" aria-label={`В историю — ${medication.name}`}>
          <Archive />В историю
        </Button>
      </Dialog.Trigger>
      <MedicationDialogContent title="Перенести в историю">
        <p className="mt-1 text-sm break-words text-muted-foreground">{medication.name}</p>
        <form className="mt-4 space-y-4" onSubmit={submit}>
          {medication.course_type === "regular" && (
            <div className="space-y-2">
              <Label htmlFor={dateId}>Фактическая дата окончания</Label>
              <Input id={dateId} name="end_date" type="date" required defaultValue={localToday()}
                min={medication.start_date} disabled={saving} />
            </div>
          )}
          <MedicationDialogActions saving={saving} error={error} submitLabel="Перенести" />
        </form>
      </MedicationDialogContent>
    </Dialog.Root>
  )
}
