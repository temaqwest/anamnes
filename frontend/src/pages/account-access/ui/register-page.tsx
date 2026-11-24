import { useLocation } from "react-router-dom"
import { register } from "@/entities/session"
import { AccountCard } from "@/shared/ui/account-card"
import { readInvite } from "../model/account-link"
import { AccountActionForm } from "./account-action-form"
import { AccountEmailField, AccountPasswordField } from "./account-fields"

export function RegisterPage() {
  const { hash } = useLocation()
  const invite = readInvite(hash)

  return (
    <AccountCard title="Регистрация" links={[
      { to: "/", label: "Войти" },
      { to: "/resend-verification", label: "Повторить письмо подтверждения" },
    ]}>
      {invite ? (
        <AccountActionForm key={hash} submitLabel="Создать аккаунт" action={(fields) => register(
          String(fields.get("email") ?? "").trim(), String(fields.get("password") ?? ""), invite,
        )}>
          <AccountEmailField />
          <AccountPasswordField label="Пароль" />
        </AccountActionForm>
      ) : <p className="text-sm text-muted-foreground">Откройте ссылку из приглашения, чтобы создать аккаунт.</p>}
    </AccountCard>
  )
}
