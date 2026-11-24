import { Check, FileText, Plus, UploadCloud, X } from "lucide-react"
import { type FormEvent, useRef } from "react"
import { Link, useLocation, useSearchParams } from "react-router-dom"
import { StudyAreas, StudyFileFields, type Area } from "@/entities/study"
import { StudyAreaDialog } from "@/features/edit-study-area"
import { Button } from "@/shared/ui/button"
import { batchLimit, useUploadBatch } from "../model/use-upload-batch"
import { AreaSuggestions } from "./area-suggestions"

export function UploadPage({ areas, onAreaSaved }: { areas: Area[]; onAreaSaved: (area: Area) => void }) {
  const input = useRef<HTMLInputElement>(null)
  const [params] = useSearchParams()
  const { state } = useLocation()
  const returnTo = state?.returnTo ?? "/"
  const preselected = areas.filter(({ slug }) => slug === params.get("area")).map(({ slug }) => slug)

  const { entries, error, suggesting, sending, pending, savedCount, add, save, update, selectArea, remove } = useUploadBatch(preselected, areas)

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    void save(pending)
  }

  function retry(entry: (typeof entries)[number]) {
    const date = document.getElementById(entry.id + "-date") as HTMLInputElement | null
    const title = document.getElementById(entry.id + "-title") as HTMLInputElement | null
    if (date?.reportValidity() && title?.reportValidity()) void save([entry])
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Загрузка документов</h1>
          <p className="mt-2 text-muted-foreground">Сверьте дату, название процедуры и предметные области перед сохранением.</p>
        </div>
        {!sending && <Button variant="outline" asChild><Link to={returnTo}>К архиву</Link></Button>}
      </header>
      <form className="space-y-5" onSubmit={submit}>
        <div className="flex flex-col items-stretch justify-between gap-4 rounded-xl border border-dashed border-primary/36 bg-card p-4 sm:flex-row sm:items-center sm:p-5"
          onDragOver={(event) => event.preventDefault()}
          onDrop={(event) => { event.preventDefault(); void add(Array.from(event.dataTransfer.files)) }}>
          <div className="flex items-center gap-4">
            <span className="grid size-11 place-items-center rounded-lg bg-accent text-accent-foreground"><UploadCloud size={21} /></span>
            <div>
              <p className="font-medium">Перетащите PDF сюда или выберите файлы</p>
              <p className="mt-1 text-sm text-muted-foreground">До 10 файлов, до 25 МБ каждый · {entries.length} из 10 выбрано</p>
            </div>
          </div>
          <input ref={input} type="file" accept=".pdf,application/pdf" multiple hidden
            onChange={(event) => { void add(Array.from(event.currentTarget.files ?? [])); event.currentTarget.value = "" }} />
          <Button type="button" variant="outline" disabled={sending || suggesting || entries.length === batchLimit}
            onClick={() => input.current?.click()}>Выбрать файлы</Button>
        </div>
        {error && <p role="alert" className="rounded-lg border border-destructive/20 bg-card p-3 text-sm text-destructive">{error}</p>}
        {suggesting && <p role="status" className="text-sm text-muted-foreground">Читаем имена файлов…</p>}
        {entries.map((entry) => (
          <section key={entry.id} className="space-y-4 rounded-xl border bg-card p-4 sm:p-5">
            <div className="flex items-center justify-between gap-3">
              <div className="flex min-w-0 items-center gap-2.5">
                <FileText size={18} className="shrink-0 text-primary" />
                <p className="font-medium break-all">{entry.file.name}</p>
              </div>
              {entry.status === "saved" ? (
                <span className="flex shrink-0 items-center gap-1.5 text-sm text-emerald-800"><Check size={17} />Сохранён</span>
              ) : <Button variant="ghost" size="icon" type="button" aria-label={"Убрать " + entry.file.name} disabled={sending || suggesting}
                onClick={() => remove(entry.id)}><X /></Button>}
            </div>
            {/\.pdf$/i.test(entry.file.name) && (
              <>
                <StudyFileFields id={entry.id} value={entry.fields} disabled={suggesting || sending || entry.status === "saved"}
                  onChange={(fields) => update(entry.id, { fields })} />
                <StudyAreas areas={areas} selected={entry.fields.areas} disabled={suggesting || sending || entry.status === "saved"}
                  onChange={(selected) => update(entry.id, { fields: { ...entry.fields, areas: selected } })} />
                {entry.status !== "saved" && <AreaSuggestions
                  areas={areas} suggestions={entry.areaSuggestions} selected={entry.fields.areas} disabled={suggesting || sending}
                  onSelect={(slug) => selectArea(entry.id, slug)} />}
                {entry.status !== "saved" && <StudyAreaDialog
                  trigger={<Button type="button" variant="outline" size="sm" disabled={suggesting || sending}>
                    <Plus />Добавить область
                  </Button>}
                  onSaved={(area) => {
                    onAreaSaved(area)
                    selectArea(entry.id, area.slug)
                  }} />}
              </>
            )}
            {entry.issue && <p role="alert" className="text-sm text-destructive">{entry.issue}</p>}
            {entry.status === "failed" && <Button type="button" variant="outline" size="sm"
              disabled={sending || suggesting} onClick={() => retry(entry)}>Повторить загрузку файла</Button>}
            {entry.documentId && <Link to={"/documents/" + entry.documentId} state={{ returnTo }}
              className="text-sm font-medium text-primary hover:underline">Открыть PDF</Link>}
          </section>
        ))}
        {entries.length > 0 && (
          <div className="flex flex-wrap items-center justify-end gap-4">
            {savedCount > 0 && <p role="status" className="text-sm text-muted-foreground">Сохранено: {savedCount} из {entries.length}</p>}
            {pending.length > 0 && <Button disabled={suggesting || sending}>{sending ? "Сохраняем…" : "Сохранить документы"}</Button>}
            {pending.length === 0 && savedCount > 0 && <Button asChild><Link to={returnTo}>Вернуться в архив</Link></Button>}
          </div>
        )}
      </form>
    </div>
  )
}
