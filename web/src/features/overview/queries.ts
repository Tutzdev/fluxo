import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { Forecast, MonthTotals, Summary } from '@/lib/types'

export function useSummary(month: string) {
  return useQuery({
    queryKey: ['reports', 'summary', month],
    queryFn: () => api<Summary>('/api/reports/summary', { query: { month } }),
  })
}

export function useTrend(month: string, months = 6) {
  return useQuery({
    queryKey: ['reports', 'trend', month, months],
    queryFn: async () => (await api<{ items: MonthTotals[] }>('/api/reports/trend', { query: { month, months } })).items,
  })
}

export function useForecast(enabled: boolean) {
  return useQuery({
    queryKey: ['reports', 'forecast'],
    queryFn: () => api<Forecast>('/api/reports/forecast'),
    enabled,
  })
}
