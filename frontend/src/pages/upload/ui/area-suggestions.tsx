import { Plus } from "lucide-react"
import type { Area, StudyAreaSuggestion } from "@/entities/study"
import { Button } from "@/shared/ui/button"
import { visibleAreaSuggestions } from "../model/area-suggestions"

export function AreaSuggestions({ areas, suggestions, selected, disabled, onSelect }: {
  areas: Area[]
  suggestions: StudyAreaSuggestion[]
  selected: string[]
  disabled: boolean
  onSelect: (slug: string) => void
}) {
  if (!suggestions.length) return null
  const names = new Map(areas.map(({ slug, name }) => [slug, name]))
  const { matched, choices } = visibleAreaSuggestions(suggestions.filter(({ slug }) => names.has(slug)), selected)
  if (!matched.length && !choices.length) return null

  return (
    <div className="space-y-3 rounded-lg bg-muted/45 px-3 py-2.5 text-sm">
      {matched.length > 0 && (
        <div className="space-y-1">
          <p className="font-medium">Совпадения в имени файла</p>
          <ul className="space-y-0.5 text-muted-foreground">
            {matched.map(({ slug, matched_text }) => (
              <li key={slug} className="wrap-anywhere">{names.get(slug)} — «{matched_text}»</li>
            ))}
          </ul>
        </div>
      )}
      {choices.length > 0 && (
        <div className="space-y-2">
          <p className="font-medium">Предложенные области</p>
          <ul className="flex flex-wrap gap-2">
            {choices.map(({ slug, matched_text }) => (
              <li key={slug} className="max-w-full">
                <Button type="button" variant="outline" size="sm" disabled={disabled}
                  className="h-auto max-w-full py-1.5 text-left whitespace-normal" onClick={() => onSelect(slug)}>
                  <Plus /><span className="min-w-0 wrap-anywhere">{names.get(slug)} <span className="font-normal text-muted-foreground">· «{matched_text}»</span></span>
                </Button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
