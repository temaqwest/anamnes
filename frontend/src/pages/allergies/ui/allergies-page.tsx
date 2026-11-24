import { Plus } from "lucide-react"
import { type FormEvent, useEffect, useState } from "react"
import { errorMessage } from "@/shared/api"
import { Button } from "@/shared/ui/button"
import { Input } from "@/shared/ui/input"
import { Label } from "@/shared/ui/label"
import { addAllergy, listAllergies, type Allergy } from "../api/allergies"

export function AllergiesPage() {
  const [allergies, setAllergies] = useState<Allergy[] | null>(null)
  const [loadError, setLoadError] = useState("")
  const [reload, setReload] = useState(0)
  const [name, setName] = useState("")
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState("")
  const [announcement, setAnnouncement] = useState("")

  useEffect(() => {
    const controller = new AbortController()
    listAllergies(controller.signal)
      .then((records) => { if (!controller.signal.aborted) setAllergies(records) })
      .catch((error) => { if (!controller.signal.aborted) setLoadError(errorMessage(error)) })
    return () => controller.abort()
  }, [reload])

  async function handleAdd(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!name.trim() || saving) return
    setSaveError("")
    setAnnouncement("")
    setSaving(true)
    try {
      const saved = await addAllergy(name)
      setAllergies((current) => [saved, ...(current ?? [])])
      setName("")
      setAnnouncement(`Аллерген «${saved.name}» добавлен.`)
    } catch (error) {
      setSaveError(errorMessage(error))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <h1 className="text-3xl font-semibold tracking-tight">Аллергии</h1>
      <p role="status" className="sr-only">{announcement}</p>
      {loadError ? (
        <div className="space-y-4 rounded-xl border bg-card p-5">
          <p role="alert">{loadError}</p>
          <Button onClick={() => { setLoadError(""); setReload((value) => value + 1) }}>Повторить</Button>
        </div>
      ) : !allergies ? (
        <p role="status" className="rounded-xl border bg-card p-5">Загружаем список аллергенов…</p>
      ) : (
        <div className="rounded-xl border bg-card">
          <form className="space-y-2 border-b p-4 sm:p-5" onSubmit={handleAdd}>
            <Label htmlFor="allergy-name">Название аллергена</Label>
            <div className="grid max-w-2xl gap-2 sm:grid-cols-[minmax(0,1fr)_auto]">
              <Input
                id="allergy-name"
                autoComplete="off"
                maxLength={160}
                readOnly={saving}
                required
                value={name}
                onChange={(event) => { setName(event.target.value); setSaveError("") }}
              />
              <Button type="submit" disabled={!name.trim() || saving}>
                <Plus aria-hidden="true" />{saving ? "Добавляем…" : "Добавить аллерген"}
              </Button>
            </div>
            {saveError && <p role="alert" className="text-sm text-destructive">{saveError}</p>}
          </form>
          {allergies.length ? (
            <ul aria-label="Аллергены" className="divide-y">
              {allergies.map((allergy) => (
                <li key={allergy.id} className="px-4 py-3 font-medium break-words sm:px-5">{allergy.name}</li>
              ))}
            </ul>
          ) : <p className="px-4 py-5 text-sm text-muted-foreground sm:px-5">Список аллергенов пуст.</p>}
        </div>
      )}
    </div>
  )
}
