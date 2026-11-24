import { useLocation } from "react-router-dom"
import { resetPassword } from "@/entities/session"
import { AccountCard } from "@/shared/ui/account-card"
import { readEmailLink } from "../model/account-link"
import { AccountActionForm } from "./account-action-form"
import { AccountPasswordField } from "./account-fields"

export function ResetPasswordPage() {
  const { hash } = useLocation()
  const link = readEmailLink(hash)

  return (
    <AccountCard title="Новый пароль" links={[
      { to: "/", label: "Войти" },
      { to: "/forgot-password", label: "Запросить новую ссылку" },
    ]}>
      {link ? (
        <AccountActionForm key={hash} submitLabel="Сохранить пароль"
          action={(fields) => resetPassword(link, String(fields.get("password") ?? ""))}>
          <AccountPasswordField label="Новый пароль" />
        </AccountActionForm>
      ) : <p role="alert" className="text-sm text-muted-foreground">Ссылка неполная. Откройте ссылку из письма или запросите новую.</p>}
    </AccountCard>
  )
}
