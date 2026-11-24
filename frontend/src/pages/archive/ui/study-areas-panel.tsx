import { Pencil, Plus } from "lucide-react"
import { StudyAreaHint, type Area } from "@/entities/study"
import { StudyAreaDialog } from "@/features/edit-study-area"
import { Button } from "@/shared/ui/button"

export function StudyAreasPanel({ areas, onAreaSaved, id }: {
  areas: Area[]
  onAreaSaved: (area: Area) => void
  id: string
}) {
  return (
    <section id={id} aria-labelledby={id + "-title"} className="space-y-3 rounded-xl border bg-card p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 id={id + "-title"} className="font-semibold">Предметные области</h2>
        <StudyAreaDialog onSaved={onAreaSaved}
          trigger={<Button type="button" size="sm"><Plus />Добавить область</Button>} />
      </div>
      <ul className="grid gap-2 sm:grid-cols-2">
        {areas.map((area) => (
          <li key={area.slug} className="flex items-center justify-between gap-3 rounded-md border px-3 py-1">
            <div className="flex min-w-0 items-center gap-1">
              <span className="text-sm wrap-anywhere">{area.name}</span>
              <StudyAreaHint area={area} />
            </div>
            <StudyAreaDialog area={area} onSaved={onAreaSaved}
              trigger={<Button type="button" size="icon" variant="ghost" className="shrink-0"
                aria-label={"Редактировать " + area.name} title="Редактировать"><Pencil /></Button>} />
          </li>
        ))}
      </ul>
    </section>
  )
}
