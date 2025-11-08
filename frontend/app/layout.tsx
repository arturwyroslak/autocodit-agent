import './globals.css'
import type { Metadata } from 'next'
import { ToasterPortal } from '@/components/toaster-portal'

export const metadata: Metadata = {
  title: 'AutoCodit Agent',
  description: 'Mission Control Dashboard',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        {children}
        <ToasterPortal />
      </body>
    </html>
  )
}
