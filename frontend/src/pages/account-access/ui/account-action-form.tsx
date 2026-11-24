import { type FormEvent, type ReactNode, useRef, useState } from "react"
import type { AccountNotice } from "@/entities/session"
import { errorMessage } from "@/shared/api"
import { Button } from "@/shared/ui/button"

export function AccountActionForm({ submitLabel, action, children }: {
  submitLabel: string
  action: (fields: FormData) => Promise<AccountNotice>
  children?: ReactNode
}) {
  const [pending, setPending] = useState(false)
  const [error, setError] = useState("")
  const [result, setResult] = useState<AccountNotice | null>(null)
  const submitting = useRef(false)

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (submitting.current) return
    const fields = new FormData(event.currentTarget)
    submitting.current = true
    setPending(true)
    setError("")
    try {
      setResult(await action(fields))
    } catch (error) {
      setError(errorMessage(error))
    } finally {
      setPending(false)
      submitting.current = false
    }
  }

  return (
    <>
      {!result && (
        <form className="space-y-4" onSubmit={submit}>
          {children && <fieldset className="min-w-0 space-y-4" disabled={pending}>{children}</fieldset>}
          {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
          <Button type="submit" className="w-full" disabled={pending}>{pending ? "Отправляем…" : submitLabel}</Button>
        </form>
      )}
      <div role="status">
        {result && <p className="rounded-lg border bg-muted px-4 py-3 text-sm">{result.detail}</p>}
      </div>
    </>
  )
}
