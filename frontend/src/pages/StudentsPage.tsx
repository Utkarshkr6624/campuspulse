import { QueryState } from '../components/QueryState.tsx'
import { Card } from '../components/ui/Card.tsx'
import { useApiList } from '../hooks/useApiList.ts'
import { getStudents } from '../services/api.ts'

export function StudentsPage() {
  const state = useApiList(getStudents)

  return (
    <section className="space-y-6">
      <p className="max-w-2xl text-sm leading-6 text-[var(--cp-muted)]">
        Registered students are listed here.
      </p>
      <QueryState
        {...state}
        loadingLabel="Loading students"
        emptyTitle="No students yet"
        emptyMessage="No students have been added yet."
      >
        {(students) => (
          <Card className="overflow-hidden p-0">
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm">
                <thead className="border-b border-[var(--cp-border)] bg-slate-50 text-[var(--cp-muted)]">
                  <tr>
                    <th className="px-4 py-3 font-medium" scope="col">
                      University ID
                    </th>
                    <th className="px-4 py-3 font-medium" scope="col">
                      Name
                    </th>
                    <th className="px-4 py-3 font-medium" scope="col">
                      Email
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {students.map((student) => (
                    <tr key={student.id} className="border-b border-slate-100 last:border-b-0">
                      <td className="px-4 py-3 font-medium text-[var(--cp-ink)]">{student.university_id}</td>
                      <td className="px-4 py-3 text-slate-700">{student.full_name}</td>
                      <td className="px-4 py-3 text-slate-700">{student.email}</td>
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
