function fragmentParams(hash: string) {
  return new URLSearchParams(hash.startsWith("#") ? hash.slice(1) : "")
}

export function readInvite(hash: string) {
  return fragmentParams(hash).get("invite") || null
}

export function readEmailLink(hash: string) {
  const params = fragmentParams(hash)
  const uid = params.get("uid")
  const token = params.get("token")
  return uid && token ? { uid, token } : null
}
