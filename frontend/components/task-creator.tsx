'use client'

import * as React from 'react'
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { postJSON } from '@/lib/api'
import { useToast } from '@/components/ui/use-toast'

export default function TaskCreator() {
  const [open, setOpen] = useState(false)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [repository, setRepository] = useState('')
  const [actionType, setActionType] = useState('plan')
  const [priority, setPriority] = useState('normal')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { add } = useToast()

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      await postJSON('/api/v1/tasks', {
        title: title || `${actionType} task`,
        description,
        repository,
        action_type: actionType,
        priority,
      })
      add({ title: 'Task created', description: `${actionType} – ${repository}` })
      setOpen(false)
      setTitle(''); setDescription(''); setRepository('')
      // try to refresh task lists by reloading location (simple approach)
      if (typeof window !== 'undefined') window.location.reload()
    } catch (e: any) {
      setError(e?.message || 'Failed to create task')
      add({ title: 'Failed to create task', description: e?.message || '', variant: 'destructive' })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="rounded-lg border p-4 bg-card">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Create Task</h3>
        <Button onClick={() => setOpen(!open)} variant={open ? 'outline' : 'default'}>
          {open ? 'Close' : 'New Task'}
        </Button>
      </div>
      {open && (
        <form onSubmit={onSubmit} className="mt-4 space-y-3">
          <div>
            <label className="block text-sm mb-1">Repository (owner/name)</label>
            <Input value={repository} onChange={e => setRepository(e.target.value)} required placeholder="org/repo" />
          </div>
          <div>
            <label className="block text-sm mb-1">Title</label>
            <Input value={title} onChange={e => setTitle(e.target.value)} placeholder="Short title" />
          </div>
          <div>
            <label className="block text-sm mb-1">Description</label>
            <Input value={description} onChange={e => setDescription(e.target.value)} placeholder="What should the agent do?" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm mb-1">Action Type</label>
              <Input value={actionType} onChange={e => setActionType(e.target.value)} placeholder="plan|apply|fix|review|test" />
            </div>
            <div>
              <label className="block text-sm mb-1">Priority</label>
              <Input value={priority} onChange={e => setPriority(e.target.value)} placeholder="low|normal|high|urgent" />
            </div>
          </div>
          {error && <p className="text-sm text-destructive">{error}</p>}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
            <Button type="submit" disabled={submitting}>{submitting ? 'Submitting...' : 'Create'}</Button>
          </div>
        </form>
      )}
    </div>
  )
}
