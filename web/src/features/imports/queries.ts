import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { StatementImport } from '@/lib/types'

export function useRecentImports() {
  return useQuery({
    queryKey: ['imports'],
    queryFn: async () => (await api<{ items: StatementImport[] }>('/api/imports')).items,
  })
}

export function useImportStatement() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ accountId, file, invert }: { accountId: number; file: File; invert: boolean }) => {
      const form = new FormData()
      form.set('file', file)
      form.set('account_id', String(accountId))
      form.set('invert_amounts', String(invert))
      return api<StatementImport>('/api/imports', { body: form })
    },
    onSuccess: () => queryClient.invalidateQueries(),
  })
}
