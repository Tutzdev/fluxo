import * as RadixDialog from '@radix-ui/react-dialog'
import { X } from 'lucide-react'
import type { ReactNode } from 'react'

interface DialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  description?: string
  children: ReactNode
}

export function Dialog({ open, onOpenChange, title, description, children }: DialogProps) {
  return (
    <RadixDialog.Root open={open} onOpenChange={onOpenChange}>
      <RadixDialog.Portal>
        <RadixDialog.Overlay className="fixed inset-0 z-40 bg-ink/40" />
        <RadixDialog.Content
          className="fixed inset-x-4 top-[10vh] z-50 mx-auto max-w-lg rounded-2xl bg-surface p-6 shadow-[0_24px_60px_-20px_rgba(18,52,59,0.45)]"
          // Radix links the description by itself; without one, it is told there is none on purpose.
          {...(description ? {} : { 'aria-describedby': undefined })}
        >
          <div className="mb-5 flex items-start justify-between gap-4">
            <div>
              <RadixDialog.Title className="font-display text-xl font-semibold">{title}</RadixDialog.Title>
              {description && (
                <RadixDialog.Description className="mt-1 text-sm text-ink-soft">{description}</RadixDialog.Description>
              )}
            </div>
            <RadixDialog.Close className="rounded-md p-1 text-ink-soft hover:text-ink" aria-label="Close">
              <X aria-hidden className="size-5" />
            </RadixDialog.Close>
          </div>
          {children}
        </RadixDialog.Content>
      </RadixDialog.Portal>
    </RadixDialog.Root>
  )
}
