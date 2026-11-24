import { FolderOpen, LogOut, Pill, Plus, ShieldAlert } from "lucide-react"
import { type ReactNode, useCallback, useEffect, useState } from "react"
import { Link, Navigate, NavLink, Outlet, Route, Routes } from "react-router-dom"
import { getSession, signOut, type Session } from "@/entities/session"
import { listStudyAreas, type Area } from "@/entities/study"
import { ConfirmEmailPage, RegisterPage, RequestEmailPage, ResetPasswordPage } from "@/pages/account-access"
import { AllergiesPage } from "@/pages/allergies"
import { ArchivePage } from "@/pages/archive"
import { ComparePage } from "@/pages/compare"
import { DocumentPage } from "@/pages/document"
import { MedicationsPage } from "@/pages/medications"
import { SignInPage } from "@/pages/sign-in"
import { UploadPage } from "@/pages/upload"
import { errorMessage, onAccessDenied } from "@/shared/api"
import { Brand } from "@/shared/ui/brand"
import { Button } from "@/shared/ui/button"
import { ThemeSelect } from "./theme-select"

const byAreaName = new Intl.Collator("ru")
const compareAreas = (a: Area, b: Area) => byAreaName.compare(a.name, b.name)

export function App() {
  const [session, setSession] = useState<Session | null>(null)
  const [error, setError] = useState("")

  const refreshSession = useCallback(async () => {
    try {
      setSession(await getSession())
      setError("")
    } catch (error) {
      setError(errorMessage(error))
    }
  }, [])

  useEffect(() => {
    void refreshSession()
    return onAccessDenied(refreshSession)
  }, [refreshSession])

  if (!session) {
    return (
      <main className="grid min-h-svh place-items-center">
        {error ? (
          <div className="space-y-4 text-center">
            <p role="alert">{error}</p>
            <Button onClick={refreshSession}>Повторить</Button>
          </div>
        ) : <p role="status">Открываем Anamnes…</p>}
      </main>
    )
  }

  return (
    <Routes>
      <Route element={<PublicAccess />}>
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/confirm-email" element={<ConfirmEmailPage />} />
        <Route path="/resend-verification" element={<RequestEmailPage mode="verification" />} />
        <Route path="/forgot-password" element={<RequestEmailPage mode="reset" />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />
      </Route>
      <Route path="*" element={session.username
        ? <Workspace username={session.username} onSignOut={setSession} />
        : <PublicAccess><SignInPage onSignIn={setSession} /></PublicAccess>} />
    </Routes>
  )
}

function PublicAccess({ children }: { children?: ReactNode }) {
  return (
    <>
      <div className="absolute top-[max(1rem,env(safe-area-inset-top))] right-4"><ThemeSelect /></div>
      {children ?? <Outlet />}
    </>
  )
}

function Workspace({ username, onSignOut }: { username: string; onSignOut: (session: Session) => void }) {
  const [areas, setAreas] = useState<Area[] | null>(null)
  const [areasError, setAreasError] = useState("")
  const [logoutError, setLogoutError] = useState("")

  const loadAreas = useCallback(async () => {
    setAreasError("")
    try {
      setAreas((await listStudyAreas()).sort(compareAreas))
    } catch (error) {
      setAreasError(errorMessage(error))
    }
  }, [])
  useEffect(() => { void loadAreas() }, [loadAreas])

  function handleAreaSaved(area: Area) {
    setAreas((current) => [...(current ?? []).filter(({ slug }) => slug !== area.slug), area].sort(compareAreas))
  }

  async function handleSignOut() {
    setLogoutError("")
    try {
      onSignOut(await signOut())
    } catch (error) {
      setLogoutError(errorMessage(error))
    }
  }

  const navClass = ({ isActive }: { isActive: boolean }) =>
    "flex flex-col items-center justify-center gap-1 rounded-lg px-1 py-2 text-xs font-medium sm:flex-row sm:gap-2 sm:text-sm lg:justify-start lg:gap-3 lg:px-3 lg:py-2.5 " +
    (isActive ? "bg-accent text-accent-foreground" : "text-muted-foreground hover:bg-muted")

  const areaStatus = areasError ? (
    <div className="space-y-4">
      <p role="alert">{areasError}</p>
      <Button onClick={loadAreas}>Повторить</Button>
    </div>
  ) : <p role="status">Загружаем архив…</p>

  return (
    <div className="min-h-svh pb-[env(safe-area-inset-bottom)]">
      <aside className="sticky top-0 z-20 flex flex-wrap items-center gap-x-3 gap-y-2 border-b bg-card px-4 pt-[max(0.75rem,env(safe-area-inset-top))] pb-3 lg:fixed lg:inset-y-0 lg:left-0 lg:w-57 lg:flex-nowrap lg:flex-col lg:items-stretch lg:border-r lg:border-b-0 lg:py-6">
        <Link to="/" className="order-1 w-fit lg:mx-2"><Brand /></Link>
        <nav aria-label="Основная навигация" className="order-3 grid w-full grid-cols-4 gap-1 lg:order-2 lg:mt-10 lg:block lg:space-y-1">
          <NavLink to="/" end className={navClass}><FolderOpen size={18} />Архив</NavLink>
          <NavLink to="/upload" className={navClass}><Plus size={18} /><span>Загрузка<span className="max-[380px]:sr-only"> PDF</span></span></NavLink>
          <NavLink to="/medications" className={navClass}><Pill size={18} />Лекарства</NavLink>
          <NavLink to="/allergies" className={navClass}><ShieldAlert size={18} aria-hidden="true" />Аллергии</NavLink>
        </nav>
        <div className="order-2 ml-auto lg:order-3 lg:mt-auto lg:ml-0 lg:space-y-2 lg:border-t lg:pt-4">
          <p className="hidden truncate px-2 text-sm font-medium lg:block" title={username}>{username}</p>
          <div className="flex items-center gap-1 lg:grid lg:gap-2">
            <ThemeSelect className="max-lg:[&_[data-slot=select-value]]:sr-only lg:w-full" />
            <Button type="button" variant="ghost" className="text-muted-foreground lg:w-full lg:justify-start" onClick={handleSignOut}>
              <LogOut />Выйти
            </Button>
          </div>
          {logoutError && <p role="alert" className="text-sm text-destructive">{logoutError}</p>}
        </div>
      </aside>
      <main className="min-w-0 px-3 py-4 sm:px-6 sm:py-6 lg:ml-57 lg:px-9 lg:py-9">
          <Routes>
            <Route path="/" element={areas ? <ArchivePage areas={areas} onAreaSaved={handleAreaSaved} /> : areaStatus} />
            <Route path="/upload" element={areas ? <UploadPage areas={areas} onAreaSaved={handleAreaSaved} /> : areaStatus} />
            <Route path="/compare" element={<ComparePage />} />
            <Route path="/documents/:id" element={areas ? <DocumentPage areas={areas} /> : areaStatus} />
            <Route path="/medications" element={<MedicationsPage />} />
            <Route path="/allergies" element={<AllergiesPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
      </main>
    </div>
  )
}
