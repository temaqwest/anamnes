import { ChevronLeft, ChevronRight } from "lucide-react"
import { useEffect, useRef, useState } from "react"
import type { PDFDocumentProxy, RenderTask } from "pdfjs-dist"
import workerUrl from "pdfjs-dist/build/pdf.worker.min.mjs?url"
import { Button } from "./button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./select"
import { cn } from "../lib/cn"

export function PdfPage({ url, initialPage, panel = false }: { url: string; initialPage: number; panel?: boolean }) {
  const [pdf, setPdf] = useState<PDFDocumentProxy | null>(null)
  const [page, setPage] = useState(initialPage)
  const [error, setError] = useState("")
  const [zoom, setZoom] = useState("fit")
  const canvas = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    let stopped = false
    let destroy: (() => Promise<void>) | undefined
    async function load() {
      const { GlobalWorkerOptions, getDocument } = await import("pdfjs-dist")
      if (stopped) return
      GlobalWorkerOptions.workerSrc = workerUrl
      const task = getDocument({ url })
      destroy = () => task.destroy()
      const document = await task.promise
      if (!stopped) {
        setPage(Math.min(Math.max(initialPage, 1), document.numPages))
        setPdf(document)
      }
    }
    load().catch(() => { if (!stopped) setError("Не удалось открыть PDF. Попробуйте открыть оригинал.") })
    return () => {
      stopped = true
      void destroy?.().catch(() => {})
    }
  }, [url, initialPage])

  useEffect(() => {
    const element = canvas.current
    if (!pdf || !element) return
    let stopped = false
    let render: RenderTask | undefined
    async function draw(document: PDFDocumentProxy, target: HTMLCanvasElement) {
      const source = await document.getPage(page)
      if (stopped) return
      const scale = zoom === "fit" ? 1.45 : Number(zoom) / 100
      const viewport = source.getViewport({ scale: Math.max(1.45, scale) })
      const outputScale = Math.min(window.devicePixelRatio || 1, 2)
      target.width = Math.floor(viewport.width * outputScale)
      target.height = Math.floor(viewport.height * outputScale)
      target.style.width = source.getViewport({ scale }).width + "px"
      render = source.render({
        canvas: target,
        viewport,
        transform: [outputScale, 0, 0, outputScale, 0, 0],
      })
      await render.promise
    }
    setError("")
    draw(pdf, element).catch(() => { if (!stopped) setError("Не удалось отобразить страницу.") })
    return () => { stopped = true; render?.cancel() }
  }, [pdf, page, zoom])

  return (
    <section aria-label="Просмотр PDF"
      className={cn("min-w-0 overflow-hidden rounded-xl border bg-card", panel && "flex min-h-0 flex-1 flex-col")}>
      <div className="flex shrink-0 flex-wrap items-center justify-center gap-3 border-b px-3 py-2">
        <Button type="button" variant="outline" size="icon" aria-label="Предыдущая страница" disabled={!pdf || page <= 1}
          onClick={() => setPage(page - 1)}><ChevronLeft /></Button>
        <span className="min-w-24 text-center text-sm tabular-nums" aria-live="polite">
          {pdf ? "Страница " + page + " из " + pdf.numPages : "PDF"}
        </span>
        <Button type="button" variant="outline" size="icon" aria-label="Следующая страница" disabled={!pdf || page >= pdf.numPages}
          onClick={() => setPage(page + 1)}><ChevronRight /></Button>
        {panel && (
          <Select value={zoom} disabled={!pdf} onValueChange={setZoom}>
            <SelectTrigger aria-label="Масштаб PDF"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="fit">По ширине</SelectItem>
              <SelectItem value="100">100%</SelectItem>
              <SelectItem value="125">125%</SelectItem>
              <SelectItem value="150">150%</SelectItem>
            </SelectContent>
          </Select>
        )}
      </div>
      <div role={panel ? "region" : undefined} aria-label={panel ? "Область прокрутки PDF" : undefined}
        tabIndex={panel ? 0 : undefined}
        className={cn("overflow-auto bg-[#e8eaf2] p-5", panel ? "min-h-0 flex-1" : "min-h-80")}>
        {error && <p role="alert" className="rounded-md bg-card p-4 text-sm text-destructive">{error}</p>}
        {!pdf && !error && <p role="status" className="text-center text-sm text-muted-foreground">Открываем PDF…</p>}
        <canvas ref={canvas} hidden={!pdf || !!error} aria-label={"Страница " + page}
          className={cn("mx-auto bg-white shadow-sm", zoom === "fit" && "max-w-full")} />
      </div>
    </section>
  )
}
