import { api } from "@/shared/api"

export type AccountNotice = { detail: string }
type EmailLink = { uid: string; token: string }

const fieldLabels = { email: "Электронная почта", password: "Пароль", invite: "Приглашение" }

function submitAccountAction(path: string, fields: Record<string, string>) {
  return api<AccountNotice>(`/auth/${path}/`, {
    method: "POST",
    body: JSON.stringify(fields),
  }, fieldLabels)
}

export function register(email: string, password: string, invite: string) {
  return submitAccountAction("register", { email, password, invite })
}

export function verifyEmail(link: EmailLink) {
  return submitAccountAction("verify-email", link)
}

export function resendVerification(email: string) {
  return submitAccountAction("resend-verification", { email })
}

export function requestPasswordReset(email: string) {
  return submitAccountAction("password-reset", { email })
}

export function resetPassword(link: EmailLink, password: string) {
  return submitAccountAction("password-reset/confirm", { ...link, password })
}
