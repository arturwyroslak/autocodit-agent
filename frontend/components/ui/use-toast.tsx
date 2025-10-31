'use client'

import * as React from 'react'
import { Button } from '@/components/ui/button'

export function useToast() {
  const [toasts, setToasts] = React.useState<{ id: number; title: string; description?: string; variant?: 'default' | 'destructive' }[]>([])
  const add = (t: Omit<(typeof toasts)[number], 'id'>) => setToasts(prev => [...prev, { id: Date.now(), ...t }])
  const remove = (id: number) => setToasts(prev => prev.filter(t => t.id !== id))
  return {
    add,
    remove,
    Toaster: () => (
      <div className="fixed bottom-4 right-4 space-y-2 z-50">
        {toasts.map(t => (
          <div key={t.id} className={`rounded-md border p-3 shadow bg-card ${t.variant === 'destructive' ? 'border-destructive text-destructive-foreground' : ''}`}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="font-medium">{t.title}</div>
                {t.description && <div className="text-sm text-muted-foreground">{t.description}</div>}
              </div>
              <Button size="sm" variant="ghost" onClick={() => remove(t.id)}>Close</Button>
            </div>
          </div>
        ))}
      </div>
    )
  }
}
