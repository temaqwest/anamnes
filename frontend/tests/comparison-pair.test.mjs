import assert from "node:assert/strict"
import test from "node:test"
import { findComparison, paneNavigation } from "../src/pages/compare/model/comparison-pair.ts"

const studies = [{ id: "a" }, { id: "b" }, { id: "c" }, { id: "d" }]

test("a comparison link resolves two distinct studies in the current collection", () => {
  assert.deepEqual(findComparison(studies, "b", "a"), { left: studies[1], right: studies[0] })
  assert.equal(findComparison(studies, "a", "a"), null)
  assert.equal(findComparison(studies, "a", "removed"), null)
})

test("pane navigation skips the other PDF and keeps the archive order", () => {
  const navigation = paneNavigation(studies, "b", "c")
  assert.deepEqual(navigation.options.map(({ id }) => id), ["a", "b", "d"])
  assert.equal(navigation.previous?.id, "a")
  assert.equal(navigation.next?.id, "d")
  assert.equal(paneNavigation(studies, "d", "c").next, undefined)
})
