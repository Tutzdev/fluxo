import { Plus, X } from 'lucide-react'
import { type FormEvent, useState } from 'react'
import { Button } from '@/components/ui/button'
import { ErrorNotice, Notice } from '@/components/ui/notice'
import { PageHeader } from '@/components/ui/page-header'
import { useCategories, useCategoryMutations } from '@/features/categories/queries'
import type { Category, CategoryKind } from '@/lib/types'

const SECTIONS: { kind: CategoryKind; title: string; description: string }[] = [
  { kind: 'expense', title: 'Spending', description: 'What money goes out on.' },
  { kind: 'income', title: 'Income', description: 'What comes in.' },
  {
    kind: 'transfer',
    title: 'Between my accounts',
    description: 'Paying the card bill, saving, investing. Left out of income and spending so nothing counts twice.',
  },
]

function RuleChips({ category }: { category: Category }) {
  const { addRule, removeRule } = useCategoryMutations()
  const [pattern, setPattern] = useState('')

  const add = (event: FormEvent) => {
    event.preventDefault()
    if (pattern.trim()) {
      addRule.mutate({ categoryId: category.id, pattern }, { onSuccess: () => setPattern('') })
    }
  }

  return (
    <div className="mt-3">
      <ul className="flex flex-wrap gap-1.5" aria-label={`Rules for ${category.name}`}>
        {category.rules.map((rule) => (
          <li key={rule.id} className="flex items-center gap-1 rounded-full bg-paper py-0.5 pr-1 pl-2.5 text-xs font-semibold tracking-wide">
            {rule.pattern}
            <button
              type="button"
              onClick={() => removeRule.mutate(rule.id)}
              className="rounded-full p-0.5 text-ink-soft hover:bg-line hover:text-ink"
              aria-label={`Remove rule ${rule.pattern}`}
            >
              <X aria-hidden className="size-3" />
            </button>
          </li>
        ))}
        <li>
          <form onSubmit={add} className="flex items-center gap-1">
            <input
              value={pattern}
              onChange={(event) => setPattern(event.target.value)}
              placeholder="Add a word, like PADARIA"
              aria-label={`New rule for ${category.name}`}
              className="h-7 w-48 rounded-full border border-dashed border-line bg-transparent px-3 text-xs focus:border-ink focus:outline-none"
            />
            {pattern.trim() && (
              <button type="submit" className="rounded-full bg-ink p-1 text-paper" aria-label="Add rule">
                <Plus aria-hidden className="size-3.5" />
              </button>
            )}
          </form>
        </li>
      </ul>
      <ErrorNotice error={addRule.error} />
    </div>
  )
}

function CategoryRow({ category }: { category: Category }) {
  const { remove } = useCategoryMutations()
  const [confirming, setConfirming] = useState(false)

  return (
    <li className="p-4">
      <div className="flex items-center justify-between gap-3">
        <span className="flex items-center gap-2.5 font-semibold">
          <span aria-hidden className="size-3 rounded-full" style={{ backgroundColor: category.color }} />
          {category.name}
        </span>
        {confirming ? (
          <span className="flex gap-3 text-sm">
            <button type="button" className="font-semibold text-over" onClick={() => remove.mutate(category.id)}>
              Delete {category.name}
            </button>
            <button type="button" className="text-ink-soft" onClick={() => setConfirming(false)}>
              Keep
            </button>
          </span>
        ) : (
          <button type="button" className="text-sm text-ink-soft hover:text-over" onClick={() => setConfirming(true)}>
            Delete
          </button>
        )}
      </div>
      {confirming && (
        <p className="mt-2 text-sm text-ink-soft">Its transactions go back to review, and its rules and budget are removed.</p>
      )}
      <RuleChips category={category} />
    </li>
  )
}

function NewCategory() {
  const { create } = useCategoryMutations()
  const [name, setName] = useState('')
  const [kind, setKind] = useState<CategoryKind>('expense')
  const [color, setColor] = useState('#4f8d9c')

  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (name.trim()) {
      create.mutate({ name: name.trim(), kind, color }, { onSuccess: () => setName('') })
    }
  }

  return (
    <form onSubmit={submit} className="flex flex-wrap items-end gap-3">
      <label className="flex flex-col gap-1.5 text-sm font-semibold">
        Name
        <input
          value={name}
          onChange={(event) => setName(event.target.value)}
          maxLength={40}
          placeholder="Pets"
          className="min-h-11 rounded-lg border border-line bg-surface px-3 font-normal focus:border-ink focus:outline-none"
        />
      </label>
      <label className="flex flex-col gap-1.5 text-sm font-semibold">
        Kind
        <select
          value={kind}
          onChange={(event) => setKind(event.target.value as CategoryKind)}
          className="min-h-11 rounded-lg border border-line bg-surface px-3 font-normal focus:border-ink focus:outline-none"
        >
          <option value="expense">Spending</option>
          <option value="income">Income</option>
          <option value="transfer">Between my accounts</option>
        </select>
      </label>
      <label className="flex flex-col gap-1.5 text-sm font-semibold">
        Colour
        <input type="color" value={color} onChange={(event) => setColor(event.target.value)} className="h-11 w-14 rounded-lg border border-line bg-surface p-1" />
      </label>
      <Button type="submit" disabled={!name.trim()} busy={create.isPending}>
        Add category
      </Button>
      <div className="basis-full">
        <ErrorNotice error={create.error} />
      </div>
    </form>
  )
}

export function CategoriesPage() {
  const { data: categories = [], error } = useCategories()

  return (
    <div>
      <PageHeader
        title="Categories & rules"
        description="A rule is a word from the bank description. When it shows up, the transaction goes to that category, no guessing. Rules always win over what Fluxo learned, and only your own choices win over rules."
      />

      <div className="mb-8 flex flex-col gap-4">
        <ErrorNotice error={error} />
        <Notice>New rules apply right away to past transactions too, except the ones you categorized yourself.</Notice>
      </div>

      <div className="flex flex-col gap-10">
        {SECTIONS.map((section) => (
          <section key={section.kind} aria-labelledby={`section-${section.kind}`}>
            <h2 id={`section-${section.kind}`} className="text-xl">
              {section.title}
            </h2>
            <p className="mb-4 text-sm text-ink-soft">{section.description}</p>
            <ul className="divide-y divide-line rounded-2xl bg-surface ring-1 ring-line">
              {categories
                .filter((category) => category.kind === section.kind)
                .map((category) => (
                  <CategoryRow key={category.id} category={category} />
                ))}
            </ul>
          </section>
        ))}

        <section aria-labelledby="new-category">
          <h2 id="new-category" className="mb-4 text-xl">
            New category
          </h2>
          <NewCategory />
        </section>
      </div>
    </div>
  )
}
