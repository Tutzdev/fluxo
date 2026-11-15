import { LoaderCircle } from 'lucide-react'
import type { ButtonHTMLAttributes } from 'react'

type Variant = 'primary' | 'quiet' | 'danger' | 'brass'
type Size = 'normal' | 'small'

const variants: Record<Variant, string> = {
  primary: 'bg-ink text-paper hover:bg-ink/90 disabled:bg-line disabled:text-ink-soft',
  quiet: 'bg-transparent text-ink ring-1 ring-inset ring-line hover:bg-surface hover:ring-ink-soft',
  danger: 'bg-transparent text-over ring-1 ring-inset ring-over/40 hover:bg-over/5',
  brass: 'bg-brass text-ink hover:bg-brass/85 disabled:bg-line disabled:text-ink-soft',
}

const sizes: Record<Size, string> = {
  normal: 'min-h-11 px-5 text-base',
  small: 'min-h-9 px-3 text-sm',
}

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
  busy?: boolean
}

export function Button({
  variant = 'primary',
  size = 'normal',
  busy = false,
  disabled,
  className = '',
  type = 'button',
  children,
  ...rest
}: ButtonProps) {
  return (
    <button
      {...rest}
      type={type}
      disabled={disabled || busy}
      aria-busy={busy || undefined}
      className={`inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-colors
        disabled:cursor-not-allowed ${variants[variant]} ${sizes[size]} ${className}`}
    >
      {busy && <LoaderCircle aria-hidden className="size-4 animate-spin motion-reduce:animate-none" />}
      {children}
    </button>
  )
}
