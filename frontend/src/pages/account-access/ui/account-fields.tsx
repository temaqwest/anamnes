import { useId } from "react"
import { Input } from "@/shared/ui/input"
import { Label } from "@/shared/ui/label"

export function AccountEmailField() {
  const id = useId()
  return (
    <div className="space-y-2">
      <Label htmlFor={id}>Электронная почта</Label>
      <Input id={id} name="email" type="email" autoComplete="email" maxLength={254} required />
    </div>
  )
}

export function AccountPasswordField({ label }: { label: string }) {
  const id = useId()
  return (
    <div className="space-y-2">
      <Label htmlFor={id}>{label}</Label>
      <Input id={id} name="password" type="password" autoComplete="new-password" required />
    </div>
  )
}
