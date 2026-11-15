import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { Account, AccountKind, Money } from '@/lib/types'

export const accountKeys = { all: ['accounts'] as const }

export const ACCOUNT_KIND_LABELS: Record<AccountKind, string> = {
  checking: 'Checking',
  savings: 'Savings',
  credit_card: 'Credit card',
  cash: 'Cash',
}

export function useAccounts() {
  return useQuery({
    queryKey: accountKeys.all,
    queryFn: () => api<{ items: Account[]; total_balance: Money }>('/api/accounts'),
  })
}

export function useAccountMutations() {
  const queryClient = useQueryClient()
  const refreshEverything = () => queryClient.invalidateQueries()

  return {
    create: useMutation({
      mutationFn: (body: { name: string; kind: AccountKind; opening_balance: string }) =>
        api<Account>('/api/accounts', { body }),
      onSuccess: refreshEverything,
    }),
    rename: useMutation({
      mutationFn: ({ accountId, name }: { accountId: number; name: string }) =>
        api<Account>(`/api/accounts/${accountId}`, { method: 'PATCH', body: { name } }),
      onSuccess: refreshEverything,
    }),
    remove: useMutation({
      mutationFn: (accountId: number) => api(`/api/accounts/${accountId}`, { method: 'DELETE' }),
      onSuccess: refreshEverything,
    }),
  }
}
