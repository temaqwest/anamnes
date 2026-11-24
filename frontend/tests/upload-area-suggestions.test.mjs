import assert from "node:assert/strict"
import test from "node:test"
import { initializeAreaSuggestions, visibleAreaSuggestions } from "../src/pages/upload/model/area-suggestions.ts"

const archive = { slug: "archive", matched_text: "Архив", auto_select: true }
const thyroid = { slug: "thyroid", matched_text: "щитовидной железы", auto_select: true }
const cardiology = { slug: "cardiology", matched_text: "сердца", auto_select: false }
const allowed = new Set([archive.slug, thyroid.slug, cardiology.slug])

test("automatic matches extend the archive selection without duplicates", () => {
  const result = initializeAreaSuggestions([archive.slug], allowed, [
    archive, thyroid, cardiology, { ...thyroid }, { ...thyroid, slug: "unknown" },
  ])

  assert.deepEqual(result.selected, [archive.slug, thyroid.slug])
  assert.deepEqual(result.suggestions, [archive, thyroid, cardiology])
})

test("an omitted or empty suggestion list still keeps the existing selection", () => {
  for (const suggestions of [undefined, []]) {
    assert.deepEqual(initializeAreaSuggestions([archive.slug], allowed, suggestions), {
      selected: [archive.slug], suggestions: [],
    })
  }
})

test("visible reasons and actions follow the user's current checkboxes", () => {
  const suggestions = [thyroid, cardiology]
  assert.deepEqual(visibleAreaSuggestions(suggestions, [thyroid.slug]), {
    matched: [thyroid], choices: [cardiology],
  })
  assert.deepEqual(visibleAreaSuggestions(suggestions, [cardiology.slug]), {
    matched: [], choices: [],
  })
  assert.deepEqual(visibleAreaSuggestions(suggestions, []), {
    matched: [], choices: [cardiology],
  })
})
