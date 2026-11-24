import { api } from "@/shared/api"

export type Session = { username: string | null }

export function getSession() {
  return api<Session>("/auth/session/")
}

export function signIn(username: string, password: string) {
  return api<Session>("/auth/login/", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  })
}

export function signOut() {
  return api<Session>("/auth/logout/", { method: "POST" })
}
