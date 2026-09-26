import { QueryState } from '../components/QueryState.tsx'
import { Card } from '../components/ui/Card.tsx'
import { useApiList } from '../hooks/useApiList.ts'
import { getEnrollments } from '../services/api.ts'

export function EnrollmentsPage() {
  const state = useApiList(getEnrollments)

  return (
    <section className="space-y-6">
      <p className="max-w-2xl text-sm leading-6 text-[var(--cp-muted)]">
        Your enrollment records are listed here.
      </p>
      <QueryState
        {...state}
        loadingLabel="Loading enrollments"
        emptyTitle="No enrollments yet"
        emptyMessage="No enrollments have been recorded yet."
      >
        {(enrollments) => (
          <Card className="overflow-hidden p-0">
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm">
                <thead className="border-b border-[var(--cp-border)] bg-slate-50 text-[var(--cp-muted)]">
                  <tr>
                    <th className="px-4 py-3 font-medium" scope="col">
                      Course ID
                    </th>
                    <th className="px-4 py-3 font-medium" scope="col">
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {enrollments.map((enrollment) => (
                    <tr key={enrollment.id} className="border-b border-slate-100 last:border-b-0">
                      <td className="px-4 py-3 text-slate-700">{enrollment.course_id}</td>
                      <td className="px-4 py-3 font-medium text-[var(--cp-ink)]">{enrollment.status}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}
      </QueryState>
    </section>
  )
}
