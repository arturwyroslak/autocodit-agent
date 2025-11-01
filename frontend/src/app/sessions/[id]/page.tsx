import LiveSessionView from '@/components/LiveSessionView'

export default function Page({ params }: { params: { id: string } }) {
  return (
    <div className="container mx-auto p-4">
      <LiveSessionView sessionId={params.id} />
    </div>
  )
}
