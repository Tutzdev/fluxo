import { ChevronLeft, ChevronRight } from 'lucide-react'
import { currentMonth, monthLabel, shiftMonth } from '@/lib/format'

interface MonthSwitcherProps {
  month: string
  onChange: (month: string) => void
}

export function MonthSwitcher({ month, onChange }: MonthSwitcherProps) {
  const isCurrent = month >= currentMonth()

  return (
    <div className="inline-flex items-center gap-1 rounded-lg bg-surface p-1 ring-1 ring-line">
      <button
        type="button"
        onClick={() => onChange(shiftMonth(month, -1))}
        className="rounded-md p-1.5 hover:bg-paper"
        aria-label="Previous month"
      >
        <ChevronLeft aria-hidden className="size-4" />
      </button>
      <span className="min-w-36 text-center text-sm font-semibold" aria-live="polite">
        {monthLabel(month)}
      </span>
      <button
        type="button"
        onClick={() => onChange(shiftMonth(month, 1))}
        disabled={isCurrent}
        className="rounded-md p-1.5 hover:bg-paper disabled:opacity-30 disabled:hover:bg-transparent"
        aria-label="Next month"
      >
        <ChevronRight aria-hidden className="size-4" />
      </button>
    </div>
  )
}
