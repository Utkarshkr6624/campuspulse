import { EmptyState } from '../components/ui/EmptyState.tsx'

type PlaceholderPageProps = {
  title: string
  message: string
}

export function PlaceholderPage({ title, message }: PlaceholderPageProps) {
  return (
    <section>
      <EmptyState title={title} message={message} />
    </section>
  )
}
