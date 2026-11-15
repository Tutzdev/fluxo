import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Navigate, useNavigate } from 'react-router'
import { z } from 'zod'
import { Logo } from '@/components/app-shell'
import { Button } from '@/components/ui/button'
import { TextField } from '@/components/ui/field'
import { ErrorNotice } from '@/components/ui/notice'
import { useSession } from '@/features/auth/session'

interface SampleLine {
  description: string
  amount: string
  category: string
  decidedBy: string
  needsYou?: boolean
}

/** What happens to a statement inside Centavo, shown with lines like the ones a Brazilian bank exports. */
const SAMPLE_LINES: SampleLine[] = [
  { description: 'SALARIO ACME TECNOLOGIA', amount: '+R$ 6.800,00', category: 'Salary', decidedBy: 'Rule' },
  { description: 'IFOOD *IFOOD', amount: '−R$ 58,90', category: 'Restaurants', decidedBy: 'Rule' },
  { description: 'PREZUNIC TIJUCA', amount: '−R$ 212,40', category: 'Groceries', decidedBy: 'Learned 87%' },
  { description: 'BOTECO DO ZE', amount: '−R$ 96,00', category: 'Restaurants', decidedBy: 'Learned 74%' },
  { description: 'PAG*JOAOPAULOSOUZA', amount: '−R$ 80,00', category: 'Needs you', decidedBy: '', needsYou: true },
]

function StatementPreview() {
  return (
    <figure className="rounded-2xl bg-surface p-5 ring-1 ring-line sm:p-6">
      <figcaption className="mb-4 flex items-baseline justify-between text-sm text-ink-soft">
        <span className="font-semibold text-ink">Your statement, sorted</span>
        <span>November</span>
      </figcaption>
      <ul className="divide-y divide-line">
        {SAMPLE_LINES.map((line, index) => (
          <li key={line.description} className="grid grid-cols-[1fr_auto] gap-x-4 gap-y-1 py-3">
            <span className="truncate text-sm font-semibold tracking-wide">{line.description}</span>
            <span className={`figures text-right text-sm ${line.amount.startsWith('+') ? 'text-income' : ''}`}>
              {line.amount}
            </span>
            <span className="resolve flex items-center gap-2 text-sm" style={{ animationDelay: `${300 + index * 180}ms` }}>
              {line.needsYou ? (
                <span className="rounded-full bg-brass-soft px-2 py-0.5 text-xs font-semibold text-brass-deep">
                  Needs you: one click teaches Centavo
                </span>
              ) : (
                <>
                  <span className="text-ink">{line.category}</span>
                  <span
                    className={
                      line.decidedBy.startsWith('Learned')
                        ? 'rounded-full px-2 py-0.5 text-xs font-semibold text-brass-deep ring-1 ring-inset ring-brass/50'
                        : 'text-xs text-ink-soft'
                    }
                  >
                    {line.decidedBy}
                  </span>
                </>
              )}
            </span>
          </li>
        ))}
      </ul>
    </figure>
  )
}

const signInSchema = z.object({
  email: z.email('Type the e-mail you signed up with.'),
  password: z.string().min(1, 'Type your password.'),
})

const signUpSchema = z.object({
  name: z.string().trim().min(1, 'Tell us what to call you.').max(80),
  email: z.email('Type a valid e-mail.'),
  password: z.string().min(10, 'Use at least 10 characters.').max(128),
})

type SignInValues = z.infer<typeof signInSchema>
type SignUpValues = z.infer<typeof signUpSchema>

function SignInForm() {
  const { signIn } = useSession()
  const navigate = useNavigate()
  const [error, setError] = useState<unknown>(null)
  const form = useForm<SignInValues>({ resolver: zodResolver(signInSchema) })

  const submit = form.handleSubmit(async ({ email, password }) => {
    setError(null)
    try {
      await signIn(email, password)
      navigate('/')
    } catch (caught) {
      setError(caught)
    }
  })

  return (
    <form onSubmit={submit} className="flex flex-col gap-4" noValidate>
      <TextField label="E-mail" type="email" autoComplete="email" error={form.formState.errors.email?.message} {...form.register('email')} />
      <TextField
        label="Password"
        type="password"
        autoComplete="current-password"
        error={form.formState.errors.password?.message}
        {...form.register('password')}
      />
      <ErrorNotice error={error} />
      <Button type="submit" busy={form.formState.isSubmitting}>
        Sign in
      </Button>
    </form>
  )
}

function SignUpForm() {
  const { signUp } = useSession()
  const navigate = useNavigate()
  const [error, setError] = useState<unknown>(null)
  const form = useForm<SignUpValues>({ resolver: zodResolver(signUpSchema) })

  const submit = form.handleSubmit(async ({ name, email, password }) => {
    setError(null)
    try {
      await signUp(name, email, password)
      navigate('/accounts')
    } catch (caught) {
      setError(caught)
    }
  })

  return (
    <form onSubmit={submit} className="flex flex-col gap-4" noValidate>
      <TextField label="Your name" autoComplete="given-name" error={form.formState.errors.name?.message} {...form.register('name')} />
      <TextField label="E-mail" type="email" autoComplete="email" error={form.formState.errors.email?.message} {...form.register('email')} />
      <TextField
        label="Password"
        type="password"
        autoComplete="new-password"
        hint="At least 10 characters."
        error={form.formState.errors.password?.message}
        {...form.register('password')}
      />
      <ErrorNotice error={error} />
      <Button type="submit" busy={form.formState.isSubmitting}>
        Create account
      </Button>
    </form>
  )
}

function DemoButton() {
  const { startDemo } = useSession()
  const navigate = useNavigate()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<unknown>(null)

  const start = async () => {
    setBusy(true)
    setError(null)
    try {
      await startDemo()
      navigate('/')
    } catch (caught) {
      setError(caught)
      setBusy(false)
    }
  }

  return (
    <div className="flex flex-col gap-3">
      <Button variant="brass" busy={busy} onClick={start} className="w-full sm:w-auto">
        Try it with six months of sample data
      </Button>
      <p className="text-sm text-ink-soft">A private demo account, deleted after a day. No sign-up needed.</p>
      <ErrorNotice error={error} />
    </div>
  )
}

export function WelcomePage() {
  const { user } = useSession()
  const [mode, setMode] = useState<'sign-in' | 'sign-up'>('sign-in')

  if (user) {
    return <Navigate to="/" replace />
  }

  return (
    <div className="mx-auto grid min-h-dvh max-w-6xl gap-12 px-4 py-8 sm:px-8 lg:grid-cols-[1.2fr_1fr] lg:items-center lg:py-16">
      <section className="flex flex-col gap-8">
        <Logo />
        <div className="max-w-xl">
          <h1 className="text-3xl sm:text-4xl">Your bank statement, sorted.</h1>
          <p className="mt-4 text-lg text-ink-soft">
            Import the CSV or OFX your bank gives you. Centavo files every line under a category, learns from each
            correction you make, and tells you how the month is going to end.
          </p>
        </div>
        <StatementPreview />
        <DemoButton />
      </section>

      <section className="rounded-2xl bg-surface p-6 ring-1 ring-line sm:p-8" aria-label="Your account">
        <div className="mb-6 grid grid-cols-2 rounded-lg bg-paper p-1" role="tablist">
          {(['sign-in', 'sign-up'] as const).map((option) => (
            <button
              key={option}
              type="button"
              role="tab"
              aria-selected={mode === option}
              onClick={() => setMode(option)}
              className={`rounded-md py-2 text-sm font-semibold ${mode === option ? 'bg-surface shadow-sm' : 'text-ink-soft'}`}
            >
              {option === 'sign-in' ? 'Sign in' : 'Create account'}
            </button>
          ))}
        </div>
        {mode === 'sign-in' ? <SignInForm /> : <SignUpForm />}
      </section>
    </div>
  )
}
