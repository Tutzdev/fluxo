import { type FormEvent, useState } from 'react'
import { Button } from '@/components/ui/button'
import { MonthSwitcher } from '@/components/ui/month-switcher'
import { ErrorNotice } from '@/components/ui/notice'
import { PageHeader } from '@/components/ui/page-header'
import { BudgetBar } from '@/features/budgets/budget-bar'
import { useBudgetMutations, useBudgets } from '@/features/budgets/queries'
import { useCategories } from '@/features/categories/queries'
import { currentMonth } from '@/lib/format'
import type { Budget } from '@/lib/types'

const AMOUNT = /^\d{1,12}([.,]\d{1,2})?$/

function toApiAmount(text: string): string | null {
  const trimmed = text.trim()
  return AMOUNT.test(trimmed) && Number(trimmed.replace(',', '.')) > 0 ? trimmed.replace(',', '.') : null
}

function BudgetRow({ budget }: { budget: Budget }) {
  const { setLimit, remove } = useBudgetMutations()
  const [editing, setEditing] = useState(false)
  const [limit, setLimitText] = useState(budget.monthly_limit.replace('.', ','))
  const parsed = toApiAmount(limit)

  const save = (event: FormEvent) => {
    event.preventDefault()
    if (parsed) {
      setLimit.mutate({ categoryId: budget.category_id, monthlyLimit: parsed }, { onSuccess: () => setEditing(false) })
    }
  }

  return (
    <li className="p-4">
      <BudgetBar budget={budget} />
      {editing ? (
        <form onSubmit={save} className="mt-3 flex flex-wrap items-center gap-2">
          <label className="text-sm" htmlFor={`limit-${budget.category_id}`}>
            Monthly limit (R$)
          </label>
          <input
            id={`limit-${budget.category_id}`}
            inputMode="decimal"
            value={limit}
            onChange={(event) => setLimitText(event.target.value)}
            aria-invalid={!parsed || undefined}
            className="min-h-9 w-28 rounded-lg border border-line px-2 text-sm focus:border-ink focus:outline-none"
          />
          <Button type="submit" size="small" disabled={!parsed} busy={setLimit.isPending}>
            Save limit
          </Button>
          <Button variant="quiet" size="small" onClick={() => setEditing(false)}>
            Cancel
          </Button>
        </form>
      ) : (
        <div className="mt-2 flex gap-4 text-sm">
          <button type="button" className="font-semibold text-ink-soft hover:text-ink" onClick={() => setEditing(true)}>
            Change limit
          </button>
          <button type="button" className="font-semibold text-ink-soft hover:text-over" onClick={() => remove.mutate(budget.category_id)}>
            Remove budget
          </button>
        </div>
      )}
      <ErrorNotice error={setLimit.error ?? remove.error} />
    </li>
  )
}

function NewBudget({ budgeted }: { budgeted: Set<number> }) {
  const { data: categories = [] } = useCategories()
  const { setLimit } = useBudgetMutations()
  const [categoryId, setCategoryId] = useState('')
  const [limit, setLimitText] = useState('')
  const parsed = toApiAmount(limit)

  const available = categories.filter((category) => category.kind === 'expense' && !budgeted.has(category.id))

  const create = (event: FormEvent) => {
    event.preventDefault()
    if (categoryId && parsed) {
      setLimit.mutate(
        { categoryId: Number(categoryId), monthlyLimit: parsed },
        {
          onSuccess: () => {
            setCategoryId('')
            setLimitText('')
          },
        },
      )
    }
  }

  if (available.length === 0) {
    return null
  }

  return (
    <form onSubmit={create} className="mt-8 flex flex-wrap items-end gap-3">
      <label className="flex flex-col gap-1.5 text-sm font-semibold">
        Category
        <select
          value={categoryId}
          onChange={(event) => setCategoryId(event.target.value)}
          className="min-h-11 rounded-lg border border-line bg-surface px-3 font-normal focus:border-ink focus:outline-none"
        >
          <option value="">Choose a category</option>
          {available.map((category) => (
            <option key={category.id} value={category.id}>
              {category.name}
            </option>
          ))}
        </select>
      </label>
      <label className="flex flex-col gap-1.5 text-sm font-semibold">
        Monthly limit (R$)
        <input
          inputMode="decimal"
          placeholder="800"
          value={limit}
          onChange={(event) => setLimitText(event.target.value)}
          className="min-h-11 w-32 rounded-lg border border-line bg-surface px-3 font-normal focus:border-ink focus:outline-none"
        />
      </label>
      <Button type="submit" disabled={!categoryId || !parsed} busy={setLimit.isPending}>
        Add budget
      </Button>
      <div className="basis-full">
        <ErrorNotice error={setLimit.error} />
      </div>
    </form>
  )
}

export function BudgetsPage() {
  const [month, setMonth] = useState(currentMonth())
  const budgets = useBudgets(month)
  const items = budgets.data ?? []

  return (
    <div>
      <PageHeader
        title="Budgets"
        description="A monthly limit for the categories you want to keep an eye on. The bar turns brass at 80% and red once it goes over."
        actions={<MonthSwitcher month={month} onChange={setMonth} />}
      />

      <ErrorNotice error={budgets.error} />

      {budgets.isSuccess && items.length === 0 ? (
        <p className="rounded-2xl bg-surface p-8 text-ink-soft ring-1 ring-line">
          No budgets yet. Pick a category below and give it a monthly limit.
        </p>
      ) : (
        <ul className="grid divide-y divide-line rounded-2xl bg-surface ring-1 ring-line">
          {items.map((budget) => (
            <BudgetRow key={`${budget.category_id}-${budget.monthly_limit}`} budget={budget} />
          ))}
        </ul>
      )}

      <NewBudget budgeted={new Set(items.map((budget) => budget.category_id))} />
    </div>
  )
}
