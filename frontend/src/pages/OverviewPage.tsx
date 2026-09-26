import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { PlaceholderCard } from '../components/PlaceholderCard.tsx'
import { Alert } from '../components/ui/Alert.tsx'
import { Badge } from '../components/ui/Badge.tsx'
import { Button } from '../components/ui/Button.tsx'
import { Card, CardTitle } from '../components/ui/Card.tsx'
import { EmptyState } from '../components/ui/EmptyState.tsx'
import { GpaHistoryLineChart } from '../components/charts/AnalyticsCharts.tsx'
import { ASSIGNMENT_PRIORITY_LABELS, ASSIGNMENT_STATUS_LABELS } from '../constants/assignmentEnums.ts'
import { assessmentLabel } from '../constants/assessmentTypes.ts'
import { examTypeLabel } from '../constants/examTypes.ts'
import { useAuth } from '../hooks/useAuth.tsx'
import {
  getAcademicSummary,
  getAnalyticsInsights,
  getAnalyticsIntelligence,
  getAssignments,
  getAttendanceOverview,
  getExams,
  getSemesters,
} from '../services/api.ts'
import type {
  AcademicInsight,
  AcademicIntelligence,
  AcademicSummary,
  Assignment,
  AttendanceOverview,
  Exam,
} from '../types/entities.ts'
import { relativeDayLabel } from '../utils/plannerEvents.ts'

function metricValue(value: number | null | undefined, suffix = ''): string {
  if (value === null || value === undefined) {
    return '—'
  }
  return `${value}${suffix}`
}

function formatShortDate(value: string): string {
  return new Date(`${value}T12:00:00`).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
  })
}

export function OverviewPage() {
  const { student } = useAuth()
  const navigate = useNavigate()
  const [academic, setAcademic] = useState<AcademicSummary | null>(null)
  const [attendance, setAttendance] = useState<AttendanceOverview | null>(null)
  const [upcomingExams, setUpcomingExams] = useState<Exam[]>([])
  const [assignments, setAssignments] = useState<Assignment[]>([])
  const [insights, setInsights] = useState<AcademicInsight[]>([])
  const [intelligence, setIntelligence] = useState<AcademicIntelligence | null>(null)
  const [hasSemesterSetup, setHasSemesterSetup] = useState<boolean | null>(null)
  const [currentSemesterNumber, setCurrentSemesterNumber] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    Promise.all([
      getAcademicSummary(),
      getAttendanceOverview(),
      getExams({ upcoming: true }),
      getAssignments(),
      getAnalyticsInsights(),
      getSemesters(),
      getAnalyticsIntelligence(),
    ])
      .then(([nextAcademic, nextAttendance, nextExams, nextAssignments, nextInsights, nextSemesters, nextIntelligence]) => {
        if (!active) {
          return
        }
        setAcademic(nextAcademic)
        setAttendance(nextAttendance)
        setUpcomingExams(nextExams.slice(0, 4))
        setAssignments(nextAssignments)
        setInsights(nextInsights.insights.slice(0, 3))
        setHasSemesterSetup(nextSemesters.length > 0)
        setCurrentSemesterNumber(nextSemesters.find((item) => item.is_current)?.number ?? null)
        setIntelligence(nextIntelligence)
      })
      .catch((caught: unknown) => {
        if (active) {
          setError(caught instanceof Error ? caught.message : 'Could not load dashboard.')
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false)
        }
      })
    return () => {
      active = false
    }
  }, [])

  const completedCourses = academic?.courses.filter((item) => item.status === 'complete') ?? []
  const overdueAssignments = assignments
    .filter((item) => item.is_overdue)
    .sort((a, b) => a.due_date.localeCompare(b.due_date))
    .slice(0, 3)
  const dueSoonAssignments = assignments
    .filter((item) => item.status !== 'COMPLETED' && !item.is_overdue && item.days_until <= 7)
    .sort((a, b) => a.due_date.localeCompare(b.due_date))
    .slice(0, 3)
  const recentlyCompleted = assignments
    .filter((item) => item.status === 'COMPLETED')
    .sort((a, b) => b.updated_at.localeCompare(a.updated_at))
    .slice(0, 3)

  return (
    <section className="space-y-8">
      <section className="relative overflow-hidden rounded-[1.35rem] bg-[var(--cp-brand)] px-6 py-7 text-white shadow-[var(--cp-shadow)] sm:px-8 sm:py-8" aria-labelledby="overview-welcome">
        <div className="relative z-10 flex flex-col justify-between gap-6 md:flex-row md:items-end">
          <div className="max-w-2xl">
            <p className="cp-kicker !text-[var(--cp-accent)]">Your academic workspace</p>
            <h2 id="overview-welcome" className="mt-3 text-2xl font-semibold tracking-[-0.04em] sm:text-3xl">
              {student ? `Good to see you, ${student.full_name.split(' ')[0]}.` : 'Your academic picture, in focus.'}
            </h2>
            <p className="mt-2 max-w-xl text-sm leading-6 text-white/70">
              {currentSemesterNumber
                ? `Semester ${currentSemesterNumber} · A calm place to understand your progress and plan what comes next.`
                : 'A calm place to understand your progress and plan what comes next.'}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {hasSemesterSetup === false ? <Button variant="secondary" onClick={() => navigate('/semesters')}>Set up semesters</Button> : null}
            <Button className="!border !border-white/20 !bg-white/10 !text-white hover:!bg-white/15" onClick={() => navigate('/assistant')}>
              Ask CampusPulse
            </Button>
          </div>
        </div>
        <div aria-hidden="true" className="pointer-events-none absolute -right-8 -top-24 h-72 w-72 rounded-full border border-white/10" />
        <div aria-hidden="true" className="pointer-events-none absolute -right-2 -top-16 h-56 w-56 rounded-full border border-white/10" />
      </section>

      {error ? <Alert>{error}</Alert> : null}
      {loading ? (
        <p className="text-sm text-[var(--cp-muted)]" role="status">
          Loading dashboard
        </p>
      ) : null}

      <Card padded={false} className="overflow-hidden">
        <div className="grid divide-y divide-[var(--cp-border)] sm:grid-cols-2 sm:divide-x sm:divide-y-0 xl:grid-cols-4">
        <div className="p-5 sm:p-6">
          <CardTitle>Current GPA</CardTitle>
          <p className="mt-3 text-3xl font-semibold tracking-[-0.05em] text-[var(--cp-ink)]">
            {metricValue(academic?.gpa.value)}
          </p>
          <p className="mt-1.5 text-xs text-[var(--cp-muted)]">{currentSemesterNumber ? `Semester ${currentSemesterNumber}` : 'Current semester'}</p>
        </div>
        <div className="p-5 sm:p-6">
          <CardTitle>CGPA</CardTitle>
          <p className="mt-3 text-3xl font-semibold tracking-[-0.05em] text-[var(--cp-ink)]">
            {metricValue(academic?.cgpa.value)}
          </p>
          <p className="mt-1.5 text-xs text-[var(--cp-muted)]">Cumulative performance</p>
        </div>
        <div className="p-5 sm:p-6">
          <CardTitle>Overall attendance</CardTitle>
          <p className="mt-3 text-3xl font-semibold tracking-[-0.05em] text-[var(--cp-ink)]">
            {metricValue(attendance?.attendance_percentage, '%')}
          </p>
          <p className="mt-1.5 text-xs text-[var(--cp-muted)]">
            {(attendance?.total_classes ?? 0) === 0
              ? 'No attendance has been recorded yet.'
              : `${attendance?.attended_classes}/${attendance?.total_classes} classes attended.`}
          </p>
        </div>
        <div className="p-5 sm:p-6">
          <CardTitle>Credits completed</CardTitle>
          <p className="mt-3 text-3xl font-semibold tracking-[-0.05em] text-[var(--cp-ink)]">{intelligence?.completed_credits ?? 0}</p>
          <p className="mt-1.5 text-xs text-[var(--cp-muted)]">Across available academic history</p>
        </div>
        </div>
      </Card>

      <div className="grid gap-5 xl:grid-cols-[1.35fr_0.85fr]">
        <Card className="space-y-4">
          <div className="flex items-start justify-between gap-3">
            <div><CardTitle>Semester trajectory</CardTitle><p className="mt-1 text-xs text-[var(--cp-muted)]">SGPA by completed academic period</p></div>
            <Link className="text-xs font-semibold text-[var(--cp-brand)] hover:underline" to="/analytics">Full analysis <span aria-hidden="true">→</span></Link>
          </div>
          {intelligence?.semester_trend.some((item) => item.sgpa !== null) ? (
            <GpaHistoryLineChart data={intelligence.semester_trend.filter((item) => item.sgpa !== null).map((item) => ({ semester: `Sem ${item.semester_number}`, gpa: item.sgpa as number }))} />
          ) : <p className="rounded-[var(--cp-radius-sm)] bg-[var(--cp-surface-raised)] px-4 py-5 text-sm leading-6 text-[var(--cp-muted)]">Add semester results to build your academic trajectory. Available grades and course data remain below.</p>}
        </Card>
        <Card className="space-y-4">
          <div className="flex items-start justify-between gap-3"><div><CardTitle>Academic signals</CardTitle><p className="mt-1 text-xs text-[var(--cp-muted)]">Observations from your records</p></div><Link className="text-xs font-semibold text-[var(--cp-brand)] hover:underline" to="/analytics">View all</Link></div>
          {insights.length ? <ul className="divide-y divide-[var(--cp-border)]">{insights.slice(0, 3).map((insight) => <li key={insight.id} className="py-3 first:pt-0"><div className="flex items-start gap-2"><span aria-hidden="true" className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${insight.severity === 'CRITICAL' ? 'bg-red-500' : insight.severity === 'WARNING' ? 'bg-amber-500' : 'bg-[var(--cp-success)]'}`} /><p className="text-sm leading-6 text-[var(--cp-ink)]">{insight.message}</p></div></li>)}</ul> : <p className="text-sm leading-6 text-[var(--cp-muted)]">No notable signals yet. As you add marks and attendance, measurable observations will appear here.</p>}
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="space-y-4">
          <div className="flex items-end justify-between gap-3">
            <div>
              <CardTitle>Upcoming exams</CardTitle>
              <p className="mt-1 text-sm text-[var(--cp-muted)]">Next scheduled assessments.</p>
            </div>
            <Link
              className="text-sm font-semibold text-[var(--cp-brand)] underline-offset-2 hover:underline"
              to="/exams"
            >
              View exams
            </Link>
          </div>
          {upcomingExams.length === 0 ? (
            <EmptyState
              title="No upcoming exams"
              message="Add CAT, FAT, or quiz dates to see them here."
              actionLabel="Add exam"
              onAction={() => navigate('/exams')}
            />
          ) : (
            <ul className="space-y-3">
              {upcomingExams.map((exam) => (
                <li
                  key={exam.id}
                  className="flex items-start justify-between gap-3 border-t border-[var(--cp-border)] pt-3 first:border-t-0 first:pt-0"
                >
                  <div>
                    <p className="text-sm font-semibold text-[var(--cp-ink)]">
                      {exam.course.title} — {examTypeLabel(exam.exam_type)}
                    </p>
                    <p className="mt-1 text-xs text-[var(--cp-muted)]">
                      {formatShortDate(exam.exam_date)} · {relativeDayLabel(exam.days_until)}
                      {exam.location ? ` · ${exam.location}` : ''}
                    </p>
                  </div>
                  <Badge tone={exam.days_until <= 3 ? 'accent' : 'brand'}>{examTypeLabel(exam.exam_type)}</Badge>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card className="space-y-4">
          <div className="flex items-end justify-between gap-3">
            <div>
              <CardTitle>Assignments</CardTitle>
              <p className="mt-1 text-sm text-[var(--cp-muted)]">Due soon, overdue, and completed.</p>
            </div>
            <Link
              className="text-sm font-semibold text-[var(--cp-brand)] underline-offset-2 hover:underline"
              to="/assignments"
            >
              View assignments
            </Link>
          </div>

          {overdueAssignments.length === 0 &&
          dueSoonAssignments.length === 0 &&
          recentlyCompleted.length === 0 ? (
            <EmptyState
              title="No assignment activity"
              message="Track homework and project deadlines from the assignments page."
              actionLabel="Add assignment"
              onAction={() => navigate('/assignments')}
            />
          ) : (
            <div className="space-y-5">
              {overdueAssignments.length > 0 ? (
                <div>
                  <p className="text-xs font-semibold tracking-wide text-[var(--cp-muted)] uppercase">
                    Overdue
                  </p>
                  <ul className="mt-2 space-y-2">
                    {overdueAssignments.map((item) => (
                      <li key={item.id} className="flex items-center justify-between gap-3 text-sm">
                        <span className="font-medium text-[var(--cp-ink)]">
                          {item.course.code} — {item.title}
                        </span>
                        <Badge tone="danger">{formatShortDate(item.due_date)}</Badge>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}

              {dueSoonAssignments.length > 0 ? (
                <div>
                  <p className="text-xs font-semibold tracking-wide text-[var(--cp-muted)] uppercase">
                    Due soon
                  </p>
                  <ul className="mt-2 space-y-2">
                    {dueSoonAssignments.map((item) => (
                      <li key={item.id} className="flex items-center justify-between gap-3 text-sm">
                        <span className="font-medium text-[var(--cp-ink)]">
                          {item.course.code} — {item.title}
                        </span>
                        <Badge tone="brand">
                          {formatShortDate(item.due_date)} · {ASSIGNMENT_PRIORITY_LABELS[item.priority]}
                        </Badge>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}

              {recentlyCompleted.length > 0 ? (
                <div>
                  <p className="text-xs font-semibold tracking-wide text-[var(--cp-muted)] uppercase">
                    Recently completed
                  </p>
                  <ul className="mt-2 space-y-2">
                    {recentlyCompleted.map((item) => (
                      <li key={item.id} className="flex items-center justify-between gap-3 text-sm">
                        <span className="font-medium text-[var(--cp-ink)]">
                          {item.course.code} — {item.title}
                        </span>
                        <Badge tone="success">{ASSIGNMENT_STATUS_LABELS[item.status]}</Badge>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </div>
          )}
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.4fr_0.8fr]">
        <section className="space-y-4">
          <div className="flex items-end justify-between gap-3">
            <div>
              <h2 className="text-base font-semibold text-[var(--cp-ink)]">Academic performance</h2>
              <p className="mt-1 text-sm text-[var(--cp-muted)]">
                Course scores and grades from the calculation engine.
              </p>
            </div>
            <Link className="text-sm font-semibold text-[var(--cp-brand)] underline-offset-2 hover:underline" to="/marks">
              Open marks
            </Link>
          </div>

          {completedCourses.length > 0 ? (
            <div className="grid gap-4 md:grid-cols-2">
              {completedCourses.map((course) => (
                <Card key={course.course.id}>
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-[var(--cp-ink)]">{course.course.title}</p>
                      <p className="mt-1 text-xs text-[var(--cp-muted)]">
                        {course.course.code} · {course.credits} credits
                      </p>
                    </div>
                    <Badge tone="brand">
                      {course.grade ?? '—'} · {course.final_score ?? '—'}%
                    </Badge>
                  </div>
                  <ul className="mt-4 space-y-2">
                    {course.assessments.slice(0, 4).map((item) => (
                      <li key={item.assessment_type} className="flex items-center justify-between text-sm">
                        <span className="text-slate-600">{assessmentLabel(item.assessment_type)}</span>
                        <span className="font-medium text-[var(--cp-ink)]">
                          {item.marks_obtained}/{item.maximum_marks}
                        </span>
                      </li>
                    ))}
                  </ul>
                </Card>
              ))}
            </div>
          ) : (
            <EmptyState
              title="No graded courses yet"
              message={
                academic?.gpa.message ??
                'Add the required weighted assessments for a course to calculate score, grade, and GPA.'
              }
              actionLabel="Add marks"
              onAction={() => navigate('/marks')}
            />
          )}
        </section>

        <section className="space-y-4">
          <div>
            <h2 className="text-base font-semibold text-[var(--cp-ink)]">Quick actions</h2>
            <p className="mt-1 text-sm text-[var(--cp-muted)]">Jump into the next academic task.</p>
          </div>
          <Card className="space-y-3">
            <Button className="w-full" onClick={() => navigate('/analytics')}>
              Open analytics
            </Button>
            <Button className="w-full" variant="secondary" onClick={() => navigate('/exams')}>
              Add exam
            </Button>
            <Button className="w-full" variant="secondary" onClick={() => navigate('/assignments')}>
              Add assignment
            </Button>
            <Button className="w-full" variant="secondary" onClick={() => navigate('/planner')}>
              Open planner
            </Button>
            <Button className="w-full" variant="secondary" onClick={() => navigate('/marks')}>
              Add marks
            </Button>
            <Button className="w-full" variant="secondary" onClick={() => navigate('/attendance')}>
              Record attendance
            </Button>
          </Card>
          <PlaceholderCard
            title="Signed in"
            message={student ? `${student.email} · ${student.university_id}` : 'Session active'}
          />
        </section>
      </div>
    </section>
  )
}
