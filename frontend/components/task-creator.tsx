'use client'

import * as React from 'react'
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { postJSON } from '@/lib/api'
import { useToast } from '@/components/ui/use-toast'
import { Plus, X, Sparkles } from 'lucide-react'

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
    <div className="rounded-xl border bg-gradient-to-br from-card to-card/50 backdrop-blur-sm shadow-lg overflow-hidden">
      <div className="p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/10">
              <Sparkles className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h3 className="text-xl font-semibold">Create Task</h3>
              <p className="text-sm text-muted-foreground">Deploy a new autonomous agent</p>
            </div>
          </div>
          <Button 
            onClick={() => setOpen(!open)} 
            variant={open ? 'outline' : 'default'}
            className="gap-2"
          >
            {open ? (
              <>
                <X className="w-4 h-4" />
                Close
              </>
            ) : (
              <>
                <Plus className="w-4 h-4" />
                New Task
              </>
            )}
          </Button>
        </div>
        
        {open && (
          <form onSubmit={onSubmit} className="mt-6 space-y-5 animate-slide-up">
            <div className="space-y-2">
              <label className="text-sm font-medium flex items-center gap-2">
                Repository
                <span className="text-destructive">*</span>
              </label>
              <Input 
                value={repository} 
                onChange={e => setRepository(e.target.value)} 
                required 
                placeholder="e.g. owner/repository-name"
                className="h-11 bg-background/50"
              />
              <p className="text-xs text-muted-foreground">GitHub repository in format: owner/name</p>
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium">Task Title</label>
              <Input 
                value={title} 
                onChange={e => setTitle(e.target.value)} 
                placeholder="Brief description of the task"
                className="h-11 bg-background/50"
              />
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium">Description</label>
              <Input 
                value={description} 
                onChange={e => setDescription(e.target.value)} 
                placeholder="What should the agent do?"
                className="h-11 bg-background/50"
              />
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Action Type</label>
                <select
                  value={actionType}
                  onChange={e => setActionType(e.target.value)}
                  className="w-full h-11 px-3 rounded-md border bg-background/50 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                >
                  <option value="plan">Plan</option>
                  <option value="apply">Apply</option>
                  <option value="fix">Fix</option>
                  <option value="review">Review</option>
                  <option value="test">Test</option>
                </select>
              </div>
              
              <div className="space-y-2">
                <label className="text-sm font-medium">Priority</label>
                <select
                  value={priority}
                  onChange={e => setPriority(e.target.value)}
                  className="w-full h-11 px-3 rounded-md border bg-background/50 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                >
                  <option value="low">Low</option>
                  <option value="normal">Normal</option>
                  <option value="high">High</option>
                  <option value="urgent">Urgent</option>
                </select>
              </div>
            </div>
            
            {error && (
              <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20">
                <p className="text-sm text-destructive">{error}</p>
              </div>
            )}
            
            <div className="flex justify-end gap-3 pt-2">
              <Button 
                type="button" 
                variant="outline" 
                onClick={() => setOpen(false)}
                className="min-w-24"
              >
                Cancel
              </Button>
              <Button 
                type="submit" 
                disabled={submitting}
                className="min-w-32 gap-2"
              >
                {submitting ? (
                  <>
                    <div className="w-4 h-4 border-2 border-background/30 border-t-background rounded-full animate-spin" />
                    Creating...
                  </>
                ) : (
                  <>
                    <Plus className="w-4 h-4" />
                    Create Task
                  </>
                )}
              </Button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
