import { useEffect, useState } from "react"
import { Link, useSearchParams } from "react-router-dom"
import { listStudies, orderStudies, type StudyDocument } from "@/entities/study"
import { errorMessage } from "@/shared/api"
import { Button } from "@/shared/ui/button"
import { findComparison } from "../model/comparison-pair"
import { ComparePanel } from "./compare-panel"

type LoadResult = { key: string; documents: StudyDocument[] } | { key: string; error: string }

export function ComparePage() {
  const [params, setParams] = useSearchParams()
  const [loaded, setLoaded] = useState<LoadResult | null>(null)
  const [reload, setReload] = useState(0)
  const area = params.get("area") ?? ""
  const category = params.get("category") ?? ""
  const query = (params.get("q") ?? "").trim()
  const order = params.get("sort") ?? "newest"
  const key = JSON.stringify([area, category, query, reload])
  const current = loaded?.key === key ? loaded : null

  useEffect(() => {
    const controller = new AbortController()
    listStudies({ area, category, query, signal: controller.signal }).then(
      (documents) => { if (!controller.signal.aborted) setLoaded({ key, documents }) },
      (error) => { if (!controller.signal.aborted) setLoaded({ key, error: errorMessage(error) }) },
    )
    return () => controller.abort()
  }, [area, category, query, key])

  const archiveParams = new URLSearchParams(params)
  archiveParams.delete("left")
  archiveParams.delete("right")
  const returnTo = archiveParams.size ? "/?" + archiveParams.toString() : "/"
  const documents = current && "documents" in current ? orderStudies(current.documents, order) : []
  const pair = findComparison(documents, params.get("left"), params.get("right"))

  function changeDocument(side: "left" | "right", id: string) {
    const updated = new URLSearchParams(params)
    updated.set(side, id)
    setParams(updated, { replace: true })
  }

  return (
    <div className="mx-auto max-w-[1800px] space-y-5">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Сравнение документов</h1>
        <Button asChild variant="outline"><Link to={returnTo}>К архиву</Link></Button>
      </header>
      {!current ? (
        <p role="status">Загружаем подборку…</p>
      ) : "error" in current ? (
        <div className="space-y-4 rounded-xl border bg-card p-5">
          <p role="alert">{current.error}</p>
          <Button onClick={() => setReload((value) => value + 1)}>Повторить</Button>
        </div>
      ) : pair ? (
        <div className="grid gap-4 md:grid-cols-2">
          <ComparePanel side="Левый документ" study={pair.left} other={pair.right} documents={documents}
            onChange={(id) => changeDocument("left", id)} />
          <ComparePanel side="Правый документ" study={pair.right} other={pair.left} documents={documents}
            onChange={(id) => changeDocument("right", id)} />
        </div>
      ) : (
        <p className="rounded-xl border bg-card p-5">Выберите в архиве два доступных исследования для сравнения.</p>
      )}
    </div>
  )
}
