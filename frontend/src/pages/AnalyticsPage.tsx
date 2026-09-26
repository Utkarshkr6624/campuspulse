import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  AttendanceBarChart,
  CourseScoreBarChart,
  GradeDonutChart,
  GpaHistoryLineChart,
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
  getAnalyticsIntelligence,
  getAnalyticsOverview,
  getAnalyticsPerformance,
  simulateGpa,
} from '../services/api.ts'
import { ApiError } from '../services/http.ts'
import type {
  AnalyticsOverview,
  AcademicIntelligence,
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
  const [intelligence, setIntelligence] = useState<AcademicIntelligence | null>(null)
  const [firstSemesterId, setFirstSemesterId] = useState('')
  const [secondSemesterId, setSecondSemesterId] = useState('')
  const [comparing, setComparing] = useState(false)
  const [comparisonError, setComparisonError] = useState<string | null>(null)
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
      const [nextOverview, nextCourses, nextPerformance, nextAttendance, nextInsights, nextIntelligence] =
        await Promise.all([
          getAnalyticsOverview(),
          getAnalyticsCourses(),
          getAnalyticsPerformance(),
          getAnalyticsAttendance(),
          getAnalyticsInsights(),
          getAnalyticsIntelligence(),
        ])
      setOverview(nextOverview)
      setCourses(nextCourses)
      setPerformance(nextPerformance)
      setAttendance(nextAttendance)
      setInsights(nextInsights)
      setIntelligence(nextIntelligence)
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

  async function handleSemesterCompare() {
    if (!firstSemesterId || !secondSemesterId || firstSemesterId === secondSemesterId) {
      setComparisonError('Choose two different semesters to compare.')
      return
    }
    setComparisonError(null)
    setComparing(true)
    try {
      setIntelligence(await getAnalyticsIntelligence({
        first_semester_id: Number(firstSemesterId),
        second_semester_id: Number(secondSemesterId),
      }))
    } catch (caught) {
      setComparisonError(caught instanceof Error ? caught.message : 'Could not compare semesters.')
    } finally {
      setComparing(false)
    }
  }

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
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="cp-kicker">Performance intelligence</p>
          <h2 className="cp-page-title mt-2">Academic analytics</h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-[var(--cp-muted)]">
            Explainable insights from your marks, attendance, exams, and assignments — calculated on
            the server from real data.
          </p>
        </div>
        <Link to="/assistant" state={{ prompt: 'Summarize my academic performance and explain the semester trend.' }} className="inline-flex min-h-10 items-center justify-center gap-2 self-start rounded-[var(--cp-radius-sm)] border border-[var(--cp-border)] bg-white px-3.5 text-xs font-semibold text-[var(--cp-ink)] transition hover:bg-[var(--cp-brand-wash)] sm:self-auto">
          Explain my performance <span aria-hidden="true">→</span>
        </Link>
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

          {intelligence ? (
            <>
              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <Card>
                  <CardTitle>Current SGPA</CardTitle>
                  <p className="mt-4 text-2xl font-semibold">{metric(intelligence.current_sgpa)}</p>
                  <p className="mt-2 text-sm text-[var(--cp-muted)]">
                    Previous SGPA {metric(intelligence.previous_sgpa)}
                    {intelligence.sgpa_change !== null ? ` · ${intelligence.sgpa_change > 0 ? '+' : ''}${intelligence.sgpa_change}` : ''}
                  </p>
                  <p className="mt-1 text-xs text-[var(--cp-muted)]">
                    Best: {intelligence.best_semester_number ? `Sem ${intelligence.best_semester_number} · ${metric(intelligence.best_sgpa)}` : '—'}
                    {' · '}Lowest: {intelligence.lowest_semester_number ? `Sem ${intelligence.lowest_semester_number} · ${metric(intelligence.lowest_sgpa)}` : '—'}
                  </p>
                </Card>
                <Card>
                  <CardTitle>Average recorded marks</CardTitle>
                  <p className="mt-4 text-2xl font-semibold">{metric(intelligence.average_marks, '%')}</p>
                  <p className="mt-2 text-sm text-[var(--cp-muted)]">Available course final scores only</p>
                </Card>
                <Card>
                  <CardTitle>Completed credits</CardTitle>
                  <p className="mt-4 text-2xl font-semibold">{intelligence.completed_credits}</p>
                  <p className="mt-2 text-sm text-[var(--cp-muted)]">
                    {intelligence.current_semester_credits} known in current semester · {intelligence.total_known_credits} total known
                  </p>
                </Card>
                <Card>
                  <CardTitle>Course progress</CardTitle>
                  <p className="mt-4 text-2xl font-semibold">
                    {intelligence.completed_courses} complete · {intelligence.ongoing_courses} ongoing
                  </p>
                  <p className="mt-2 text-sm text-[var(--cp-muted)]">
                    Attendance threshold {intelligence.attendance_warning_threshold}%
                  </p>
                </Card>
              </div>

              <div className="grid gap-6 xl:grid-cols-2">
                <Card className="space-y-3">
                  <div>
                    <CardTitle>Semester performance and credit trend</CardTitle>
                    <p className="mt-1 text-sm text-[var(--cp-muted)]">
                      Semester GPAs and cumulative progression use completed-course credits.
                    </p>
                  </div>
                  {intelligence.semester_trend.some((item) => item.sgpa !== null) ? (
                    <>
                      <GpaHistoryLineChart data={intelligence.semester_trend
                        .filter((item) => item.sgpa !== null)
                        .map((item) => ({ semester: `Sem ${item.semester_number}`, gpa: item.sgpa as number }))} />
                      <ul className="space-y-2 text-sm">
                        {intelligence.semester_trend.map((item) => (
                          <li key={item.semester_id} className="flex justify-between gap-3 border-t border-[var(--cp-border)] pt-2">
                            <span>Semester {item.semester_number} · {item.course_count} courses · {item.completed_credits}/{item.known_credits} credits</span>
                            <span>SGPA {metric(item.sgpa)} · CGPA {metric(item.cumulative_gpa)}</span>
                          </li>
                        ))}
                      </ul>
                    </>
                  ) : (
                    <EmptyState title="Semester trend unavailable" message={intelligence.message ?? 'Add completed semester data to view GPA progression.'} />
                  )}
                </Card>
                <Card className="space-y-4">
                  <div>
                    <CardTitle>Compare semesters</CardTitle>
                    <p className="mt-1 text-sm text-[var(--cp-muted)]">Differences are second semester minus first semester.</p>
                  </div>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <SelectField label="First semester" name="compare-first" value={firstSemesterId} onChange={(event) => setFirstSemesterId(event.target.value)}>
                      <option value="">Choose semester</option>
                      {intelligence.semester_trend.map((item) => <option key={item.semester_id} value={item.semester_id}>Semester {item.semester_number}</option>)}
                    </SelectField>
                    <SelectField label="Second semester" name="compare-second" value={secondSemesterId} onChange={(event) => setSecondSemesterId(event.target.value)}>
                      <option value="">Choose semester</option>
                      {intelligence.semester_trend.map((item) => <option key={item.semester_id} value={item.semester_id}>Semester {item.semester_number}</option>)}
                    </SelectField>
                  </div>
                  <Button onClick={() => void handleSemesterCompare()} disabled={comparing || intelligence.semester_trend.length < 2}>
                    {comparing ? 'Comparing' : 'Compare semesters'}
                  </Button>
                  {comparisonError ? <Alert>{comparisonError}</Alert> : null}
                  {intelligence.comparison ? (
                    <div className="space-y-2 rounded-xl border border-[var(--cp-border)] p-4 text-sm">
                      <p>SGPA change: <strong>{metric(intelligence.comparison.sgpa_difference)}</strong></p>
                      <p>Average marks change: <strong>{metric(intelligence.comparison.average_marks_difference, ' pp')}</strong></p>
                      <p>Known credits change: <strong>{intelligence.comparison.credits_difference > 0 ? '+' : ''}{intelligence.comparison.credits_difference}</strong></p>
                      <p>Course count change: <strong>{intelligence.comparison.course_count_difference > 0 ? '+' : ''}{intelligence.comparison.course_count_difference}</strong></p>
                      <p className="text-[var(--cp-muted)]">{intelligence.comparison.attendance_note}</p>
                    </div>
                  ) : null}
                </Card>
              </div>

              <Card className="space-y-4">
                <div>
                  <CardTitle>Subject performance intelligence</CardTitle>
                  <p className="mt-1 text-sm text-[var(--cp-muted)]">
                    Score categories use configured thresholds ({intelligence.low_score_threshold}% attention, {intelligence.strong_score_threshold}% strong). Attendance is course-wide where recorded.
                  </p>
                </div>
                {intelligence.courses.length ? (
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[720px] text-left text-sm">
                      <thead><tr className="border-b border-[var(--cp-border)] text-[var(--cp-muted)]"><th className="py-2">Semester / course</th><th>Score</th><th>Grade / GP</th><th>Credits</th><th>Attendance</th><th>CAT 1 → CAT 2</th><th>Status</th></tr></thead>
                      <tbody>{intelligence.courses.map((item, index) => (
                        <tr key={`${item.semester_id ?? 'legacy'}-${item.course_id ?? item.course_code}-${index}`} className="border-b border-[var(--cp-border)]">
                          <td className="py-3">{item.semester_number ? `Sem ${item.semester_number} · ` : ''}{item.course_code ?? item.course_name}<span className="block text-xs text-[var(--cp-muted)]">{item.course_name}</span></td>
                          <td>{metric(item.score, '%')}</td><td>{item.grade ?? '—'} / {metric(item.grade_point)}</td><td>{item.credits}</td>
                          <td>{metric(item.attendance_percentage, '%')}<span className="block text-xs text-[var(--cp-muted)]">{item.attendance_health}</span></td>
                          <td>{metric(item.cat1_to_cat2_change, ' pp')}</td><td><Badge tone={item.performance_category === 'STRONG' ? 'success' : item.performance_category === 'NEEDS_ATTENTION' ? 'danger' : 'neutral'}>{item.performance_category.replaceAll('_', ' ')}</Badge></td>
                        </tr>
                      ))}</tbody>
                    </table>
                  </div>
                ) : <EmptyState title="No course records" message="Add semester history or enroll in courses and record marks." />}
              </Card>

              <Card className="space-y-3">
                <div><CardTitle>Academic intelligence insights</CardTitle><p className="mt-1 text-sm text-[var(--cp-muted)]">Deterministic observations with the source metric shown.</p></div>
                {intelligence.insights.length ? <ul className="space-y-3">{intelligence.insights.map((item, index) => (
                  <li key={`${item.type}-${index}`} className="rounded-xl border border-[var(--cp-border)] px-4 py-3">
                    <div className="flex flex-wrap items-center gap-2"><strong className="text-sm">{item.title}</strong><Badge tone={severityTone(item.severity)}>{item.severity}</Badge></div>
                    <p className="mt-1 text-sm text-[var(--cp-muted)]">{item.description}</p>
                    <p className="mt-1 text-xs text-[var(--cp-muted)]">Source: {item.source_metric}</p>
                  </li>
                ))}</ul> : <EmptyState title="No insights yet" message={intelligence.message ?? 'Add more academic data to generate measurable observations.'} />}
              </Card>
            </>
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
