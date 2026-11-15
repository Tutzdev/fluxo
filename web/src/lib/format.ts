import type { Money } from '@/lib/types'

const currency = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' })
const wholeCurrency = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 })
const shortDate = new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'short', timeZone: 'UTC' })
const monthName = new Intl.DateTimeFormat('en-GB', { month: 'long', timeZone: 'UTC' })
const monthAndYear = new Intl.DateTimeFormat('en-GB', { month: 'long', year: 'numeric', timeZone: 'UTC' })
const shortMonth = new Intl.DateTimeFormat('en-GB', { month: 'short', timeZone: 'UTC' })

/** Amounts are shown the way a Brazilian statement shows them: R$ 1.234,56. */
export function formatMoney(value: Money | number, options: { whole?: boolean; signed?: boolean } = {}): string {
  const number = Number(value)
  const text = (options.whole ? wholeCurrency : currency).format(Math.abs(number))

  if (number < 0) {
    return `−${text}`
  }
  return options.signed && number > 0 ? `+${text}` : text
}

export function toNumber(value: Money): number {
  return Number(value)
}

/** API dates are calendar days ("2026-11-15"); reading them as UTC keeps them from shifting a day. */
export function formatDay(isoDate: string): string {
  return shortDate.format(new Date(`${isoDate}T00:00:00Z`))
}

export function monthLabel(month: string, withYear = true): string {
  const date = new Date(`${month}-01T00:00:00Z`)
  return (withYear ? monthAndYear : monthName).format(date)
}

export function shortMonthLabel(month: string): string {
  return shortMonth.format(new Date(`${month}-01T00:00:00Z`))
}

export function currentMonth(): string {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
}

export function shiftMonth(month: string, offset: number): string {
  const [year, monthNumber] = month.split('-').map(Number)
  const index = year * 12 + (monthNumber - 1) + offset
  return `${Math.floor(index / 12)}-${String((index % 12) + 1).padStart(2, '0')}`
}

export function plural(count: number, one: string, many: string): string {
  return `${count} ${count === 1 ? one : many}`
}
