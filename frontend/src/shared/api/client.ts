const accessDeniedEvent = "anamnes:session-check"

class ApiError extends Error {
  constructor(message: string) {
    super(message)
  }
}

function csrfToken() {
  return document.cookie.split("; ").find((item) => item.startsWith("csrftoken="))?.slice(10) ?? ""
}

function describeError(value: unknown, fieldLabels: Readonly<Record<string, string>>): string {
  if (typeof value === "string") return value
  if (Array.isArray(value)) return value.map((entry) => describeError(entry, fieldLabels)).filter(Boolean).join(" ")
  if (value && typeof value === "object") {
    return Object.entries(value).map(([key, entry]) => {
      const description = describeError(entry, fieldLabels)
      return Object.hasOwn(fieldLabels, key) && description ? fieldLabels[key] + ": " + description : description
    }).filter(Boolean).join(" ")
  }
  return ""
}

export async function api<T>(path: string, init?: RequestInit, fieldLabels: Readonly<Record<string, string>> = {}): Promise<T> {
  const headers = new Headers(init?.headers)
  if (init?.method && init.method !== "GET") {
    headers.set("X-CSRFToken", csrfToken())
    if (typeof init.body === "string") headers.set("Content-Type", "application/json")
  }
  const response = await fetch("/api" + path, { ...init, headers, cache: "no-store" })
  const body: unknown = await response.json().catch(() => null)
  if (!response.ok) {
    if (response.status === 403) window.dispatchEvent(new Event(accessDeniedEvent))
    throw new ApiError(describeError(body, fieldLabels) || "Запрос не удалось выполнить.")
  }
  return body as T
}

export function errorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : "Проверьте подключение и попробуйте ещё раз."
}

export function onAccessDenied(listener: () => void): () => void {
  window.addEventListener(accessDeniedEvent, listener)
  return () => window.removeEventListener(accessDeniedEvent, listener)
}
