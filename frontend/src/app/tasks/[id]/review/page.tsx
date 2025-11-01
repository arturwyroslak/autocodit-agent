import TaskReview from '@/components/TaskReview'

export default function Page({ params }: { params: { id: string } }) {
  return (
    <div className="container mx-auto p-4">
      <TaskReview taskId={params.id} />
    </div>
  )
}
