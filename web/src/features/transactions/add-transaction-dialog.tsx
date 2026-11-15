import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { Button } from '@/components/ui/button'
import { Dialog } from '@/components/ui/dialog'
import { SelectField, TextField } from '@/components/ui/field'
import { ErrorNotice } from '@/components/ui/notice'
import { useAccounts } from '@/features/accounts/queries'
import { CategorySelect } from '@/features/categories/category-select'
import { useTransactionMutations } from '@/features/transactions/queries'

const schema = z.object({
  account_id: z.coerce.number<string>().int().positive('Choose an account.'),
  occurred_on: z.iso.date('Choose a date.'),
  description: z.string().trim().min(1, 'Describe it, like the bank would.').max(200),
  direction: z.enum(['out', 'in']),
  amount: z
    .string()
    .trim()
    .regex(/^\d{1,12}([.,]\d{1,2})?$/, 'Type an amount like 45,90.')
    .refine((value) => Number(value.replace(',', '.')) > 0, 'The amount must be more than zero.'),
  category_id: z.number().nullable(),
})

type Values = z.input<typeof schema>
type Parsed = z.output<typeof schema>

interface AddTransactionDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function AddTransactionDialog({ open, onOpenChange }: AddTransactionDialogProps) {
  const { data: accounts } = useAccounts()
  const { create } = useTransactionMutations()
  const today = new Date().toISOString().slice(0, 10)

  const form = useForm<Values, unknown, Parsed>({
    resolver: zodResolver(schema),
    defaultValues: { account_id: '', occurred_on: today, description: '', direction: 'out', amount: '', category_id: null },
  })

  const submit = form.handleSubmit((values) => {
    const magnitude = values.amount.replace(',', '.')

    create.mutate(
      {
        account_id: values.account_id,
        occurred_on: values.occurred_on,
        description: values.description,
        amount: values.direction === 'out' ? `-${magnitude}` : magnitude,
        category_id: values.category_id,
      },
      {
        onSuccess: () => {
          form.reset()
          onOpenChange(false)
        },
      },
    )
  })

  const errors = form.formState.errors

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title="Add a transaction"
      description="For cash and anything your bank statement does not show. Leave the category empty and Centavo will try."
    >
      <form onSubmit={submit} className="flex flex-col gap-4" noValidate>
        <SelectField label="Account" error={errors.account_id?.message} {...form.register('account_id')}>
          <option value="">Choose an account</option>
          {accounts?.items.map((account) => (
            <option key={account.id} value={account.id}>
              {account.name}
            </option>
          ))}
        </SelectField>

        <div className="grid gap-4 sm:grid-cols-2">
          <TextField label="Date" type="date" error={errors.occurred_on?.message} {...form.register('occurred_on')} />
          <SelectField label="Money" {...form.register('direction')}>
            <option value="out">Went out</option>
            <option value="in">Came in</option>
          </SelectField>
        </div>

        <TextField label="Description" placeholder="Feira de domingo" error={errors.description?.message} {...form.register('description')} />
        <TextField label="Amount (R$)" inputMode="decimal" placeholder="45,90" error={errors.amount?.message} {...form.register('amount')} />

        <div className="flex flex-col gap-1.5">
          <span className="text-sm font-semibold">Category</span>
          <CategorySelect
            aria-label="Category"
            value={form.watch('category_id')}
            onChange={(categoryId) => form.setValue('category_id', categoryId)}
            emptyLabel="Let Centavo decide"
            className="min-h-11"
          />
        </div>

        <ErrorNotice error={create.error} />
        <Button type="submit" busy={create.isPending}>
          Add transaction
        </Button>
      </form>
    </Dialog>
  )
}
