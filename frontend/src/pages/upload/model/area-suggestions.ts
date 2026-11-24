import type { StudyAreaSuggestion } from "@/entities/study"

export function initializeAreaSuggestions(
  selected: readonly string[],
  allowedSlugs: ReadonlySet<string>,
  incoming: readonly StudyAreaSuggestion[] = [],
) {
  const bySlug = new Map<string, StudyAreaSuggestion>()
  for (const suggestion of incoming) {
    if (!allowedSlugs.has(suggestion.slug)) continue
    const previous = bySlug.get(suggestion.slug)
    if (!previous || (suggestion.auto_select && !previous.auto_select)) bySlug.set(suggestion.slug, suggestion)
  }
  const suggestions = [...bySlug.values()]
  const automatic = suggestions.filter(({ auto_select }) => auto_select).map(({ slug }) => slug)
  return { selected: [...new Set([...selected, ...automatic])], suggestions }
}

export function visibleAreaSuggestions(suggestions: readonly StudyAreaSuggestion[], selected: readonly string[]) {
  return {
    matched: suggestions.filter(({ slug, auto_select }) => auto_select && selected.includes(slug)),
    choices: suggestions.filter(({ slug, auto_select }) => !auto_select && !selected.includes(slug)),
  }
}
