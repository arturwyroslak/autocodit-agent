import * as React from 'react'
import { cn } from '@/components/lib/utils'

export function Badge({ className, variant = 'default', ...props }: React.HTMLAttributes<HTMLSpanElement> & { variant?: 'default' | 'secondary' | 'destructive' | 'outline' }) {
  const variants: Record<string, string> = {
    default: 'bg-primary text-primary-foreground shadow',
    secondary: 'bg-secondary text-secondary-foreground',
    destructive: 'bg-destructive text-destructive-foreground shadow',
    outline: 'text-foreground border',
  }
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors',
        variants[variant],
        className
      )}
      {...props}
    />
  )
}
