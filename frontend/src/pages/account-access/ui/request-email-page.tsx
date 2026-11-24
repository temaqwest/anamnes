import { requestPasswordReset, resendVerification } from "@/entities/session"
import { AccountCard } from "@/shared/ui/account-card"
import { AccountActionForm } from "./account-action-form"
import { AccountEmailField } from "./account-fields"

const requests = {
  verification: { title: "Новое письмо подтверждения", request: resendVerification },
  reset: { title: "Восстановление пароля", request: requestPasswordReset },
}

export function RequestEmailPage({ mode }: { mode: keyof typeof requests }) {
  const { title, request } = requests[mode]

  return (
    <AccountCard title={title} links={[{ to: "/", label: "Вернуться ко входу" }]}>
      <AccountActionForm key={mode} submitLabel="Отправить письмо"
        action={(fields) => request(String(fields.get("email") ?? "").trim())}>
        <AccountEmailField />
      </AccountActionForm>
    </AccountCard>
  )
}
