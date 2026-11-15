import type { Transaction } from '@/lib/types'

/** Who decided the category, in words a person uses: "Rule", "Learned 82%", "You". */
export function CategorySource({ transaction }: { transaction: Transaction }) {
  // A fixed width keeps every row's category select the same size, whatever the label.
  return <span className="w-24 shrink-0">{label(transaction)}</span>
}

function label(transaction: Transaction) {
  if (transaction.needs_review) {
    return <span className="rounded-full bg-brass-soft px-2 py-0.5 text-xs font-semibold text-brass-deep">Needs you</span>
  }

  switch (transaction.category_source) {
    case 'model': {
      const confidence = Math.round(Number(transaction.category_confidence ?? 0) * 100)
      return (
        <span
          className="rounded-full px-2 py-0.5 text-xs font-semibold text-brass-deep ring-1 ring-inset ring-brass/50"
          title="Centavo learned this from categories you chose before"
        >
          Learned {confidence}%
        </span>
      )
    }
    case 'rule':
      return <span className="text-xs text-ink-soft" title="A keyword rule matched">Rule</span>
    default:
      return <span className="text-xs text-ink-soft" title="You chose this category">You</span>
  }
}
