import { CalendarDays, Columns2, FolderOpen, List, Plus, RefreshCw, Search, Tags, Trash2 } from "lucide-react"
import { useEffect, useRef, useState } from "react"
import { Link, useSearchParams } from "react-router-dom"
import { formatStudyDate, listStudies, orderStudies, StudyAreaBadge, StudyAreaHint, studyCategories, StudyCategoryIcon, StudyCategoryLabel,
  studyDocumentPath, StudyIndexStatus, type Area, type StudyDeletion, type StudyDocument } from "@/entities/study"
import { errorMessage } from "@/shared/api"
import { Button } from "@/shared/ui/button"
import { Checkbox } from "@/shared/ui/checkbox"
import { Input } from "@/shared/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/shared/ui/table"
import { DeleteStudiesDialog } from "./delete-studies-dialog"
import { StudyAreasPanel } from "./study-areas-panel"
import { StudyTimeline } from "./study-timeline"

type ArchiveResponse = { key: string; documents: StudyDocument[] } | { key: string; error: string }

export function ArchivePage({ areas, onAreaSaved }: { areas: Area[]; onAreaSaved: (area: Area) => void }) {
  const [params, setParams] = useSearchParams()
  const [response, setResponse] = useState<ArchiveResponse | null>(null)
  const [reload, setReload] = useState(0)
  const [showAreas, setShowAreas] = useState(false)
  const [selectedIds, setSelectedIds] = useState<string[]>([])
  const [deletion, setDeletion] = useState<StudyDeletion | null>(null)
  const [deletedCount, setDeletedCount] = useState<number | null>(null)
  const archiveHeading = useRef<HTMLHeadingElement>(null)
  const deleteTrigger = useRef<HTMLButtonElement>(null)
  const area = params.get("area") ?? ""
  const activeArea = areas.find(({ slug }) => slug === area)
  const category = params.get("category") ?? ""
  const query = params.get("q") ?? ""
  const term = query.trim()
  const hasFilters = Boolean(area || category || term)
  const sort = params.get("sort") ?? "newest"
  const timeline = params.get("view") === "timeline"
  const requestKey = JSON.stringify([area, category, term, reload])
  const current = response?.key === requestKey ? response : null
  const error = current && "error" in current ? current.error : ""

  useEffect(() => {
    const controller = new AbortController()
    const timer = window.setTimeout(() => {
      listStudies({ area, category, query: term, signal: controller.signal })
        .then((documents) => {
          if (!controller.signal.aborted) setResponse({ key: requestKey, documents })
        })
        .catch((error) => {
          if (!controller.signal.aborted) setResponse({ key: requestKey, error: errorMessage(error) })
        })
    }, term ? 200 : 0)
    return () => {
      window.clearTimeout(timer)
      controller.abort()
    }
  }, [area, category, term, requestKey])

  function setFilter(key: string, value: string) {
    const next = new URLSearchParams(window.location.search)
    if (value) next.set(key, value)
    else next.delete(key)
    if (key === "area" || key === "category" || key === "q") setSelectedIds([])
    setParams(next, { replace: true })
  }

  const documents = current && "documents" in current ? current.documents : null
  const results = documents && orderStudies(documents, sort)
  const visibleIds = new Set(documents?.map(({ id }) => id))
  const selected = selectedIds.filter((id) => visibleIds.has(id))
  const selectedSet = new Set(selected)
  const allVisibleSelected = visibleIds.size > 0 && selected.length === visibleIds.size
  const comparisonParams = new URLSearchParams(params)
  if (selected.length === 2) {
    comparisonParams.set("left", selected[0])
    comparisonParams.set("right", selected[1])
  }
  const returnTo = params.size ? "/?" + params.toString() : "/"

  function showDeletion(selection: StudyDeletion, trigger: HTMLButtonElement) {
    deleteTrigger.current = trigger
    setDeletedCount(null)
    setDeletion(selection)
  }

  function finishDeletion(count: number) {
    setDeletion(null)
    setSelectedIds([])
    setDeletedCount(count)
    setReload((value) => value + 1)
  }

  function restoreDeleteFocus() {
    const trigger = deleteTrigger.current
    if (trigger?.isConnected && !trigger.disabled) trigger.focus()
    else archiveHeading.current?.focus()
  }

  return (
    <div className="mx-auto max-w-7xl space-y-4 sm:space-y-6">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <h1 ref={archiveHeading} tabIndex={-1} className="text-2xl font-semibold tracking-tight sm:text-3xl">Архив исследований</h1>
        <div className="flex flex-wrap gap-2">
          {!timeline && (selected.length === 2 ? (
            <Button variant="outline" asChild>
              <Link to={"/compare?" + comparisonParams.toString()}><Columns2 />Сравнить два PDF</Link>
            </Button>
          ) : (
            <Button type="button" variant="outline" disabled>
              <Columns2 />{selected.length < 2 ? "Сравнить (" + selected.length + "/2)" : "Сравнить два PDF"}
            </Button>
          ))}
          <Button type="button" variant="outline" aria-expanded={showAreas} aria-controls="study-areas"
            onClick={() => setShowAreas(!showAreas)}><Tags />Предметные области</Button>
          <Button type="button" variant="outline" size="icon" aria-label="Обновить список" title="Обновить список"
            onClick={() => setReload((value) => value + 1)}><RefreshCw /></Button>
          <Button asChild><Link to={area ? "/upload?area=" + encodeURIComponent(area) : "/upload"} state={{ returnTo }}>
            <Plus />Загрузить PDF
          </Link></Button>
        </div>
      </header>
      {showAreas && <StudyAreasPanel id="study-areas" areas={areas} onAreaSaved={onAreaSaved} />}
      <div className="flex flex-wrap items-center gap-2" role="group" aria-label="Вид архива">
        <Button type="button" variant={timeline ? "outline" : "secondary"} aria-pressed={!timeline}
          onClick={() => setFilter("view", "")}><List />Список</Button>
        <Button type="button" variant={timeline ? "secondary" : "outline"} aria-pressed={timeline}
          onClick={() => setFilter("view", "timeline")}><CalendarDays />Таймлайн</Button>
      </div>
      <div className="flex flex-wrap gap-3 rounded-xl border bg-card p-3 sm:p-4">
        <div className="relative min-w-0 basis-full lg:flex-1">
          <Search className="pointer-events-none absolute top-2.5 left-3 size-4 text-muted-foreground" />
          <Input type="search" aria-label="Поиск в архиве" placeholder="Поиск по названию и тексту PDF"
            className="pl-9" value={query} maxLength={120} onChange={(event) => setFilter("q", event.target.value)} />
        </div>
        <div className="flex min-w-36 flex-1 items-center gap-1 sm:min-w-44 lg:max-w-55">
          <Select value={area || "__all__"} onValueChange={(value) => setFilter("area", value === "__all__" ? "" : value)}>
            <SelectTrigger aria-label="Предметная область" className="flex-1"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="__all__">Все области</SelectItem>
              {areas.map(({ slug, name }) => <SelectItem value={slug} key={slug}>{name}</SelectItem>)}
            </SelectContent>
          </Select>
          {activeArea && <StudyAreaHint area={activeArea} />}
        </div>
        <div className="min-w-36 flex-1 sm:min-w-44 lg:max-w-52">
          <Select value={category || "__all__"} onValueChange={(value) => setFilter("category", value === "__all__" ? "" : value)}>
            <SelectTrigger aria-label="Категория документа" className="w-full"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="__all__">Все категории</SelectItem>
              {Object.entries(studyCategories).map(([value, { label }]) => (
                <SelectItem value={value || "uncategorized"} key={value}>{label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        {!timeline && <div className="min-w-36 flex-1 sm:min-w-40 lg:max-w-45">
          <Select value={sort} onValueChange={(value) => setFilter("sort", value)}>
            <SelectTrigger aria-label="Сортировка" className="w-full"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="newest">Сначала новые</SelectItem>
              <SelectItem value="oldest">Сначала старые</SelectItem>
              <SelectItem value="title">По названию</SelectItem>
            </SelectContent>
          </Select>
        </div>}
      </div>
      {!timeline && results && (results.length > 0 || hasFilters) && (
        <div className="flex flex-wrap justify-end gap-2">
          {selected.length > 0 && (
            <Button type="button" variant="outline" className="text-destructive hover:text-destructive"
              onClick={(event) => showDeletion({ ids: selected }, event.currentTarget)}>
              <Trash2 />Удалить выбранные ({selected.length})
            </Button>
          )}
          <Button type="button" variant="outline" className="text-destructive hover:text-destructive"
            onClick={(event) => showDeletion({ all: true }, event.currentTarget)}>Удалить все документы</Button>
        </div>
      )}
      {deletedCount !== null && <p role="status" className="text-sm text-muted-foreground">Удалено документов: {deletedCount}</p>}
      <DeleteStudiesDialog selection={deletion} onDismiss={() => setDeletion(null)}
        onDeleted={finishDeletion} onRestoreFocus={restoreDeleteFocus} />
      <section aria-label={timeline ? "Исследования по датам" : "Список исследований"} className="overflow-hidden rounded-xl border bg-card">
        {error ? (
          <div className="space-y-4 p-8">
            <p role="alert">{error}</p>
            <Button onClick={() => setReload((value) => value + 1)}>Повторить</Button>
          </div>
        ) : !results ? <p role="status" className="p-8">Загружаем исследования…</p> : timeline && documents?.length ? (
          <StudyTimeline documents={documents} returnTo={returnTo} />
        ) : results.length ? (
          <Table className="block md:table">
            <TableHeader className="block bg-muted/60 md:table-header-group">
              <TableRow className="block md:table-row">
                <TableHead className="block w-full px-4 md:table-cell md:w-10">
                  <label className="inline-flex h-full cursor-pointer items-center gap-3">
                    <Checkbox checked={allVisibleSelected || (selected.length > 0 ? "indeterminate" : false)}
                      aria-label="Выбрать все показанные исследования"
                      onCheckedChange={(checked) => setSelectedIds(checked ? Array.from(visibleIds) : [])} />
                    <span aria-hidden="true" className="md:sr-only">Выбрать все показанные исследования</span>
                  </label>
                </TableHead>
                <TableHead className="hidden px-5 md:table-cell">Исследование</TableHead>
                <TableHead className="hidden w-38 md:table-cell">Дата исследования</TableHead>
                <TableHead className="hidden w-1/3 md:table-cell">Предметные области</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody className="block md:table-row-group">
              {results.map((item) => (
                <TableRow key={item.id} data-state={selectedSet.has(item.id) ? "selected" : undefined}
                  className="grid grid-cols-[2.75rem_minmax(0,1fr)] py-2 md:table-row">
                  <TableCell className="row-span-3 w-10 px-4">
                    <Checkbox checked={selectedSet.has(item.id)}
                      aria-label={"Выбрать " + item.title + " · " + formatStudyDate(item.study_date)}
                      onCheckedChange={(checked) => setSelectedIds(checked
                        ? [...selected, item.id] : selected.filter((id) => id !== item.id))} />
                  </TableCell>
                  <TableCell className="min-w-0 px-2 py-2 md:px-5 md:py-4">
                    <div className="flex min-w-0 items-start gap-3">
                      <StudyCategoryIcon category={item.category} />
                      <div className="min-w-0 whitespace-normal">
                        <Link to={studyDocumentPath(item)}
                          state={{ returnTo }}
                          className="text-base font-medium break-words text-primary hover:underline">{item.title}</Link>
                        <p className="mt-0.5 text-sm break-all text-muted-foreground">{item.original_name}</p>
                        <div className="mt-1"><StudyCategoryLabel category={item.category} /></div>
                        {item.search_match && <p className="mt-1 text-sm break-words text-muted-foreground">
                          <span className="font-medium text-foreground">Страница {item.search_match.page}</span>
                          {" · "}{item.search_match.excerpt}
                        </p>}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell className="col-start-2 px-2 py-1 tabular-nums md:px-2">{formatStudyDate(item.study_date)}</TableCell>
                  <TableCell className="col-start-2 px-2 py-2 whitespace-normal md:pr-5">
                    <div className="flex flex-wrap gap-1.5">
                      {areas.filter(({ slug }) => item.areas.includes(slug)).map((studyArea) => (
                        <StudyAreaBadge key={studyArea.slug} area={studyArea} />
                      ))}
                      {!item.areas.length && <span className="text-muted-foreground">—</span>}
                    </div>
                    {item.index_status !== "ready" && <div className="mt-2">
                      <StudyIndexStatus status={item.index_status} />
                    </div>}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : (
          <div className="flex flex-col items-center px-6 py-19 text-center">
            <div className="mb-4 grid size-12 place-items-center rounded-xl bg-accent text-accent-foreground"><FolderOpen /></div>
            <h2 className="text-lg font-semibold">{hasFilters ? "Исследования не найдены" : "Архив пока пуст"}</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              {hasFilters ? "Измените запрос или фильтры." : "Загрузите PDF с анализом, обследованием или заключением."}
            </p>
            {!hasFilters && <Button asChild variant="outline" className="mt-5"><Link to="/upload">Загрузить PDF</Link></Button>}
          </div>
        )}
      </section>
    </div>
  )
}
