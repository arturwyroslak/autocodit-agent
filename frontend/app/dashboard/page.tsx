'use client'

import * as React from 'react'
import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Sparkles, GitBranch, FileText, Loader2 } from 'lucide-react'
import { postJSON } from '@/lib/api'
import { useToast } from '@/components/ui/use-toast'

// Mock data - replace with API calls
const mockRepositories = [
  'arturwyroslak/autocodit-agent',
  'arturwyroslak/project-alpha',
  'arturwyroslak/project-beta',
]

const mockBranches = {
  'arturwyroslak/autocodit-agent': ['main', 'develop', 'feature/ui-improvements'],
  'arturwyroslak/project-alpha': ['main', 'staging', 'production'],
  'arturwyroslak/project-beta': ['main', 'dev'],
}

export default function DashboardPage() {
  const [selectedRepo, setSelectedRepo] = useState('')
  const [selectedBranch, setSelectedBranch] = useState('')
  const [description, setDescription] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const { add } = useToast()

  const availableBranches = selectedRepo ? mockBranches[selectedRepo as keyof typeof mockBranches] || [] : []

  async function handleCreateTask(e: React.FormEvent) {
    e.preventDefault()
    if (!selectedRepo || !selectedBranch || !description) {
      add({
        title: 'Validation Error',
        description: 'Please fill in all fields',
        variant: 'destructive',
      })
      return
    }

    setSubmitting(true)
    try {
      await postJSON('/api/v1/tasks', {
        title: `Task for ${selectedRepo}`,
        description,
        repository: selectedRepo,
        branch: selectedBranch,
        action_type: 'plan',
        priority: 'normal',
      })
      add({
        title: 'Task Created',
        description: `Task created for ${selectedRepo} on ${selectedBranch}`,
      })
      setDescription('')
      // Optionally refresh the page or task list
      setTimeout(() => {
        if (typeof window !== 'undefined') window.location.reload()
      }, 1000)
    } catch (e: any) {
      add({
        title: 'Failed to create task',
        description: e?.message || 'An error occurred',
        variant: 'destructive',
      })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Hero Section */}
      <div className="border-b bg-gradient-to-br from-card to-card/50 backdrop-blur-sm">
        <div className="container mx-auto px-6 py-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 rounded-lg bg-primary/10">
              <Sparkles className="w-6 h-6 text-primary" />
            </div>
            <h1 className="text-3xl font-bold gradient-text">Mission Control</h1>
          </div>
          <p className="text-muted-foreground text-lg">Create and manage autonomous coding tasks</p>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-6 py-8">
        <div className="max-w-3xl mx-auto">
          <Card className="shadow-lg border-2">
            <CardHeader className="space-y-1 pb-6">
              <CardTitle className="text-2xl flex items-center gap-2">
                <div className="p-2 rounded-lg bg-gradient-to-br from-primary/20 to-primary/10">
                  <FileText className="w-5 h-5 text-primary" />
                </div>
                Create New Task
              </CardTitle>
              <CardDescription className="text-base">
                Select a repository, branch, and describe what you want the agent to do
              </CardDescription>
            </CardHeader>
            
            <CardContent>
              <form onSubmit={handleCreateTask} className="space-y-6">
                {/* Repository Selection */}
                <div className="space-y-2">
                  <label className="text-sm font-medium flex items-center gap-2">
                    <GitBranch className="w-4 h-4" />
                    Repository
                    <span className="text-destructive">*</span>
                  </label>
                  <Select value={selectedRepo} onValueChange={(value) => {
                    setSelectedRepo(value)
                    setSelectedBranch('') // Reset branch when repo changes
                  }}>
                    <SelectTrigger className="h-12">
                      <SelectValue placeholder="Select a repository" />
                    </SelectTrigger>
                    <SelectContent>
                      {mockRepositories.map((repo) => (
                        <SelectItem key={repo} value={repo}>
                          {repo}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Branch Selection */}
                <div className="space-y-2">
                  <label className="text-sm font-medium flex items-center gap-2">
                    <GitBranch className="w-4 h-4" />
                    Branch
                    <span className="text-destructive">*</span>
                  </label>
                  <Select 
                    value={selectedBranch} 
                    onValueChange={setSelectedBranch}
                    disabled={!selectedRepo}
                  >
                    <SelectTrigger className="h-12">
                      <SelectValue placeholder={selectedRepo ? "Select a branch" : "Select repository first"} />
                    </SelectTrigger>
                    <SelectContent>
                      {availableBranches.map((branch) => (
                        <SelectItem key={branch} value={branch}>
                          {branch}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Task Description */}
                <div className="space-y-2">
                  <label className="text-sm font-medium flex items-center gap-2">
                    <FileText className="w-4 h-4" />
                    Task Description
                    <span className="text-destructive">*</span>
                  </label>
                  <textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Describe what you want the agent to do...\n\nExample:\n- Fix the authentication bug in the login page\n- Add dark mode support to the dashboard\n- Optimize database queries for better performance"
                    className="w-full min-h-[200px] px-4 py-3 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring resize-none"
                    required
                  />
                  <p className="text-xs text-muted-foreground">
                    Be specific and clear about what you want to achieve
                  </p>
                </div>

                {/* Submit Button */}
                <div className="flex justify-end gap-3 pt-4">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => {
                      setSelectedRepo('')
                      setSelectedBranch('')
                      setDescription('')
                    }}
                    disabled={submitting}
                  >
                    Clear
                  </Button>
                  <Button
                    type="submit"
                    disabled={submitting || !selectedRepo || !selectedBranch || !description}
                    className="min-w-32 gap-2"
                    size="lg"
                  >
                    {submitting ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Creating...
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-4 h-4" />
                        Create Task
                      </>
                    )}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>

          {/* Info Cards */}
          <div className="grid md:grid-cols-3 gap-4 mt-8">
            <Card className="card-hover">
              <CardHeader>
                <CardTitle className="text-sm font-medium text-muted-foreground">Quick Tips</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm">Be specific about the task you want to accomplish</p>
              </CardContent>
            </Card>
            <Card className="card-hover">
              <CardHeader>
                <CardTitle className="text-sm font-medium text-muted-foreground">Best Practices</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm">Include context and expected outcomes in your description</p>
              </CardContent>
            </Card>
            <Card className="card-hover">
              <CardHeader>
                <CardTitle className="text-sm font-medium text-muted-foreground">Need Help?</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm">Check the documentation for example tasks and patterns</p>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
