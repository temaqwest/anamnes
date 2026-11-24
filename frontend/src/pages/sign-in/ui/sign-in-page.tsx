import { type FormEvent, useState } from "react"
import { signIn, type Session } from "@/entities/session"
import { errorMessage } from "@/shared/api"
import { AccountCard } from "@/shared/ui/account-card"
import { Button } from "@/shared/ui/button"
import { Input } from "@/shared/ui/input"
import { Label } from "@/shared/ui/label"

export function SignInPage({ onSignIn }: { onSignIn: (session: Session) => void }) {
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [submitting, setSubmitting] = useState(false)

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (submitting) return
    setError("")
    setSubmitting(true)
    try {
      onSignIn(await signIn(username.trim(), password))
    } catch (error) {
      setError(errorMessage(error))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AccountCard title="Вход в личный архив" links={[
      { to: "/register", label: "Регистрация" },
      { to: "/forgot-password", label: "Забыли пароль?" },
      { to: "/resend-verification", label: "Не пришло письмо?" },
    ]}>
      <form className="space-y-4" onSubmit={submit}>
        <div className="space-y-2">
          <Label htmlFor="username">Электронная почта или имя пользователя</Label>
          <Input id="username" name="username" autoComplete="username" autoCapitalize="none" spellCheck={false} required value={username}
            onChange={(event) => setUsername(event.target.value)} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="password">Пароль</Label>
          <Input id="password" name="password" type="password" autoComplete="current-password" required value={password}
            onChange={(event) => setPassword(event.target.value)} />
        </div>
        {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
        <Button type="submit" className="w-full" disabled={submitting}>{submitting ? "Входим…" : "Войти"}</Button>
      </form>
    </AccountCard>
  )
}
