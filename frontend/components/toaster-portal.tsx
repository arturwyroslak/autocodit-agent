'use client'

import { useToast } from '@/components/ui/use-toast'

export function ToasterPortal() {
  const { Toaster } = useToast()
  return <Toaster />
}
