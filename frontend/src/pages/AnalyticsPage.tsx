import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  AttendanceBarChart,
  CourseScoreBarChart,
  GradeDonutChart,
  PerformanceLineChart,
} from '../components/charts/AnalyticsCharts.tsx'
import { Alert } from '../components/ui/Alert.tsx'
import { Badge } from '../components/ui/Badge.tsx'
import { Button } from '../components/ui/Button.tsx'
import { Card, CardTitle } from '../components/ui/Card.tsx'
import { EmptyState } from '../components/ui/EmptyState.tsx'
import { SelectField } from '../components/ui/Field.tsx'
import { ProgressBar } from '../components/ui/ProgressBar.tsx'
import {
  getAnalyticsAttendance,
  getAnalyticsCourses,
  getAnalyticsInsights,
  getAnalyticsOverview,
  getAnalyticsPerformance,
  simulateGpa,
} from '../services/api.ts'
import { ApiError } from '../services/http.ts'
import type {
  AnalyticsOverview,
  AttendanceAnalytics,
  CourseAnalytics,
  GpaSimulationResponse,
  InsightsResponse,
  PerformanceTrend,
} from '../types/entities.ts'

function metric(value: number | null | undefined, suffix = ''): string {
  if (value === null || value === undefined) {
    return '—'
  }
  return `${value}${suffix}`
}

function severityTone(severity: string): 'danger' | 'accent' | 'brand' | 'neutral' {
  if (severity === 'CRITICAL') {
    return 'danger'
  }
  if (severity === 'WARNING') {
    return 'accent'
  }
  if (severity === 'INFO') {
    return 'brand'
  }
  return 'neutral'
}

function healthTone(health: string): 'success' | 'accent' | 'danger' | 'neutral' {
  if (health === 'HEALTHY') {
    return 'success'
  }
  if (health === 'WARNING') {
    return 'accent'
  }
  if (health === 'CRITICAL') {
    return 'danger'
  }
  return 'neutral'
}

export function AnalyticsPage() {
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null)
  const [courses, setCourses] = useState<CourseAnalytics[]>([])
  const [performance, setPerformance] = useState<PerformanceTrend | null>(null)
  const [attendance, setAttendance] = useState<AttendanceAnalytics | null>(null)
  const [insights, setInsights] = useState<InsightsResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const [hypoGrades, setHypoGrades] = useState<Record<number, string>>({})
  const [simulation, setSimulation] = useState<GpaSimulationResponse | null>(null)
  const [simulating, setSimulating] = useState(false)
  const [simError, setSimError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [nextOverview, nextCourses, nextPerformance, nextAttendance, nextInsights] =
        await Promise.all([
          getAnalyticsOverview(),
          getAnalyticsCourses(),
          getAnalyticsPerformance(),
          getAnalyticsAttendance(),
          getAnalyticsInsights(),
        ])
      setOverview(nextOverview)
      setCourses(nextCourses)
      setPerformance(nextPerformance)
      setAttendance(nextAttendance)
      setInsights(nextInsights)
      setHypoGrades((prev) => {
        const next = { ...prev }
        for (const course of nextCourses) {
          if (course.status !== 'complete' && !(course.course.id in next)) {
            next[course.course.id] = nextOverview.available_grade_letters[0] ?? 'A'
          }
        }
        return next
      })
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Could not load analytics.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const incompleteCourses = useMemo(
    () => courses.filter((item) => item.status !== 'complete'),
    [courses],
  )

  const scoredCourses = useMemo(
    () =>
      courses
        .filter((item) => item.current_score !== null)
        .map((item) => ({
          name: item.course.code,
          score: item.current_score as number,
        })),
    [courses],
  )

  const performanceChart = useMemo(() => {
    if (!performance || performance.status !== 'ready') {
      return []
    }
    return performance.points.map((point, index) => ({
      label: `${point.assessment_name}`,
      percentage: point.percentage,
      course: point.course.code,
      key: `${point.course.code}-${point.assessment_type}-${index}`,
    }))
  }, [performance])

  const attendanceChart = useMemo(() => {
    if (!attendance) {
      return []
    }
    return attendance.courses
      .filter((item) => item.percentage !== null)
      .map((item) => ({
        name: item.course.code,
        percentage: item.percentage as number,
      }))
  }, [attendance])

  const gradeChart = useMemo(() => {
    if (!overview) {
      return []
    }
    return overview.grade_distribution.filter((item) => item.count > 0)
  }, [overview])

  async function handleSimulate() {
    setSimError(null)
    setSimulating(true)
    try {
      const payload = incompleteCourses
        .filter((item) => hypoGrades[item.course.id])
        .map((item) => ({
          course_id: item.course.id,
          letter_grade: hypoGrades[item.course.id],
        }))
      const result = await simulateGpa(payload)
      setSimulation(result)
    } catch (caught) {
      setSimError(caught instanceof ApiError ? caught.message : 'Could not run GPA simulation.')
    } finally {
      setSimulating(false)
    }
  }

  return (
    <section className="space-y-8">
      <div>
        <h2 className="text-base font-semibold text-[var(--cp-ink)]">Academic analytics</h2>
        <p className="mt-1 max-w-2xl text-sm leading-6 text-[var(--cp-muted)]">
          Explainable insights from your marks, attendance, exams, and assignments — calculated on
          the server from real data.
        </p>
      </div>

      {error ? <Alert>{error}</Alert> : null}
      {loading ? (
        <p className="text-sm text-[var(--cp-muted)]" role="status">
          Loading analytics
        </p>
      ) : null}

      {!loading && overview ? (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <Card>
              <CardTitle>GPA</CardTitle>
              <p className="mt-4 text-2xl font-semibold">{metric(overview.gpa.value)}</p>
              <p className="mt-2 text-sm text-[var(--cp-muted)]">
                {overview.gpa.message ?? 'Current semester GPA'}
              </p>
            </Card>
            <Card>
              <CardTitle>CGPA</CardTitle>
              <p className="mt-4 text-2xl font-semibold">{metric(overview.cgpa.value)}</p>
              <p className="mt-2 text-sm text-[var(--cp-muted)]">
                {overview.cgpa.message ?? 'Cumulative GPA'}
              </p>
            </Card>
            <Card>
              <CardTitle>Credits</CardTitle>
              <p className="mt-4 text-2xl font-semibold">
                {overview.completed_credits}/{overview.total_credits}
              </p>
              <p className="mt-2 text-sm text-[var(--cp-muted)]">
                {overview.completed_courses} of {overview.total_courses} courses complete
              </p>
            </Card>
            <Card>
              <CardTitle>Attendance</CardTitle>
              <p className="mt-4 text-2xl font-semibold">{metric(overview.overall_attendance, '%')}</p>
              {overview.overall_attendance !== null ? (
                <div className="mt-4">
                  <ProgressBar value={overview.overall_attendance} />
                </div>
              ) : (
                <p className="mt-2 text-sm text-[var(--cp-muted)]">No attendance recorded yet.</p>
              )}
            </Card>
          </div>

          {overview.data_status === 'empty' ? (
            <EmptyState
              title="Not enough academic data yet"
              message={overview.message ?? 'Enroll in courses and add marks to unlock analytics.'}
            />
          ) : null}

          <div className="grid gap-6 xl:grid-cols-2">
            <Card className="space-y-3">
              <div>
                <CardTitle>Performance trend</CardTitle>
                <p className="mt-1 text-sm text-[var(--cp-muted)]">
                  Assessment results in chronological order.
                </p>
              </div>
              {performance?.status === 'ready' && performanceChart.length > 0 ? (
                <>
                  <PerformanceLineChart data={performanceChart} />
                  <ul className="space-y-2 text-sm">
                    {performance.points.map((point, index) => (
                      <li
                        key={`${point.course.id}-${point.assessment_type}-${index}`}
                        className="flex flex-wrap items-center justify-between gap-2 border-t border-[var(--cp-border)] pt-2"
                      >
                        <span>
                          {point.course.code} · {point.assessment_name}
                        </span>
                        <span className="font-medium">
                          {point.percentage}%
                          {point.change_from_previous !== null
                            ? ` (${point.change_from_previous > 0 ? '+' : ''}${point.change_from_previous})`
                            : ''}
                        </span>
                      </li>
                    ))}
                  </ul>
                </>
              ) : (
                <EmptyState
                  title="Insufficient performance data"
                  message={
                    performance?.message ??
                    'At least two assessment results are needed for a trend chart.'
                  }
                />
              )}
            </Card>

            <Card className="space-y-3">
              <div>
                <CardTitle>Course performance</CardTitle>
                <p className="mt-1 text-sm text-[var(--cp-muted)]">
                  Current scores for courses with calculated results.
                </p>
              </div>
              {scoredCourses.length > 0 ? (
                <>
                  <CourseScoreBarChart data={scoredCourses} />
                  <ul className="space-y-2 text-sm">
                    {courses.map((item) => (
                      <li
                        key={item.course.id}
                        className="flex flex-wrap items-center justify-between gap-2 border-t border-[var(--cp-border)] pt-2"
                      >
                        <span>
                          {item.course.code} · {item.course.title}
                        </span>
                        <span className="font-medium">
                          {item.current_score === null ? 'Incomplete' : `${item.current_score}%`}
                          {item.grade ? ` · ${item.grade}` : ''}
                          {` · ${item.completed_assessments}/${item.required_assessments}`}
                        </span>
                      </li>
                    ))}
                  </ul>
                </>
              ) : (
                <EmptyState
                  title="No course scores yet"
                  message="Complete weighted assessments for a course to see score comparisons."
                />
              )}
            </Card>
          </div>

          <div className="grid gap-6 xl:grid-cols-2">
            <Card className="space-y-3">
              <div>
                <CardTitle>Attendance by course</CardTitle>
                <p className="mt-1 text-sm text-[var(--cp-muted)]">{attendance?.overall_message}</p>
              </div>
              {attendanceChart.length > 0 ? (
                <>
                  <AttendanceBarChart data={attendanceChart} />
                  <ul className="space-y-2 text-sm">
                    {attendance?.courses.map((item) => (
                      <li
                        key={item.course.id}
                        className="flex flex-wrap items-center justify-between gap-2 border-t border-[var(--cp-border)] pt-2"
                      >
                        <span>
                          {item.course.code}: {item.attended}/{item.total} attended
                        </span>
                        <Badge tone={healthTone(item.health)}>{item.health}</Badge>
                      </li>
                    ))}
                  </ul>
                </>
              ) : (
                <EmptyState
                  title="No attendance data"
                  message="Record class sessions to see attendance analytics."
                />
              )}
            </Card>

            <Card className="space-y-3">
              <div>
                <CardTitle>Grade distribution</CardTitle>
                <p className="mt-1 text-sm text-[var(--cp-muted)]">
                  Completed courses only. Incomplete courses are excluded.
                </p>
              </div>
              {gradeChart.length > 0 ? (
                <>
                  <GradeDonutChart data={overview.grade_distribution} />
                  <div className="flex flex-wrap gap-2">
                    {overview.grade_distribution.map((bucket) => (
                      <Badge key={bucket.letter} tone={bucket.count > 0 ? 'brand' : 'neutral'}>
                        {bucket.letter}: {bucket.count}
                      </Badge>
                    ))}
                  </div>
                </>
              ) : (
                <EmptyState
                  title="No completed grades"
                  message="Finish a course’s weighted assessments to populate grade distribution."
                />
              )}
            </Card>
          </div>

          <Card className="space-y-4">
            <div className="flex items-end justify-between gap-3">
              <div>
                <CardTitle>Insights</CardTitle>
                <p className="mt-1 text-sm text-[var(--cp-muted)]">
                  Deterministic, factual observations — not predictions.
                </p>
              </div>
              <Link
                className="text-sm font-semibold text-[var(--cp-brand)] underline-offset-2 hover:underline"
                to="/"
              >
                Dashboard
              </Link>
            </div>
            {insights?.insights.length ? (
              <ul className="space-y-3">
                {insights.insights.map((insight) => (
                  <li
                    key={insight.id}
                    className="flex flex-col gap-2 rounded-xl border border-[var(--cp-border)] px-4 py-3 sm:flex-row sm:items-center sm:justify-between"
                  >
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="text-sm font-semibold text-[var(--cp-ink)]">{insight.title}</p>
                        <Badge tone={severityTone(insight.severity)}>{insight.severity}</Badge>
                      </div>
                      <p className="mt-1 text-sm text-[var(--cp-muted)]">{insight.message}</p>
                    </div>
                    {insight.navigation_target ? (
                      <Link
                        className="text-sm font-semibold text-[var(--cp-brand)] underline-offset-2 hover:underline"
                        to={insight.navigation_target}
                      >
                        Open
                      </Link>
                    ) : null}
                  </li>
                ))}
              </ul>
            ) : (
              <EmptyState
                title="No insights yet"
                message={insights?.message ?? 'Add more academic activity to generate insights.'}
              />
            )}
          </Card>

          <Card className="space-y-4">
            <div>
              <CardTitle>What-if GPA</CardTitle>
              <p className="mt-1 text-sm text-[var(--cp-muted)]">
                Projected / Hypothetical only. This does not change saved marks or GPA.
              </p>
            </div>
            {incompleteCourses.length === 0 ? (
              <EmptyState
                title="No incomplete courses to simulate"
                message="Hypothetical grades apply to courses that are not yet fully assessed."
              />
            ) : (
              <>
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {incompleteCourses.map((item) => (
                    <SelectField
                      key={item.course.id}
                      label={`${item.course.code} · ${item.credits} cr`}
                      name={`hypo-${item.course.id}`}
                      value={hypoGrades[item.course.id] ?? ''}
                      onChange={(event) =>
                        setHypoGrades((prev) => ({
                          ...prev,
                          [item.course.id]: event.target.value,
                        }))
                      }
                    >
                      {(overview.available_grade_letters.length
                        ? overview.available_grade_letters
                        : ['S', 'A', 'B', 'C', 'D', 'E', 'F']
                      ).map((letter) => (
                        <option key={letter} value={letter}>
                          {letter}
                        </option>
                      ))}
                    </SelectField>
                  ))}
                </div>
                <div className="flex flex-wrap items-center gap-3">
                  <Button onClick={() => void handleSimulate()} disabled={simulating}>
                    {simulating ? 'Calculating' : 'Calculate projected GPA'}
                  </Button>
                  <p className="text-sm text-[var(--cp-muted)]">
                    Current GPA: {metric(overview.gpa.value)}
                  </p>
                </div>
                {simError ? <Alert>{simError}</Alert> : null}
                {simulation ? (
                  <div className="rounded-xl border border-dashed border-[var(--cp-border)] bg-slate-50 px-4 py-4">
                    <p className="text-xs font-semibold tracking-wide text-[var(--cp-muted)] uppercase">
                      {simulation.label}
                    </p>
                    <p className="mt-2 text-2xl font-semibold text-[var(--cp-ink)]">
                      {metric(simulation.projected_gpa.value)}
                    </p>
                    <p className="mt-1 text-sm text-[var(--cp-muted)]">
                      Current {metric(simulation.current_gpa.value)} → Projected{' '}
                      {metric(simulation.projected_gpa.value)}
                      {simulation.message ? ` · ${simulation.message}` : ''}
                    </p>
                  </div>
                ) : null}
              </>
            )}
          </Card>
        </>
      ) : null}
    </section>
  )
}
