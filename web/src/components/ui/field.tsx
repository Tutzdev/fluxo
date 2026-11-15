import { forwardRef, type InputHTMLAttributes, type ReactNode, type SelectHTMLAttributes, useId } from 'react'

const control =
  'w-full min-h-11 rounded-lg border border-line bg-surface px-3 text-base text-ink placeholder:text-ink-soft/70 ' +
  'focus:border-ink focus:outline-none aria-invalid:border-over'

interface FieldProps {
  label: string
  error?: string
  hint?: ReactNode
  className?: string
}

/** A label, the control, and room for a hint or an error, wired together for screen readers. */
function FieldFrame({
  id,
  label,
  error,
  hint,
  className = '',
  children,
}: FieldProps & { id: string; children: ReactNode }) {
  return (
    <div className={`flex flex-col gap-1.5 ${className}`}>
      <label htmlFor={id} className="text-sm font-semibold">
        {label}
      </label>
      {children}
      {error ? (
        <p id={`${id}-message`} className="text-sm text-over">
          {error}
        </p>
      ) : (
        hint && (
          <p id={`${id}-message`} className="text-sm text-ink-soft">
            {hint}
          </p>
        )
      )}
    </div>
  )
}

export const TextField = forwardRef<HTMLInputElement, FieldProps & InputHTMLAttributes<HTMLInputElement>>(
  function TextField({ label, error, hint, className, ...input }, ref) {
    const id = useId()

    return (
      <FieldFrame id={id} label={label} error={error} hint={hint} className={className}>
        <input
          ref={ref}
          id={id}
          aria-invalid={Boolean(error) || undefined}
          aria-describedby={error || hint ? `${id}-message` : undefined}
          className={control}
          {...input}
        />
      </FieldFrame>
    )
  },
)

export const SelectField = forwardRef<HTMLSelectElement, FieldProps & SelectHTMLAttributes<HTMLSelectElement>>(
  function SelectField({ label, error, hint, className, children, ...select }, ref) {
    const id = useId()

    return (
      <FieldFrame id={id} label={label} error={error} hint={hint} className={className}>
        <select
          ref={ref}
          id={id}
          aria-invalid={Boolean(error) || undefined}
          aria-describedby={error || hint ? `${id}-message` : undefined}
          className={control}
          {...select}
        >
          {children}
        </select>
      </FieldFrame>
    )
  },
)
