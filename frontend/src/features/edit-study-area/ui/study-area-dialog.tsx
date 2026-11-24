import { Dialog } from "radix-ui"
import { type FormEvent, type ReactElement, useId, useState } from "react"
import { createStudyArea, updateStudyArea, type Area } from "@/entities/study"
import { errorMessage } from "@/shared/api"
import { Button } from "@/shared/ui/button"
import { Input } from "@/shared/ui/input"
import { Label } from "@/shared/ui/label"

export function StudyAreaDialog({ area, trigger, onSaved }: {
  area?: Area
  trigger: ReactElement
  onSaved: (area: Area) => void
}) {
  const [open, setOpen] = useState(false)
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState("")
  const id = useId()

  function changeOpen(next: boolean) {
    if (saving) return
    if (next) {
      setName(area?.name ?? "")
      setDescription(area?.description ?? "")
      setError("")
    }
    setOpen(next)
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    event.stopPropagation()
    if (!name.trim() || saving) return
    setSaving(true)
    setError("")
    try {
      const fields = { name, description }
      const saved = await (area ? updateStudyArea(area.slug, fields) : createStudyArea(fields))
      onSaved(saved)
      setOpen(false)
    } catch (error) {
      setError(errorMessage(error))
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog.Root open={open} onOpenChange={changeOpen}>
      <Dialog.Trigger asChild>{trigger}</Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-black/40" />
        <Dialog.Content className="fixed top-1/2 left-1/2 z-50 max-h-[90dvh] w-[calc(100%_-_2rem)] max-w-md -translate-1/2 overflow-y-auto rounded-xl border bg-card p-5 shadow-lg sm:p-6"
          aria-describedby={undefined}>
          <Dialog.Title className="text-lg font-semibold">
            {area ? "Редактировать область" : "Добавить область"}
          </Dialog.Title>
          <form onSubmit={submit} className="mt-5 space-y-4">
            <div className="space-y-2">
              <Label htmlFor={id + "-name"}>Название области</Label>
              <Input id={id + "-name"} value={name} maxLength={100} required disabled={saving}
                onChange={(event) => setName(event.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor={id + "-description"}>Текст подсказки <span className="font-normal text-muted-foreground">(необязательно)</span></Label>
              <textarea id={id + "-description"} value={description} maxLength={300} rows={3} disabled={saving}
                className="block w-full resize-y rounded-md border border-input bg-transparent px-3 py-2 text-base shadow-xs outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 disabled:opacity-50 md:text-sm dark:bg-input/30"
                onChange={(event) => setDescription(event.target.value)} />
            </div>
            {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
            <div className="flex justify-end gap-2">
              <Dialog.Close asChild><Button variant="outline" type="button" disabled={saving}>Отмена</Button></Dialog.Close>
              <Button disabled={saving || !name.trim()}>{saving ? "Сохраняем…" : area ? "Сохранить" : "Создать"}</Button>
            </div>
          </form>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
