import { Input } from "@/shared/ui/input"
import { Label } from "@/shared/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/ui/select"
import type { Area, StudyCategory, StudyFields } from "../model/types"
import { StudyAreaHint } from "./study-area-hint"
import { studyCategories, StudyCategoryIcon } from "./study-category"

export function StudyFileFields({ id, value, onChange, disabled }: {
  id: string
  value: StudyFields
  onChange: (value: StudyFields) => void
  disabled?: boolean
}) {
  return (
    <div className="grid gap-4 sm:grid-cols-[175px_minmax(0,1fr)]">
      <div className="min-w-0 space-y-2">
        <Label htmlFor={id + "-date"}>Дата исследования</Label>
        <Input id={id + "-date"} type="date" min="0001-01-01" max="9999-12-31"
          value={value.study_date} disabled={disabled} required
          onChange={(event) => onChange({ ...value, study_date: event.target.value })} />
      </div>
      <div className="space-y-2">
        <Label htmlFor={id + "-title"}>Название процедуры</Label>
        <Input id={id + "-title"} placeholder="Например, УЗИ щитовидной железы"
          value={value.title} disabled={disabled} required maxLength={255}
          onChange={(event) => onChange({ ...value, title: event.target.value })} />
      </div>
      <div className="space-y-2">
        <Label htmlFor={id + "-category"}>Категория</Label>
        <div className="flex gap-2">
          <StudyCategoryIcon category={value.category} />
          <Select value={value.category || "uncategorized"} disabled={disabled}
            onValueChange={(category) => onChange({ ...value, category: category === "uncategorized" ? "" : category as StudyCategory })}>
            <SelectTrigger id={id + "-category"} className="flex-1"><SelectValue /></SelectTrigger>
            <SelectContent>
              {Object.entries(studyCategories).map(([category, { label }]) => (
                <SelectItem value={category || "uncategorized"} key={category}>{label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>
    </div>
  )
}

export function StudyAreas({ areas, selected, onChange, disabled }: {
  areas: Area[]
  selected: string[]
  onChange: (areas: string[]) => void
  disabled?: boolean
}) {
  return (
    <fieldset className="space-y-2" disabled={disabled}>
      <legend className="mb-2 text-sm font-medium">Предметные области</legend>
      <div className="flex flex-wrap gap-2">
        {areas.map((area) => (
          <div key={area.slug} className="flex max-w-full items-center rounded-md border bg-card text-sm has-checked:border-primary/40 has-checked:bg-accent has-checked:text-accent-foreground">
            <label className="flex min-w-0 items-center gap-2 px-2.5 py-1.5">
              <input type="checkbox" checked={selected.includes(area.slug)} className="size-3.5 shrink-0 accent-primary"
                onChange={({ target }) => onChange(target.checked ? [...selected, area.slug] : selected.filter((slug) => slug !== area.slug))} />
              <span className="wrap-anywhere">{area.name}</span>
            </label>
            <StudyAreaHint area={area} />
          </div>
        ))}
      </div>
    </fieldset>
  )
}
