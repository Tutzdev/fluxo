import { FileUp } from 'lucide-react'
import { type FormEvent, useState } from 'react'
import { Link } from 'react-router'
import { Button } from '@/components/ui/button'
import { SelectField } from '@/components/ui/field'
import { ErrorNotice, Notice } from '@/components/ui/notice'
import { PageHeader } from '@/components/ui/page-header'
import { useAccounts } from '@/features/accounts/queries'
import { useImportStatement, useRecentImports } from '@/features/imports/queries'
import { formatDay, plural } from '@/lib/format'
import type { StatementImport } from '@/lib/types'

function ImportResult({ result }: { result: StatementImport }) {
  const waiting = result.imported_count - result.categorized_count

  return (
    <Notice tone="success">
      <p>
        {plural(result.imported_count, 'new transaction', 'new transactions')} from {result.filename}
        {result.duplicate_count > 0 && `, ${plural(result.duplicate_count, 'line was', 'lines were')} already in Fluxo and skipped`}.{' '}
        {result.categorized_count} got a category right away.
      </p>
      {waiting > 0 && (
        <p className="mt-1">
          <Link to="/review" className="font-semibold underline">
            {plural(waiting, 'transaction needs', 'transactions need')} you
          </Link>
        </p>
      )}
    </Notice>
  )
}

export function ImportPage() {
  const { data: accounts } = useAccounts()
  const recent = useRecentImports()
  const importStatement = useImportStatement()

  const [accountId, setAccountId] = useState<number | null>(null)
  const [file, setFile] = useState<File | null>(null)
  const [invert, setInvert] = useState(false)
  const [dragging, setDragging] = useState(false)

  const accountName = (id: number) => accounts?.items.find((account) => account.id === id)?.name ?? ''

  const chooseAccount = (id: number | null) => {
    setAccountId(id)
    // Card exports usually list purchases as positive numbers; a good default, still the person's call.
    setInvert(accounts?.items.find((account) => account.id === id)?.kind === 'credit_card')
  }

  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (accountId && file) {
      importStatement.mutate({ accountId, file, invert }, { onSuccess: () => setFile(null) })
    }
  }

  if (accounts && accounts.items.length === 0) {
    return (
      <div>
        <PageHeader title="Import a statement" />
        <p className="rounded-2xl bg-surface p-8 ring-1 ring-line">
          First tell Fluxo which account the statement belongs to.{' '}
          <Link to="/accounts" className="font-semibold underline">
            Add an account
          </Link>
        </p>
      </div>
    )
  }

  return (
    <div>
      <PageHeader
        title="Import a statement"
        description="A CSV or OFX file from your bank's app or website. Importing the same period twice is fine: lines already in Fluxo are skipped."
      />

      <form onSubmit={submit} className="flex max-w-2xl flex-col gap-5">
        <SelectField
          label="Account"
          value={accountId ?? ''}
          onChange={(event) => chooseAccount(event.target.value ? Number(event.target.value) : null)}
        >
          <option value="">Choose the account this statement is from</option>
          {accounts?.items.map((account) => (
            <option key={account.id} value={account.id}>
              {account.name}
            </option>
          ))}
        </SelectField>

        <label
          onDragOver={(event) => {
            event.preventDefault()
            setDragging(true)
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(event) => {
            event.preventDefault()
            setDragging(false)
            setFile(event.dataTransfer.files[0] ?? null)
          }}
          className={`flex cursor-pointer flex-col items-center gap-2 rounded-2xl border-2 border-dashed px-6 py-10 text-center transition-colors ${
            dragging ? 'border-brass bg-brass-soft' : 'border-line bg-surface hover:border-ink-soft'
          }`}
        >
          <FileUp aria-hidden className="size-7 text-ink-soft" />
          <span className="font-semibold">{file ? file.name : 'Drop the file here or choose it'}</span>
          <span className="text-sm text-ink-soft">CSV (Nubank, most banks) or OFX, up to 2 MB</span>
          <input
            type="file"
            accept=".csv,.ofx,text/csv"
            className="sr-only"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          />
        </label>

        <label className="flex items-start gap-3 text-sm">
          <input type="checkbox" checked={invert} onChange={(event) => setInvert(event.target.checked)} className="mt-1 size-4 accent-ink" />
          <span>
            <span className="font-semibold">Purchases are positive numbers in this file</span>
            <span className="block text-ink-soft">Common in credit card exports. Fluxo flips them so spending is negative everywhere.</span>
          </span>
        </label>

        <ErrorNotice error={importStatement.error} />
        {importStatement.data && <ImportResult result={importStatement.data} />}

        <Button type="submit" disabled={!accountId || !file} busy={importStatement.isPending} className="self-start">
          Import statement
        </Button>
      </form>

      {recent.data && recent.data.length > 0 && (
        <section aria-labelledby="recent-imports" className="mt-12">
          <h2 id="recent-imports" className="mb-4 text-xl">
            Recent imports
          </h2>
          <ul className="divide-y divide-line rounded-2xl bg-surface ring-1 ring-line">
            {recent.data.map((item) => (
              <li key={item.id} className="flex flex-wrap items-baseline justify-between gap-2 p-4 text-sm">
                <span>
                  <span className="font-semibold">{item.filename}</span>{' '}
                  <span className="text-ink-soft">
                    into {accountName(item.account_id)}, {formatDay(item.created_at.slice(0, 10))}
                  </span>
                </span>
                <span className="figures text-ink-soft">
                  {item.imported_count} new, {item.duplicate_count} skipped
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  )
}
