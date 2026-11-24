import assert from "node:assert/strict"
import test from "node:test"
import { groupStudyMonths } from "../src/pages/archive/model/study-timeline.ts"

test("timeline orders populated months and groups distinct studies on the same calendar day", () => {
  const studies = [
    { id: "a", study_date: "2025-12-04" },
    { id: "b", study_date: "2024-02-29" },
    { id: "c", study_date: "2025-12-01" },
    { id: "d", study_date: "2025-12-04" },
  ]
  const months = groupStudyMonths(studies)
  assert.deepEqual(months.map((month) => month.key), ["2025-12", "2024-02"])
  assert.equal(months[1].dayCount, 29)
  assert.deepEqual(months[0].days.map(({ date, studies }) => [date, studies.map(({ id }) => id)]), [
    ["2025-12-01", ["c"]], ["2025-12-04", ["a", "d"]],
  ])
})
