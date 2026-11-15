import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { Category, CategoryKind } from '@/lib/types'

export const categoryKeys = { all: ['categories'] as const }

export function useCategories() {
  return useQuery({
    queryKey: categoryKeys.all,
    queryFn: async () => (await api<{ items: Category[] }>('/api/categories')).items,
    staleTime: 60_000,
  })
}

/** id -> category, for rows that only carry a category_id. */
export function useCategoryLookup(): Map<number, Category> {
  const { data = [] } = useCategories()
  return new Map(data.map((category) => [category.id, category]))
}

/** Rules and categories change what every list shows, so everything is refreshed after them. */
export function useCategoryMutations() {
  const queryClient = useQueryClient()
  const refreshEverything = () => queryClient.invalidateQueries()

  return {
    create: useMutation({
      mutationFn: (body: { name: string; kind: CategoryKind; color: string }) =>
        api<Category>('/api/categories', { body }),
      onSuccess: refreshEverything,
    }),
    remove: useMutation({
      mutationFn: (categoryId: number) => api(`/api/categories/${categoryId}`, { method: 'DELETE' }),
      onSuccess: refreshEverything,
    }),
    addRule: useMutation({
      mutationFn: ({ categoryId, pattern }: { categoryId: number; pattern: string }) =>
        api(`/api/categories/${categoryId}/rules`, { body: { pattern } }),
      onSuccess: refreshEverything,
    }),
    removeRule: useMutation({
      mutationFn: (ruleId: number) => api(`/api/categories/rules/${ruleId}`, { method: 'DELETE' }),
      onSuccess: refreshEverything,
    }),
  }
}
