import assert from "node:assert/strict"
import test from "node:test"
import { readEmailLink, readInvite } from "./account-link.ts"

test("registration reads its invitation from the fragment", () => {
  assert.equal(readInvite("#invite=example%2Binvite"), "example+invite")
  assert.equal(readInvite("#token=other"), null)
  assert.equal(readInvite("#invite="), null)
  assert.equal(readInvite("?invite=example"), null)
})

test("verification and reset require both credentials", () => {
  assert.deepEqual(readEmailLink("#uid=Mw&token=example%2Btoken"), { uid: "Mw", token: "example+token" })
  assert.equal(readEmailLink("#uid=Mw"), null)
  assert.equal(readEmailLink("#token=example"), null)
  assert.equal(readEmailLink(""), null)
  assert.equal(readEmailLink("?uid=Mw&token=example"), null)
})
