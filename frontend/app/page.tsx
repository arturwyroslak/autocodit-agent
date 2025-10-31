import Link from 'next/link'
import { Button } from '@/components/ui/button'

export default function Page() {
  return (
    <main className="p-6 space-y-4">
      <h1 className="text-2xl font-bold">AutoCodit Agent</h1>
      <p className="text-muted-foreground">Mission Control Dashboard is available.</p>
      <Link href="/dashboard"><Button>Open Dashboard</Button></Link>
    </main>
  )
}
