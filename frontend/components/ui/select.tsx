'use client'
import * as React from 'react'
import { cn } from '@/lib/utils'
import { ChevronDown } from 'lucide-react'

export interface SimpleSelectProps {
  value: string
  onChange: (value: string) => void
  options: { label: string; value: string }[]
  disabled?: boolean
  placeholder?: string
  className?: string
}

export function SimpleSelect({ value, onChange, options, disabled, placeholder, className }: SimpleSelectProps) {
  return (
    <div className={cn('relative', className)}>
      <select
        className={cn(
          'w-full appearance-none h-12 rounded-md border bg-background text-sm px-4 pr-10 py-2 focus:outline-none focus:ring-2 focus:ring-ring disabled:cursor-not-allowed disabled:opacity-50',
          className
        )}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
      >
        <option value="">{placeholder || 'Select an option'}</option>
        {options.map((opt) => (
          <option value={opt.value} key={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
    </div>
  )
}
