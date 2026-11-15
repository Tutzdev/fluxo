import { ChevronLeft, ChevronRight, Plus, Trash2 } from 'lucide-react'
import { useDeferredValue, useState } from 'react'
import { Amount } from '@/components/ui/amount'
import { Button } from '@/components/ui/button'
import { CategorySource } from '@/components/ui/category-source'
import { MonthSwitcher } from '@/components/ui/month-switcher'
import { ErrorNotice } from '@/components/ui/notice'
import { PageHeader } from '@/components/ui/page-header'
import { useAccounts } from '@/features/accounts/queries'
import { CategorySelect } from '@/features/categories/category-select'
import { AddTransactionDialog } from '@/features/transactions/add-transaction-dialog'
import { useTransactionMutations, useTransactions } from '@/features/transactions/queries'
import { currentMonth, formatDay, formatMoney, plural } from '@/lib/format'
import type { Transaction } from '@/lib/types'

const PAGE_SIZE = 50

const filterControl = 'min-h-10 rounded-lg border border-line bg-surface px-3 text-sm focus:border-ink focus:outline-none'

function DeleteButton({ transaction }: { transaction: Transaction }) {
  const { remove } = useTransactionMutations()
  const [confirming, setConfirming] = useState(false)

  if (confirming) {
    return (
      <span className="flex items-center gap-2 text-sm">
        <button type="button" className="font-semibold text-over" onClick={() => remove.mutate(transaction.id)}>
          Delete
        </button>
        <button type="button" className="text-ink-soft" onClick={() => setConfirming(false)}>
          Keep
        </button>
      </span>
    )
  }

  return (
    <button
      type="button"
      onClick={() => setConfirming(true)}
      className="rounded-md p-1.5 text-ink-soft hover:bg-paper hover:text-over"
      aria-label={`Delete ${transaction.description}`}
    >
      <Trash2 aria-hidden className="size-4" />
    </button>
  )
}

export function TransactionsPage() {
  const [month, setMonth] = useState(currentMonth())
  const [accountId, setAccountId] = useState<number | undefined>()
  const [categoryId, setCategoryId] = useState<number | null>(null)
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [adding, setAdding] = useState(false)

  const deferredSearch = useDeferredValue(search.trim())
  const transactions = useTransactions({
    month,
    account_id: accountId,
    category_id: categoryId ?? undefined,
    search: deferredSearch || undefined,
    page,
    page_size: PAGE_SIZE,
  })
  const { data: accounts } = useAccounts()
  const { setCategory } = useTransactionMutations()

  const accountName = (id: number) => accounts?.items.find((account) => account.id === id)?.name ?? ''
  const data = transactions.data
  const lastPage = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1

  const resetPage = <T,>(update: (value: T) => void) => (value: T) => {
    update(value)
    setPage(1)
  }

  return (
    <div>
      <PageHeader
        title="Transactions"
        description="Change a category and Fluxo remembers it for lines like that one."
        actions={
          <Button onClick={() => setAdding(true)}>
            <Plus aria-hidden className="size-4" />
            Add transaction
          </Button>
        }
      />

      <div className="mb-6 flex flex-wrap items-center gap-3">
        <MonthSwitcher month={month} onChange={resetPage(setMonth)} />
        <select
          aria-label="Account"
          value={accountId ?? ''}
          onChange={(event) => resetPage(setAccountId)(event.target.value ? Number(event.target.value) : undefined)}
          className={filterControl}
        >
          <option value="">All accounts</option>
          {accounts?.items.map((account) => (
            <option key={account.id} value={account.id}>
              {account.name}
            </option>
          ))}
        </select>
        <CategorySelect aria-label="Category" value={categoryId} onChange={resetPage(setCategoryId)} emptyLabel="All categories" className="min-h-10" />
        <input
          type="search"
          aria-label="Search descriptions"
          placeholder="Search, like padaria"
          value={search}
          onChange={(event) => resetPage(setSearch)(event.target.value)}
          className={`${filterControl} w-full sm:w-auto sm:min-w-56 sm:flex-1 sm:max-w-72`}
        />
      </div>

      <ErrorNotice error={transactions.error ?? setCategory.error} />

      {data && (
        <p className="mb-3 text-sm text-ink-soft">
          {plural(data.total, 'transaction', 'transactions')}:{' '}
          <span className="figures text-income">{formatMoney(data.income, { signed: true })}</span> in,{' '}
          <span className="figures text-ink">{formatMoney(-Number(data.expenses))}</span> out.
        </p>
      )}

      {data && data.items.length === 0 ? (
        <p className="rounded-2xl bg-surface p-8 text-ink-soft ring-1 ring-line">No transactions match these filters.</p>
      ) : (
        <ul className="divide-y divide-line rounded-2xl bg-surface ring-1 ring-line" aria-busy={transactions.isFetching}>
          {data?.items.map((transaction) => (
            // On a phone the amount sits next to the description; on wider screens it moves after the category.
            <li
              key={transaction.id}
              className="grid grid-cols-[1fr_auto] items-center gap-x-4 gap-y-2 p-4 md:grid-cols-[1fr_17rem_8rem_2.5rem]"
            >
              <div className="min-w-0">
                <p className="truncate font-semibold tracking-wide">{transaction.description}</p>
                <p className="truncate text-sm text-ink-soft">
                  {formatDay(transaction.occurred_on)}, {accountName(transaction.account_id)}
                </p>
              </div>
              <Amount value={transaction.amount} className="text-right md:order-3" />
              <div className="flex min-w-0 items-center gap-2 md:order-2">
                <CategorySelect
                  aria-label={`Category for ${transaction.description}`}
                  value={transaction.category_id}
                  emptyLabel="Needs a category"
                  onChange={(id) => setCategory.mutate({ transactionId: transaction.id, categoryId: id })}
                  className="min-w-0 flex-1"
                />
                <CategorySource transaction={transaction} />
              </div>
              <div className="flex justify-end md:order-4">
                <DeleteButton transaction={transaction} />
              </div>
            </li>
          ))}
        </ul>
      )}

      {lastPage > 1 && (
        <nav aria-label="Pages" className="mt-4 flex items-center justify-end gap-3 text-sm">
          <Button variant="quiet" size="small" disabled={page <= 1} onClick={() => setPage(page - 1)}>
            <ChevronLeft aria-hidden className="size-4" />
            Newer
          </Button>
          <span className="figures">
            Page {page} of {lastPage}
          </span>
          <Button variant="quiet" size="small" disabled={page >= lastPage} onClick={() => setPage(page + 1)}>
            Older
            <ChevronRight aria-hidden className="size-4" />
          </Button>
        </nav>
      )}

      <AddTransactionDialog open={adding} onOpenChange={setAdding} />
    </div>
  )
}
