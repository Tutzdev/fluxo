import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { CategorizationSummary, Transaction, TransactionPage } from '@/lib/types'

export interface TransactionFilters {
  month?: string
  account_id?: number
  category_id?: number
  needs_review?: boolean
  search?: string
  page?: number
  page_size?: number
}

export function useTransactions(filters: TransactionFilters) {
  return useQuery({
    queryKey: ['transactions', filters],
    queryFn: () => api<TransactionPage>('/api/transactions', { query: { ...filters } }),
    placeholderData: keepPreviousData,
  })
}

export interface NewTransaction {
  account_id: number
  occurred_on: string
  description: string
  amount: string
  category_id: number | null
}

/** A category change moves totals, budgets and the review queue, so everything is refreshed. */
export function useTransactionMutations() {
  const queryClient = useQueryClient()
  const refreshEverything = () => queryClient.invalidateQueries()

  return {
    create: useMutation({
      mutationFn: (body: NewTransaction) => api<Transaction>('/api/transactions', { body }),
      onSuccess: refreshEverything,
    }),
    setCategory: useMutation({
      mutationFn: ({ transactionId, categoryId }: { transactionId: number; categoryId: number | null }) =>
        api<Transaction>(`/api/transactions/${transactionId}/category`, {
          method: 'PUT',
          body: { category_id: categoryId },
        }),
      onSuccess: refreshEverything,
    }),
    remove: useMutation({
      mutationFn: (transactionId: number) => api(`/api/transactions/${transactionId}`, { method: 'DELETE' }),
      onSuccess: refreshEverything,
    }),
    recategorize: useMutation({
      mutationFn: async () =>
        (await api<{ recategorized: CategorizationSummary }>('/api/transactions/recategorize', { method: 'POST' }))
          .recategorized,
      onSuccess: refreshEverything,
    }),
  }
}
