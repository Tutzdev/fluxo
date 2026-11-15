import type { SelectHTMLAttributes } from 'react'
import { useCategories } from '@/features/categories/queries'
import type { CategoryKind } from '@/lib/types'

const GROUP_LABELS: Record<CategoryKind, string> = {
  expense: 'Spending',
  income: 'Income',
  transfer: 'Between my accounts',
}

interface CategorySelectProps extends Omit<SelectHTMLAttributes<HTMLSelectElement>, 'value' | 'onChange'> {
  value: number | null
  onChange: (categoryId: number | null) => void
  emptyLabel?: string
}

/** A native select, grouped by kind: fast with a keyboard, and the phone shows its own picker. */
export function CategorySelect({ value, onChange, emptyLabel = 'No category', className = '', ...rest }: CategorySelectProps) {
  const { data: categories = [] } = useCategories()
  const kinds: CategoryKind[] = ['expense', 'income', 'transfer']

  return (
    <select
      {...rest}
      value={value ?? ''}
      onChange={(event) => onChange(event.target.value ? Number(event.target.value) : null)}
      className={`min-h-9 rounded-lg border border-line bg-surface px-2 text-sm focus:border-ink focus:outline-none ${className}`}
    >
      <option value="">{emptyLabel}</option>
      {kinds.map((kind) => (
        <optgroup key={kind} label={GROUP_LABELS[kind]}>
          {categories
            .filter((category) => category.kind === kind)
            .map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
        </optgroup>
      ))}
    </select>
  )
}
