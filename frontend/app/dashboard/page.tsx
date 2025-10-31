import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export default function DashboardPage() {
  return (
    <main className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Mission Control</h1>
          <p className="text-muted-foreground">Monitor and manage your autonomous coding agents</p>
        </div>
        <div className="flex gap-2">
          <Button>New Task</Button>
          <Link href="/">
            <Button variant="outline">Home</Button>
          </Link>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Active Tasks</CardTitle>
            <CardDescription>Currently running</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">0</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Completed Today</CardTitle>
            <CardDescription>+0% from yesterday</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">0</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            <CardDescription>Last 30 days</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">--%</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Cost Today</CardTitle>
            <CardDescription>AI model usage</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">$0.00</div>
          </CardContent>
        </Card>
      </div>
    </main>
  )
}
