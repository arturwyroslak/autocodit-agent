import { Sidebar } from '@/components/sidebar'
import { TasksSidebar } from '@/components/tasks-sidebar'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="flex h-screen overflow-hidden">
      {/* Left Sidebar - Navigation */}
      <Sidebar />
      
      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        {children}
      </main>
      
      {/* Right Sidebar - Tasks List */}
      <div className="w-80 border-l bg-card hidden xl:block">
        <TasksSidebar />
      </div>
    </div>
  )
}
