import type { ReactNode } from "react"
import { Link } from "react-router-dom"
import { Brand } from "./brand"
import { Button } from "./button"

export function AccountCard({ title, links, children }: {
  title: string
  links?: readonly { to: string; label: string }[]
  children: ReactNode
}) {
  return (
    <main className="grid min-h-svh place-items-center bg-[radial-gradient(ellipse_at_top_left,#3c3963,transparent_62%)] px-4 pt-[max(4.5rem,calc(env(safe-area-inset-top)+3.5rem))] pb-[max(1.5rem,env(safe-area-inset-bottom))] sm:px-6">
      <section className="w-full max-w-md rounded-2xl border bg-card p-5 shadow-sm sm:p-9">
        <Brand />
        <h1 className="mt-6 text-2xl font-semibold tracking-tight sm:mt-8">{title}</h1>
        <div className="mt-5 sm:mt-6">{children}</div>
        {links && (
          <nav aria-label="Действия с аккаунтом" className="mt-5 flex flex-wrap items-center gap-x-4 gap-y-3 border-t pt-4">
            {links.map(({ to, label }) => (
              <Button key={to} variant="link" className="h-auto px-0 py-0 whitespace-normal" asChild>
                <Link to={to}>{label}</Link>
              </Button>
            ))}
          </nav>
        )}
      </section>
    </main>
  )
}
