import { Sparkles } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router'
import { Amount } from '@/components/ui/amount'
import { Button } from '@/components/ui/button'
import { ErrorNotice, Notice } from '@/components/ui/notice'
import { PageHeader } from '@/components/ui/page-header'
import { useAccounts } from '@/features/accounts/queries'
import { CategorySelect } from '@/features/categories/category-select'
import { useTransactionMutations, useTransactions } from '@/features/transactions/queries'
import { formatDay, plural } from '@/lib/format'
import type { CategorizationSummary } from '@/lib/types'

function LearningResult({ result }: { result: CategorizationSummary }) {
  return (
    <Notice tone="success">
      Fluxo went through everything again: {plural(result.by_model, 'transaction', 'transactions')} sorted by what
      it learned from you, {result.by_rule} by your rules.{' '}
      {result.left_for_review > 0
        ? `${plural(result.left_for_review, 'still needs', 'still need')} you.`
        : 'Nothing is left to review.'}
    </Notice>
  )
}

export function ReviewPage() {
  const queue = useTransactions({ needs_review: true, page_size: 50 })
  const { data: accounts } = useAccounts()
  const { setCategory, recategorize } = useTransactionMutations()
  const [sortedThisVisit, setSortedThisVisit] = useState(0)
  const [result, setResult] = useState<CategorizationSummary | null>(null)

  const accountName = (accountId: number) => accounts?.items.find((account) => account.id === accountId)?.name ?? ''

  const choose = (transactionId: number, categoryId: number | null) => {
    if (categoryId === null) {
      return
    }
    setResult(null)
    setCategory.mutate(
      { transactionId, categoryId },
      { onSuccess: () => setSortedThisVisit((count) => count + 1) },
    )
  }

  const learn = () =>
    recategorize.mutate(undefined, {
      onSuccess: (summary) => {
        setResult(summary)
        setSortedThisVisit(0)
      },
    })

  const items = queue.data?.items ?? []

  return (
    <div>
      <PageHeader
        title="Review"
        description="Lines no rule knew and Fluxo was not sure about. Pick a category for a few, then let Fluxo use what you taught on the rest."
      />

      <div className="mb-6 flex flex-col gap-3">
        {result && <LearningResult result={result} />}
        <ErrorNotice error={queue.error ?? setCategory.error ?? recategorize.error} />
      </div>

      {sortedThisVisit > 0 && (
        <div className="sticky top-16 z-20 mb-6 flex flex-wrap items-center justify-between gap-3 rounded-xl bg-ink px-4 py-3 text-paper lg:top-4">
          <p className="text-sm">
            You sorted {plural(sortedThisVisit, 'line', 'lines')}. Fluxo can now look for similar ones.
          </p>
          <Button variant="brass" size="small" busy={recategorize.isPending} onClick={learn}>
            <Sparkles aria-hidden className="size-4" />
            Sort the rest with what I taught
          </Button>
        </div>
      )}

      {queue.isSuccess && items.length === 0 ? (
        <div className="rounded-2xl bg-surface p-8 ring-1 ring-line">
          <h2 className="text-xl">Nothing to review</h2>
          <p className="mt-2 text-ink-soft">
            Every transaction has a category. New ones show up here after an <Link to="/import" className="font-semibold underline">import</Link>{' '}
            when no rule matches and Fluxo is not sure.
          </p>
        </div>
      ) : (
        <ul className="divide-y divide-line rounded-2xl bg-surface ring-1 ring-line">
          {items.map((transaction) => (
            <li key={transaction.id} className="grid gap-3 p-4 sm:grid-cols-[1fr_auto_14rem] sm:items-center">
              <div className="min-w-0">
                <p className="truncate font-semibold tracking-wide">{transaction.description}</p>
                <p className="text-sm text-ink-soft">
                  {formatDay(transaction.occurred_on)}, {accountName(transaction.account_id)}
                </p>
              </div>
              <Amount value={transaction.amount} className="sm:text-right" />
              <CategorySelect
                aria-label={`Category for ${transaction.description}`}
                value={null}
                emptyLabel="Choose a category"
                disabled={setCategory.isPending}
                onChange={(categoryId) => choose(transaction.id, categoryId)}
              />
            </li>
          ))}
        </ul>
      )}

      {queue.data && queue.data.total > items.length && (
        <p className="mt-4 text-sm text-ink-soft">
          Showing the {items.length} most recent of {queue.data.total}. Sorting these usually takes care of many of the rest.
        </p>
      )}
    </div>
  )
}
