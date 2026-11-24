import { SunMoon } from "lucide-react"
import { useState } from "react"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/ui/select"

type Theme = "system" | "light" | "dark"

function readTheme(): Theme {
  const theme = document.documentElement.dataset.theme
  return theme === "light" || theme === "dark" ? theme : "system"
}

export function ThemeSelect({ className }: { className?: string }) {
  const [theme, setTheme] = useState(readTheme)

  function changeTheme(value: string) {
    if (value !== "light" && value !== "dark" && value !== "system") return
    setTheme(value)
    if (value === "system") delete document.documentElement.dataset.theme
    else document.documentElement.dataset.theme = value

    try {
      if (value === "system") localStorage.removeItem("anamnes.theme")
      else localStorage.setItem("anamnes.theme", value)
    } catch {
      // The current page can still switch themes when browser storage is unavailable.
    }
  }

  return (
    <Select value={theme} onValueChange={changeTheme}>
      <SelectTrigger aria-label="Тема оформления" title="Тема оформления" className={className}>
        <SunMoon aria-hidden="true" />
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="system">Как в системе</SelectItem>
        <SelectItem value="light">Светлая</SelectItem>
        <SelectItem value="dark">Тёмная</SelectItem>
      </SelectContent>
    </Select>
  )
}
