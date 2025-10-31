import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { getJSON } from '@/lib/api'

async function fetchTasks() {
  try {
    const data = await getJSON<{ items?: any[]; data?: any[] }>('/api/v1/tasks')
    // Backend może zwrócić {items:[...]} lub tablicę; normalizujemy
    const items = Array.isArray(data) ? (data as any) : (data.items || data.data || [])
    return items
  } catch (e) {
    return []
  }
}

function statusVariant(s?: string) {
  switch ((s || '').toLowerCase()) {
    case 'running':
      return 'default'
    case 'queued':
      return 'secondary'
    case 'completed':
      return 'outline'
    case 'failed':
      return 'destructive'
    default:
      return 'secondary'
  }
}

export default async function TaskOverview() {
  const tasks = await fetchTasks()

  return (
    <div className="rounded-lg border bg-card">
      <div className="p-4 border-b">
        <h2 className="text-lg font-semibold">Recent Tasks</h2>
      </div>
      <div className="p-4">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Title</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Progress</TableHead>
              <TableHead>Repository</TableHead>
              <TableHead className="text-right">Created</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {tasks.map((t: any) => (
              <TableRow key={t.id}>
                <TableCell className="font-mono text-xs">{t.id?.slice(0,8)}</TableCell>
                <TableCell>{t.title}</TableCell>
                <TableCell>
                  <Badge variant={statusVariant(t.status)}>{t.status}</Badge>
                </TableCell>
                <TableCell>{Math.round((t.progress || 0) * 100)}%</TableCell>
                <TableCell>{t.repository || t.repository_name || '-'}</TableCell>
                <TableCell className="text-right text-muted-foreground">
                  {t.created_at ? new Date(t.created_at).toLocaleString() : '-'}
                </TableCell>
              </TableRow>
            ))}
            {tasks.length === 0 && (
              <TableRow>
                <TableCell colSpan={6} className="text-center text-muted-foreground">No tasks found</TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
