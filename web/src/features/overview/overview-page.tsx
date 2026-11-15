import { Inbox } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router'
import { Amount } from '@/components/ui/amount'
import { MonthSwitcher } from '@/components/ui/month-switcher'
import { ErrorNotice } from '@/components/ui/notice'
import { BudgetBar } from '@/features/budgets/budget-bar'
import { useBudgets } from '@/features/budgets/queries'
import { useForecast, useSummary, useTrend } from '@/features/overview/queries'
import { currentMonth, formatMoney, monthLabel, plural, shortMonthLabel } from '@/lib/format'
import type { Forecast, MonthTotals, Summary } from '@/lib/types'

function Headline({ summary }: { summary: Summary }) {
  return (
    <div>
      <p className="font-display text-3xl font-semibold leading-tight sm:text-4xl">
        <span className="figures">{formatMoney(summary.expenses, { whole: true })}</span> out,{' '}
        <span className="figures text-income">{formatMoney(summary.income, { whole: true })}</span> in.
      </p>
      <p className="mt-2 text-ink-soft">
        {Number(summary.net) >= 0
          ? `You kept ${formatMoney(summary.net)} this month.`
          : `You spent ${formatMoney(-Number(summary.net))} more than came in.`}{' '}
        Transfers between your own accounts are left out.
      </p>
    </div>
  )
}

function ReviewCallout({ count }: { count: number }) {
  if (count === 0) {
    return null
  }

  return (
    <Link
      to="/review"
      className="flex items-center gap-3 rounded-xl bg-brass-soft px-4 py-3 text-sm text-ink ring-1 ring-brass/40 hover:ring-brass"
    >
      <Inbox aria-hidden className="size-5 shrink-0 text-brass-deep" />
      <span className="flex-1">
        <strong>{plural(count, 'transaction', 'transactions')} this month without a category.</strong> Each one you sort teaches
        Fluxo the next.
      </span>
      <span className="font-semibold text-brass-deep">Review</span>
    </Link>
  )
}

function WhereItWent({ summary }: { summary: Summary }) {
  const largest = Math.max(...summary.by_category.map((item) => Number(item.amount)), 1)

  return (
    <section aria-labelledby="where-it-went">
      <h2 id="where-it-went" className="mb-4 text-xl">
        Where it went
      </h2>
      {summary.by_category.length === 0 ? (
        <p className="text-ink-soft">Nothing spent this month yet.</p>
      ) : (
        <ul className="flex flex-col gap-3">
          {summary.by_category.map((item) => (
            <li key={item.category_id ?? 'review'} className="grid grid-cols-[minmax(6rem,9rem)_1fr_6.5rem] items-center gap-3">
              <span className="truncate text-sm font-semibold">{item.name}</span>
              <span aria-hidden className="h-2.5 rounded-full bg-line">
                <span
                  className="block h-full rounded-full"
                  style={{ width: `${(Number(item.amount) / largest) * 100}%`, backgroundColor: item.color }}
                />
              </span>
              <span className="figures text-right text-sm">{formatMoney(item.amount)}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

function MonthEnd({ forecast }: { forecast: Forecast }) {
  const changes = [
    { label: 'Income still to come', value: forecast.expected_income },
    { label: 'Bills still to come', value: forecast.expected_bills },
    { label: `Day-to-day spending, ${plural(forecast.days_left, 'day', 'days')} at your usual pace`, value: forecast.projected_day_to_day },
  ]

  return (
    <section aria-labelledby="month-end" className="rounded-2xl bg-ink p-6 text-paper">
      <h2 id="month-end" className="text-lg text-paper/80">
        How {monthLabel(forecast.today.slice(0, 7), false)} ends
      </h2>
      <p className="figures mt-2 font-display text-4xl font-semibold">{formatMoney(forecast.projected_end_balance, { whole: true })}</p>
      <p className="mt-1 text-sm text-paper/70">across your accounts on the last day, if the month keeps its pace.</p>

      <dl className="mt-6 flex flex-col gap-2 border-t border-paper/15 pt-4 text-sm">
        <div className="flex justify-between gap-4">
          <dt className="text-paper/75">Balance today, all accounts</dt>
          <dd className="figures whitespace-nowrap">{formatMoney(forecast.balance_now)}</dd>
        </div>
        {changes.map((row) => (
          <div key={row.label} className="flex justify-between gap-4">
            <dt className="text-paper/75">{row.label}</dt>
            <dd className="figures whitespace-nowrap">{formatMoney(row.value, { signed: true })}</dd>
          </div>
        ))}
      </dl>

      {forecast.upcoming.length > 0 && (
        <div className="mt-5 border-t border-paper/15 pt-4">
          <h3 className="mb-2 font-sans text-sm font-semibold text-paper/75">Recurring, not seen yet this month</h3>
          <ul className="flex flex-col gap-1.5 text-sm">
            {forecast.upcoming.map((item) => (
              <li key={item.description} className="flex justify-between gap-4">
                <span className="min-w-0">
                  <span className="block truncate">{item.description}</span>
                  <span className="block text-paper/60">around day {item.expected_day}</span>
                </span>
                <span className="figures whitespace-nowrap">{formatMoney(item.amount, { signed: true })}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  )
}

function Trend({ months }: { months: MonthTotals[] }) {
  const largest = Math.max(...months.flatMap((item) => [Number(item.income), Number(item.expenses)]), 1)

  return (
    <section aria-labelledby="trend">
      <h2 id="trend" className="mb-1 text-xl">
        Six months
      </h2>
      <p className="mb-5 flex gap-4 text-sm text-ink-soft">
        <span className="flex items-center gap-1.5">
          <span aria-hidden className="size-2.5 rounded-sm bg-income" /> In
        </span>
        <span className="flex items-center gap-1.5">
          <span aria-hidden className="size-2.5 rounded-sm bg-ink" /> Out
        </span>
      </p>
      <ol className="grid grid-cols-6 items-end gap-2 sm:gap-4">
        {months.map((item) => (
          <li key={item.month} className="flex flex-col items-center gap-2">
            <div aria-hidden className="flex h-36 w-full items-end justify-center gap-1">
              <span className="w-1/3 max-w-5 rounded-t bg-income" style={{ height: `${(Number(item.income) / largest) * 100}%` }} />
              <span className="w-1/3 max-w-5 rounded-t bg-ink" style={{ height: `${(Number(item.expenses) / largest) * 100}%` }} />
            </div>
            <span className="text-xs font-semibold">{shortMonthLabel(item.month)}</span>
            <Amount value={item.net} whole className="hidden text-xs sm:inline" />
            <span className="sr-only">
              {monthLabel(item.month)}: {formatMoney(item.income)} in, {formatMoney(item.expenses)} out
            </span>
          </li>
        ))}
      </ol>
    </section>
  )
}

export function OverviewPage() {
  const [month, setMonth] = useState(currentMonth())
  const isCurrentMonth = month === currentMonth()

  const summary = useSummary(month)
  const trend = useTrend(month)
  const forecast = useForecast(isCurrentMonth)
  const budgets = useBudgets(month)

  return (
    <div className="flex flex-col gap-10">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl">{isCurrentMonth ? `${monthLabel(month, false)} so far` : monthLabel(month)}</h1>
        <MonthSwitcher month={month} onChange={setMonth} />
      </div>

      <ErrorNotice error={summary.error} />

      {summary.data && (
        <>
          <Headline summary={summary.data} />
          <ReviewCallout count={summary.data.needs_review} />
        </>
      )}

      <div className="grid gap-10 lg:grid-cols-[1fr_22rem]">
        {summary.data && <WhereItWent summary={summary.data} />}
        {isCurrentMonth && forecast.data && <MonthEnd forecast={forecast.data} />}
      </div>

      {budgets.data && budgets.data.length > 0 && (
        <section aria-labelledby="budgets">
          <div className="mb-4 flex items-baseline justify-between">
            <h2 id="budgets" className="text-xl">
              Budgets
            </h2>
            <Link to="/budgets" className="text-sm font-semibold text-ink-soft hover:text-ink">
              Edit budgets
            </Link>
          </div>
          <ul className="grid gap-x-10 gap-y-4 sm:grid-cols-2">
            {budgets.data.map((budget) => (
              <li key={budget.category_id}>
                <BudgetBar budget={budget} />
              </li>
            ))}
          </ul>
        </section>
      )}

      {trend.data && <Trend months={trend.data} />}
    </div>
  )
}
