import { Card, CardTitle } from './ui/Card.tsx'

type PlaceholderCardProps = {
  title: string
  message: string
}

export function PlaceholderCard({ title, message }: PlaceholderCardProps) {
  return (
    <Card>
      <CardTitle>{title}</CardTitle>
      <p className="mt-4 text-sm leading-6 text-slate-700">{message}</p>
    </Card>
  )
}
