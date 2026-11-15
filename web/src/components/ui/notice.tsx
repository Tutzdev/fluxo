import { CircleAlert, CircleCheck } from 'lucide-react'
import type { ReactNode } from 'react'
import { ApiError } from '@/lib/api'

type Tone = 'error' | 'success' | 'info'

const tones: Record<Tone, string> = {
  error: 'border-over/30 bg-over/5 text-over',
  success: 'border-income/30 bg-income/5 text-income',
  info: 'border-line bg-surface text-ink',
}

export function Notice({ tone = 'info', children }: { tone?: Tone; children: ReactNode }) {
  const Icon = tone === 'success' ? CircleCheck : CircleAlert

  return (
    <div role={tone === 'error' ? 'alert' : 'status'} className={`flex gap-2 rounded-lg border px-3 py-2.5 text-sm ${tones[tone]}`}>
      {tone !== 'info' && <Icon aria-hidden className="mt-0.5 size-4 shrink-0" />}
      <div>{children}</div>
    </div>
  )
}

/** The server's own explanation when there is one; a plain one for a dropped connection. */
export function ErrorNotice({ error }: { error: unknown }) {
  if (!error) {
    return null
  }

  const message =
    error instanceof ApiError ? error.message : 'Could not reach Fluxo. Check your connection and try again.'
  return <Notice tone="error">{message}</Notice>
}
