import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { Budget } from '@/lib/types'

export function useBudgets(month: string) {
  return useQuery({
    queryKey: ['budgets', month],
    queryFn: async () => (await api<{ month: string; items: Budget[] }>('/api/budgets', { query: { month } })).items,
  })
}

export function useBudgetMutations() {
  const queryClient = useQueryClient()
  const refreshBudgets = () => queryClient.invalidateQueries({ queryKey: ['budgets'] })

  return {
    setLimit: useMutation({
      mutationFn: ({ categoryId, monthlyLimit }: { categoryId: number; monthlyLimit: string }) =>
        api(`/api/budgets/${categoryId}`, { method: 'PUT', body: { monthly_limit: monthlyLimit } }),
      onSuccess: refreshBudgets,
    }),
    remove: useMutation({
      mutationFn: (categoryId: number) => api(`/api/budgets/${categoryId}`, { method: 'DELETE' }),
      onSuccess: refreshBudgets,
    }),
  }
}
