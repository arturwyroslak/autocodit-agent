import './globals.css'
import type { Metadata } from 'next'
import { useToast } from '@/components/ui/use-toast'

export const metadata: Metadata = {
  title: 'AutoCodit Agent',
  description: 'Mission Control Dashboard',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  // Client hook cannot be used in a server component, so render Toaster in a client subcomponent
  return (
    <html lang="en">
      <body>
        {children}
        {/* Client-only toaster */}
        <ToasterPortal />
      </body>
    </html>
  )
}

'use client'
function ToasterPortal() {
  const { Toaster } = useToast()
  return <Toaster />
}
