export function LoadingState({ label = 'Loading' }: { label?: string }) {
  return (
    <div role="status" aria-label={label} aria-busy="true" className="cp-panel space-y-3 p-5">
      <span className="sr-only">{label}</span>
      <div className="cp-skeleton h-3 w-1/3" />
      <div className="cp-skeleton h-3 w-2/3" />
      <div className="cp-skeleton h-3 w-1/2" />
    </div>
  )
}
