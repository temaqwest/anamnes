import { Info } from "lucide-react"
import { Tooltip } from "radix-ui"
import { useState } from "react"
import { Badge } from "@/shared/ui/badge"
import { Button } from "@/shared/ui/button"
import type { Area } from "../model/types"

export function StudyAreaHint({ area }: { area: Area }) {
  const [open, setOpen] = useState(false)
  if (!area.description) return null

  return (
    <Tooltip.Root open={open} onOpenChange={setOpen}>
      <Tooltip.Trigger asChild>
        <Button type="button" variant="ghost" size="icon-xs" className="shrink-0 focus-visible:ring-inset"
          aria-label={`Подсказка к области «${area.name}»`}
          onClick={(event) => { event.preventDefault(); setOpen(true) }}>
          <Info />
        </Button>
      </Tooltip.Trigger>
      <Tooltip.Portal>
        <Tooltip.Content sideOffset={5} collisionPadding={8}
          className="z-50 w-max max-w-[min(20rem,calc(100vw_-_2rem))] rounded-md border bg-popover px-3 py-2 text-sm text-popover-foreground wrap-anywhere whitespace-pre-wrap shadow-md">
          {area.description}
        </Tooltip.Content>
      </Tooltip.Portal>
    </Tooltip.Root>
  )
}

export function StudyAreaBadge({ area }: { area: Area }) {
  return (
    <Badge variant="secondary" className="max-w-full whitespace-normal">
      <span className="min-w-0 wrap-anywhere">{area.name}</span>
      <StudyAreaHint area={area} />
    </Badge>
  )
}
