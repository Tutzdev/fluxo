import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter, Navigate, RouterProvider } from 'react-router'
import { RequireSession } from '@/components/app-shell'
import { AccountsPage } from '@/features/accounts/accounts-page'
import { SessionProvider } from '@/features/auth/session'
import { WelcomePage } from '@/features/auth/welcome-page'
import { BudgetsPage } from '@/features/budgets/budgets-page'
import { CategoriesPage } from '@/features/categories/categories-page'
import { ImportPage } from '@/features/imports/import-page'
import { OverviewPage } from '@/features/overview/overview-page'
import { ReviewPage } from '@/features/review/review-page'
import { TransactionsPage } from '@/features/transactions/transactions-page'
import { ApiError } from '@/lib/api'
import './index.css'

const queries = new QueryClient({
  defaultOptions: {
    queries: {
      // A 4xx will not get better by asking again; a dropped connection might.
      retry: (failures, error) => !(error instanceof ApiError && error.status < 500) && failures < 2,
    },
  },
})

const router = createBrowserRouter([
  { path: '/welcome', element: <WelcomePage /> },
  {
    element: <RequireSession />,
    children: [
      { path: '/', element: <OverviewPage /> },
      { path: '/review', element: <ReviewPage /> },
      { path: '/transactions', element: <TransactionsPage /> },
      { path: '/import', element: <ImportPage /> },
      { path: '/budgets', element: <BudgetsPage /> },
      { path: '/categories', element: <CategoriesPage /> },
      { path: '/accounts', element: <AccountsPage /> },
    ],
  },
  { path: '*', element: <Navigate to="/" replace /> },
])

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queries}>
      <SessionProvider>
        <RouterProvider router={router} />
      </SessionProvider>
    </QueryClientProvider>
  </StrictMode>,
)
