import { FolderHeart } from "lucide-react"

export function Brand() {
  return (
    <div className="flex items-center gap-3">
      <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-primary text-primary-foreground">
        <FolderHeart size={22} aria-hidden="true" />
      </span>
      <span className="text-xl font-semibold tracking-tight">Anamnes</span>
    </div>
  )
}
