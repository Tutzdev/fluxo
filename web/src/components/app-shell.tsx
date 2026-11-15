import { useQuery } from '@tanstack/react-query'
import {
  ArrowDownUp,
  Inbox,
  LayoutDashboard,
  LogOut,
  Menu,
  PiggyBank,
  Tags,
  Upload,
  Wallet,
  X,
} from 'lucide-react'
import { type ComponentType, useState } from 'react'
import { Navigate, NavLink, Outlet, useLocation } from 'react-router'
import { useSession } from '@/features/auth/session'
import { api } from '@/lib/api'
import type { TransactionPage } from '@/lib/types'

interface NavItem {
  to: string
  label: string
  icon: ComponentType<{ className?: string; 'aria-hidden'?: boolean }>
}

const NAV_ITEMS: NavItem[] = [
  { to: '/', label: 'Overview', icon: LayoutDashboard },
  { to: '/review', label: 'Review', icon: Inbox },
  { to: '/transactions', label: 'Transactions', icon: ArrowDownUp },
  { to: '/import', label: 'Import', icon: Upload },
  { to: '/budgets', label: 'Budgets', icon: PiggyBank },
  { to: '/categories', label: 'Categories & rules', icon: Tags },
  { to: '/accounts', label: 'Accounts', icon: Wallet },
]

/** How many transactions wait for the person; shown next to "Review" on every page. */
function useReviewCount(): number {
  const { data } = useQuery({
    queryKey: ['transactions', { needs_review: true, page_size: 1 }],
    queryFn: () => api<TransactionPage>('/api/transactions', { query: { needs_review: true, page_size: 1 } }),
  })
  return data?.total ?? 0
}

export function Logo() {
  return (
    <span className="flex items-center gap-2 font-display text-xl font-bold tracking-tight">
      <img src="/favicon.svg" alt="" className="size-7" />
      Centavo
    </span>
  )
}

function Navigation({ onNavigate }: { onNavigate?: () => void }) {
  const reviewCount = useReviewCount()

  return (
    <nav aria-label="Main">
      <ul className="flex flex-col gap-0.5">
        {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
          <li key={to}>
            <NavLink
              to={to}
              end={to === '/'}
              onClick={onNavigate}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-semibold transition-colors ${
                  isActive ? 'bg-ink text-paper' : 'text-ink-soft hover:bg-surface hover:text-ink'
                }`
              }
            >
              <Icon aria-hidden className="size-4.5 shrink-0" />
              <span className="flex-1">{label}</span>
              {to === '/review' && reviewCount > 0 && (
                <span className="figures rounded-full bg-brass px-2 text-xs font-bold text-ink">
                  {reviewCount}
                  <span className="sr-only"> waiting</span>
                </span>
              )}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  )
}

function Account() {
  const { user, signOut } = useSession()

  return (
    <div className="border-t border-line pt-4">
      <p className="truncate text-sm font-semibold">{user?.name}</p>
      <p className="truncate text-xs text-ink-soft">{user?.email}</p>
      <button
        type="button"
        onClick={signOut}
        className="mt-3 flex items-center gap-2 text-sm font-semibold text-ink-soft hover:text-ink"
      >
        <LogOut aria-hidden className="size-4" />
        Sign out
      </button>
    </div>
  )
}

export function AppShell() {
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <div className="min-h-dvh lg:grid lg:grid-cols-[16rem_1fr]">
      <aside className="sticky top-0 hidden h-dvh flex-col justify-between gap-8 border-r border-line px-4 py-6 lg:flex">
        <div className="flex flex-col gap-8">
          <div className="px-3">
            <Logo />
          </div>
          <Navigation />
        </div>
        <Account />
      </aside>

      <header className="sticky top-0 z-30 flex items-center justify-between border-b border-line bg-paper/95 px-4 py-3 backdrop-blur lg:hidden">
        <Logo />
        <button
          type="button"
          onClick={() => setMenuOpen(true)}
          className="rounded-lg p-2 ring-1 ring-line"
          aria-label="Open menu"
          aria-expanded={menuOpen}
        >
          <Menu aria-hidden className="size-5" />
        </button>
      </header>

      {menuOpen && (
        <div className="fixed inset-0 z-40 lg:hidden" role="dialog" aria-modal="true" aria-label="Menu">
          <button type="button" className="absolute inset-0 bg-ink/40" aria-label="Close menu" onClick={() => setMenuOpen(false)} />
          <div className="absolute inset-y-0 right-0 flex w-72 max-w-[85vw] flex-col justify-between bg-paper px-4 py-5">
            <div className="flex flex-col gap-6">
              <div className="flex items-center justify-between px-3">
                <Logo />
                <button type="button" onClick={() => setMenuOpen(false)} aria-label="Close menu" className="p-1">
                  <X aria-hidden className="size-5" />
                </button>
              </div>
              <Navigation onNavigate={() => setMenuOpen(false)} />
            </div>
            <Account />
          </div>
        </div>
      )}

      <main className="mx-auto w-full max-w-6xl px-4 py-8 sm:px-8 lg:py-12">
        <Outlet />
      </main>
    </div>
  )
}

export function RequireSession() {
  const { user } = useSession()
  const location = useLocation()

  if (!user) {
    return <Navigate to="/welcome" replace state={{ from: location.pathname }} />
  }
  return <AppShell />
}
