import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link } from 'react-router'
import { z } from 'zod'
import { Amount } from '@/components/ui/amount'
import { Button } from '@/components/ui/button'
import { SelectField, TextField } from '@/components/ui/field'
import { ErrorNotice } from '@/components/ui/notice'
import { PageHeader } from '@/components/ui/page-header'
import { ACCOUNT_KIND_LABELS, useAccountMutations, useAccounts } from '@/features/accounts/queries'
import { formatMoney, plural } from '@/lib/format'
import type { Account, AccountKind } from '@/lib/types'

const KINDS = Object.keys(ACCOUNT_KIND_LABELS) as AccountKind[]

const schema = z.object({
  name: z.string().trim().min(1, 'Give it a name you recognize, like Nubank.').max(60),
  kind: z.enum(['checking', 'savings', 'credit_card', 'cash']),
  opening_balance: z
    .string()
    .trim()
    .regex(/^-?\d{1,12}([.,]\d{1,2})?$/, 'Type an amount like 1500,00, or 0.'),
})

type Values = z.infer<typeof schema>

function NewAccountForm() {
  const { create } = useAccountMutations()
  const form = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: { name: '', kind: 'checking', opening_balance: '0' },
  })

  const submit = form.handleSubmit((values) => {
    create.mutate(
      { ...values, opening_balance: values.opening_balance.replace(',', '.') },
      { onSuccess: () => form.reset() },
    )
  })

  const errors = form.formState.errors

  return (
    <form onSubmit={submit} className="grid max-w-3xl gap-4 sm:grid-cols-3" noValidate>
      <TextField label="Name" placeholder="Nubank" error={errors.name?.message} {...form.register('name')} />
      <SelectField label="Kind" {...form.register('kind')}>
        {KINDS.map((kind) => (
          <option key={kind} value={kind}>
            {ACCOUNT_KIND_LABELS[kind]}
          </option>
        ))}
      </SelectField>
      <TextField
        label="Balance before the first import (R$)"
        inputMode="decimal"
        error={errors.opening_balance?.message}
        {...form.register('opening_balance')}
      />
      <div className="flex flex-col gap-3 sm:col-span-3">
        <ErrorNotice error={create.error} />
        <Button type="submit" busy={create.isPending} className="self-start">
          Add account
        </Button>
      </div>
    </form>
  )
}

function AccountRow({ account }: { account: Account }) {
  const { rename, remove } = useAccountMutations()
  const [mode, setMode] = useState<'view' | 'rename' | 'delete'>('view')
  const [name, setName] = useState(account.name)

  return (
    <li className="p-4">
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <div>
          <p className="font-semibold">{account.name}</p>
          <p className="text-sm text-ink-soft">
            {ACCOUNT_KIND_LABELS[account.kind]}, {plural(account.transaction_count, 'transaction', 'transactions')}
          </p>
        </div>
        <Amount value={account.balance} className="text-lg font-semibold" />
      </div>

      {mode === 'view' && (
        <div className="mt-2 flex gap-4 text-sm">
          <button type="button" className="font-semibold text-ink-soft hover:text-ink" onClick={() => setMode('rename')}>
            Rename
          </button>
          <button type="button" className="font-semibold text-ink-soft hover:text-over" onClick={() => setMode('delete')}>
            Delete
          </button>
        </div>
      )}

      {mode === 'rename' && (
        <form
          className="mt-3 flex flex-wrap items-center gap-2"
          onSubmit={(event) => {
            event.preventDefault()
            rename.mutate({ accountId: account.id, name: name.trim() }, { onSuccess: () => setMode('view') })
          }}
        >
          <input
            aria-label="New name"
            value={name}
            onChange={(event) => setName(event.target.value)}
            maxLength={60}
            className="min-h-9 rounded-lg border border-line px-2 text-sm focus:border-ink focus:outline-none"
          />
          <Button type="submit" size="small" disabled={!name.trim()} busy={rename.isPending}>
            Save name
          </Button>
          <Button variant="quiet" size="small" onClick={() => setMode('view')}>
            Cancel
          </Button>
        </form>
      )}

      {mode === 'delete' && (
        <div className="mt-3 flex flex-wrap items-center gap-3 text-sm">
          <span>
            This deletes {account.name} and its {plural(account.transaction_count, 'transaction', 'transactions')}.
          </span>
          <Button variant="danger" size="small" busy={remove.isPending} onClick={() => remove.mutate(account.id)}>
            Delete account
          </Button>
          <Button variant="quiet" size="small" onClick={() => setMode('view')}>
            Keep it
          </Button>
        </div>
      )}

      <ErrorNotice error={rename.error ?? remove.error} />
    </li>
  )
}

export function AccountsPage() {
  const { data, error } = useAccounts()

  return (
    <div>
      <PageHeader
        title="Accounts"
        description="One per bank account, card or wallet. Balances are worked out from the transactions, never typed in."
      />

      <ErrorNotice error={error} />

      {data && data.items.length > 0 && (
        <>
          <ul className="divide-y divide-line rounded-2xl bg-surface ring-1 ring-line">
            {data.items.map((account) => (
              <AccountRow key={account.id} account={account} />
            ))}
          </ul>
          <p className="mt-3 text-right text-sm text-ink-soft">
            All accounts together: <span className="figures font-semibold text-ink">{formatMoney(data.total_balance)}</span>
          </p>
        </>
      )}

      <section aria-labelledby="new-account" className="mt-12">
        <h2 id="new-account" className="mb-1 text-xl">
          New account
        </h2>
        <p className="mb-5 text-sm text-ink-soft">
          Then <Link to="/import" className="font-semibold underline">import a statement</Link> into it.
        </p>
        <NewAccountForm />
      </section>
    </div>
  )
}
