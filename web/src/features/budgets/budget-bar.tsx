import { formatMoney } from '@/lib/format'
import type { Budget, BudgetStatus } from '@/lib/types'

const FILL: Record<BudgetStatus, string> = {
  on_track: 'bg-ink',
  warning: 'bg-brass',
  exceeded: 'bg-over',
}

function statusText(budget: Budget): string {
  if (budget.status === 'exceeded') {
    return `${formatMoney(-Number(budget.remaining))} over`
  }
  return `${formatMoney(budget.remaining)} left`
}

export function BudgetBar({ budget }: { budget: Budget }) {
  const filled = Math.min(budget.percent_used, 100)

  return (
    <div>
      <div className="mb-1.5 flex items-baseline justify-between gap-3 text-sm">
        <span className="font-semibold">{budget.category_name}</span>
        <span className={`figures ${budget.status === 'exceeded' ? 'font-semibold text-over' : 'text-ink-soft'}`}>
          {statusText(budget)}
        </span>
      </div>
      <div
        role="meter"
        aria-label={`${budget.category_name} budget`}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={filled}
        aria-valuetext={`${formatMoney(budget.spent)} of ${formatMoney(budget.monthly_limit)}`}
        className="h-2 rounded-full bg-line"
      >
        <div className={`h-full rounded-full ${FILL[budget.status]}`} style={{ width: `${filled}%` }} />
      </div>
      <p className="figures mt-1 text-xs text-ink-soft">
        {formatMoney(budget.spent)} of {formatMoney(budget.monthly_limit)}
      </p>
    </div>
  )
}
