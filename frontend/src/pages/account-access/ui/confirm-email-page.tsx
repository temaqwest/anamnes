import { useLocation } from "react-router-dom"
import { verifyEmail } from "@/entities/session"
import { AccountCard } from "@/shared/ui/account-card"
import { readEmailLink } from "../model/account-link"
import { AccountActionForm } from "./account-action-form"

export function ConfirmEmailPage() {
  const { hash } = useLocation()
  const link = readEmailLink(hash)

  return (
    <AccountCard title="Подтверждение почты" links={[
      { to: "/", label: "Войти" },
      { to: "/resend-verification", label: "Запросить новое письмо" },
    ]}>
      {link ? (
        <AccountActionForm key={hash} submitLabel="Подтвердить почту" action={() => verifyEmail(link)} />
      ) : <p role="alert" className="text-sm text-muted-foreground">Ссылка неполная. Откройте ссылку из письма или запросите новую.</p>}
    </AccountCard>
  )
}
