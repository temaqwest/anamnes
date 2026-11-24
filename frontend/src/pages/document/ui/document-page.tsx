import { ExternalLink, Pencil } from "lucide-react"
import { type FormEvent, useEffect, useState } from "react"
import { Link, useLocation, useParams, useSearchParams } from "react-router-dom"
import { formatStudyDate, getStudy, StudyAreaBadge, StudyAreas, StudyCategoryIcon, StudyCategoryLabel, StudyFileFields, StudyIndexStatus, updateStudy,
  type Area, type StudyDocument, type StudyFields } from "@/entities/study"
import { errorMessage } from "@/shared/api"
import { Button } from "@/shared/ui/button"
import { PdfPage } from "@/shared/ui/pdf-page"

export function DocumentPage({ areas }: { areas: Area[] }) {
  const { id } = useParams()
  const { state } = useLocation()
  const [params] = useSearchParams()
  const parsedPage = Number(params.get("page"))
  const initialPage = Number.isSafeInteger(parsedPage) && parsedPage > 0 ? parsedPage : 1
  return <DocumentView key={id} id={id!} areas={areas} returnTo={state?.returnTo ?? "/"} initialPage={initialPage} />
}

function DocumentView({ id, areas, returnTo, initialPage }: {
  id: string
  areas: Area[]
  returnTo: string
  initialPage: number
}) {
  const [study, setStudy] = useState<StudyDocument | null>(null)
  const [fields, setFields] = useState<StudyFields | null>(null)
  const [error, setError] = useState("")
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    const controller = new AbortController()
    getStudy(id, controller.signal)
      .then(setStudy).catch((error) => { if (!controller.signal.aborted) setError(errorMessage(error)) })
    return () => controller.abort()
  }, [id])

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!fields) return
    setSaving(true)
    setError("")
    try {
      setStudy(await updateStudy(id, fields))
      setFields(null)
    } catch (error) {
      setError(errorMessage(error))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="mx-auto max-w-7xl space-y-5">
      <Button asChild variant="outline"><Link to={returnTo}>К архиву</Link></Button>
      {!study ? (
        error ? <p role="alert" className="text-destructive">{error}</p> : <p role="status">Загружаем исследование…</p>
      ) : (
        <>
          <header className="flex flex-wrap items-start justify-between gap-4">
            <div className="flex min-w-0 items-start gap-3">
              <StudyCategoryIcon category={study.category} />
              <div className="min-w-0">
                <h1 className="text-2xl font-semibold break-words tracking-tight sm:text-3xl">{study.title}</h1>
                <p className="mt-1 text-sm break-all text-muted-foreground">{study.original_name}</p>
              </div>
            </div>
            <Button asChild variant="outline" className="shrink-0">
              <a href={study.file_url} target="_blank" rel="noreferrer"><ExternalLink />Открыть оригинал</a>
            </Button>
          </header>
          <div className="rounded-xl border bg-card p-4">
            {fields ? (
              <form onSubmit={save} className="space-y-4">
                <StudyFileFields id="edit-study" value={fields} onChange={setFields} disabled={saving} />
                <StudyAreas areas={areas} selected={fields.areas} onChange={(areas) => setFields({ ...fields, areas })} disabled={saving} />
                {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
                <div className="flex gap-2">
                  <Button disabled={saving}>Сохранить</Button>
                  <Button type="button" variant="outline" disabled={saving} onClick={() => { setFields(null); setError("") }}>Отмена</Button>
                </div>
              </form>
            ) : (
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex flex-wrap items-center gap-2.5">
                  <time dateTime={study.study_date} className="text-sm font-medium">{formatStudyDate(study.study_date)}</time>
                  <StudyCategoryLabel category={study.category} />
                  {areas.filter(({ slug }) => study.areas.includes(slug)).map((area) => (
                    <StudyAreaBadge key={area.slug} area={area} />
                  ))}
                  <StudyIndexStatus status={study.index_status} />
                </div>
                <Button type="button" variant="ghost" onClick={() => setFields({
                  title: study.title, category: study.category, study_date: study.study_date, areas: study.areas,
                })}><Pencil />Редактировать</Button>
              </div>
            )}
          </div>
          <PdfPage key={study.file_url + ":" + initialPage} url={study.file_url} initialPage={initialPage} />
        </>
      )}
    </div>
  )
}
