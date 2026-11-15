import { formatMoney } from '@/lib/format'
import type { Money } from '@/lib/types'

interface AmountProps {
  value: Money | number
  whole?: boolean
  className?: string
}

/** Money in, green and signed; money out in plain ink, because spending is not an error. */
export function Amount({ value, whole = false, className = '' }: AmountProps) {
  const isIncome = Number(value) > 0

  return (
    <span className={`figures whitespace-nowrap ${isIncome ? 'text-income' : ''} ${className}`}>
      {formatMoney(value, { whole, signed: true })}
    </span>
  )
}
