import { AlertDialog } from "radix-ui"
import { useRef, useState } from "react"
import { deleteStudies, type StudyDeletion } from "@/entities/study"
import { errorMessage } from "@/shared/api"
import { Button } from "@/shared/ui/button"

export function DeleteStudiesDialog({ selection, onDismiss, onDeleted, onRestoreFocus }: {
  selection: StudyDeletion | null
  onDismiss: () => void
  onDeleted: (count: number) => void
  onRestoreFocus: () => void
}) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState("")
  const submitting = useRef(false)
  const all = selection !== null && "all" in selection
  const title = all ? "Удалить все документы?" : "Удалить выбранные документы?"
  const scope = selection && "ids" in selection
    ? "Выбрано документов: " + selection.ids.length + "."
    : "Будут удалены все документы в архиве, включая скрытые поиском или фильтрами."

  function changeOpen(open: boolean) {
    if (!open && !submitting.current) {
      setError("")
      onDismiss()
    }
  }

  async function confirm() {
    if (!selection || submitting.current) return
    submitting.current = true
    setBusy(true)
    setError("")
    try {
      const result = await deleteStudies(selection)
      onDeleted(result.deleted)
    } catch (error) {
      setError(errorMessage(error))
    } finally {
      submitting.current = false
      setBusy(false)
    }
  }

  return (
    <AlertDialog.Root open={selection !== null} onOpenChange={changeOpen}>
      <AlertDialog.Portal>
        <AlertDialog.Overlay className="fixed inset-0 z-50 bg-black/40" />
        <AlertDialog.Content
          className="fixed top-1/2 left-1/2 z-50 w-[calc(100%-2rem)] max-w-md -translate-1/2 space-y-4 rounded-xl border bg-card p-5 shadow-lg sm:p-6"
          onCloseAutoFocus={(event) => { event.preventDefault(); onRestoreFocus() }}>
          <AlertDialog.Title className="text-lg font-semibold">{title}</AlertDialog.Title>
          <AlertDialog.Description className="text-sm text-muted-foreground">
            {scope} Оригиналы PDF и данные поиска удаляются без возможности восстановления.
          </AlertDialog.Description>
          {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
          <div className="flex flex-wrap justify-end gap-2">
            <AlertDialog.Cancel asChild><Button variant="outline" disabled={busy}>Отмена</Button></AlertDialog.Cancel>
            <Button type="button" variant="destructive" disabled={busy} onClick={() => void confirm()}>
              {busy ? "Удаляем…" : all ? "Удалить все документы" : "Удалить выбранные"}
            </Button>
          </div>
        </AlertDialog.Content>
      </AlertDialog.Portal>
    </AlertDialog.Root>
  )
}
