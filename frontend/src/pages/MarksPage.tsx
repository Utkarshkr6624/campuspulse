import { useCallback, useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { Alert } from '../components/ui/Alert.tsx'
import { Badge } from '../components/ui/Badge.tsx'
import { Button } from '../components/ui/Button.tsx'
import { Card, CardTitle } from '../components/ui/Card.tsx'
import { EmptyState } from '../components/ui/EmptyState.tsx'
import { SelectField, TextField } from '../components/ui/Field.tsx'
import { Modal } from '../components/ui/Modal.tsx'
import { ASSESSMENT_TYPES, assessmentLabel } from '../constants/assessmentTypes.ts'
import type { AssessmentType } from '../constants/assessmentTypes.ts'
import {
  createMark,
  deleteMark,
  getAcademicCourses,
  getAcademicSummary,
  getCourses,
  getEnrollments,
  getMarks,
  updateMark,
} from '../services/api.ts'
import { ApiError } from '../services/http.ts'
import type {
  AcademicSummary,
  Course,
  CourseMark,
  CoursePerformance,
  Enrollment,
} from '../types/entities.ts'

type EditorState =
  | { mode: 'create' }
  | { mode: 'edit'; mark: CourseMark }
  | null

export function MarksPage() {
  const [performances, setPerformances] = useState<CoursePerformance[]>([])
  const [summary, setSummary] = useState<AcademicSummary | null>(null)
  const [marks, setMarks] = useState<CourseMark[]>([])
  const [courses, setCourses] = useState<Course[]>([])
  const [enrollments, setEnrollments] = useState<Enrollment[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [editor, setEditor] = useState<EditorState>(null)
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [courseId, setCourseId] = useState('')
  const [assessmentType, setAssessmentType] = useState<AssessmentType>('CAT1')
  const [marksObtained, setMarksObtained] = useState('')
  const [maximumMarks, setMaximumMarks] = useState('')
  const [assessmentDate, setAssessmentDate] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [nextPerformances, nextSummary, nextMarks, nextCourses, nextEnrollments] = await Promise.all([
        getAcademicCourses(),
        getAcademicSummary(),
        getMarks(),
        getCourses(),
        getEnrollments(),
      ])
      setPerformances(nextPerformances)
      setSummary(nextSummary)
      setMarks(nextMarks)
      setCourses(nextCourses)
      setEnrollments(nextEnrollments)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Could not load marks.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const enrolledCourses = useMemo(() => {
    const enrolledIds = new Set(
      enrollments.filter((item) => item.status === 'enrolled').map((item) => item.course_id),
    )
    return courses.filter((course) => enrolledIds.has(course.id))
  }, [courses, enrollments])

  const marksByKey = useMemo(() => {
    const map = new Map<string, CourseMark>()
    for (const mark of marks) {
      map.set(`${mark.course_id}:${mark.assessment_type}`, mark)
    }
    return map
  }, [marks])

  function openCreate() {
    setFormError(null)
    setCourseId(enrolledCourses[0] ? String(enrolledCourses[0].id) : '')
    setAssessmentType('CAT1')
    setMarksObtained('')
    setMaximumMarks('')
    setAssessmentDate('')
    setEditor({ mode: 'create' })
  }

  function openEdit(mark: CourseMark) {
    setFormError(null)
    setCourseId(String(mark.course_id))
    setAssessmentType(mark.assessment_type)
    setMarksObtained(String(mark.marks_obtained))
    setMaximumMarks(String(mark.maximum_marks))
    setAssessmentDate(mark.assessment_date ?? '')
    setEditor({ mode: 'edit', mark })
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!editor) {
      return
    }
    setFormError(null)
    const obtained = Number(marksObtained)
    const maximum = Number(maximumMarks)
    if (!Number.isFinite(obtained) || !Number.isFinite(maximum)) {
      setFormError('Enter valid numeric marks.')
      return
    }
    if (maximum <= 0) {
      setFormError('Maximum marks must be greater than zero.')
      return
    }
    if (obtained > maximum) {
      setFormError('Marks obtained cannot exceed maximum marks.')
      return
    }

    setSubmitting(true)
    try {
      if (editor.mode === 'create') {
        if (!courseId) {
          setFormError('Select a course.')
          return
        }
        await createMark({
          course_id: Number(courseId),
          assessment_type: assessmentType,
          marks_obtained: obtained,
          maximum_marks: maximum,
          assessment_date: assessmentDate || null,
        })
      } else {
        await updateMark(editor.mark.id, {
          assessment_type: assessmentType,
          marks_obtained: obtained,
          maximum_marks: maximum,
          assessment_date: assessmentDate || null,
        })
      }
      setEditor(null)
      await load()
    } catch (caught) {
      setFormError(caught instanceof ApiError ? caught.message : 'Could not save mark.')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleDelete(mark: CourseMark) {
    const confirmed = window.confirm(
      `Delete ${assessmentLabel(mark.assessment_type)} for ${mark.course.code}?`,
    )
    if (!confirmed) {
      return
    }
    try {
      await deleteMark(mark.id)
      await load()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Could not delete mark.')
    }
  }

  return (
    <section className="space-y-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-base font-semibold text-[var(--cp-ink)]">Marks & performance</h2>
          <p className="mt-1 max-w-2xl text-sm leading-6 text-[var(--cp-muted)]">
            Raw assessments feed the calculation engine for course score, letter grade, and grade point.
          </p>
        </div>
        <Button onClick={openCreate} disabled={enrolledCourses.length === 0 && !loading}>
          Add marks
        </Button>
      </div>

      {error ? <Alert>{error}</Alert> : null}
      {loading ? (
        <p className="text-sm text-[var(--cp-muted)]" role="status">
          Loading marks
        </p>
      ) : null}

      {!loading && summary ? (
        <div className="grid gap-4 sm:grid-cols-3">
          <Card>
            <CardTitle>GPA</CardTitle>
            <p className="mt-4 text-2xl font-semibold">{summary.gpa.value ?? '—'}</p>
            <p className="mt-2 text-sm text-[var(--cp-muted)]">{summary.gpa.message ?? 'Credit-weighted GPA'}</p>
          </Card>
          <Card>
            <CardTitle>CGPA</CardTitle>
            <p className="mt-4 text-2xl font-semibold">{summary.cgpa.value ?? '—'}</p>
            <p className="mt-2 text-sm text-[var(--cp-muted)]">{summary.cgpa.message ?? 'Cumulative GPA'}</p>
          </Card>
          <Card>
            <CardTitle>Completed courses</CardTitle>
            <p className="mt-4 text-2xl font-semibold">{summary.completed_courses}</p>
            <p className="mt-2 text-sm text-[var(--cp-muted)]">
              {summary.incomplete_courses} still missing weighted assessments
            </p>
          </Card>
        </div>
      ) : null}

      {!loading && performances.length === 0 ? (
        <EmptyState
          title="No enrolled courses"
          message="Enroll in a course, then add assessment marks to calculate performance."
        />
      ) : null}

      {!loading && performances.length > 0 ? (
        <div className="space-y-4">
          {performances.map((course) => (
            <Card key={course.course.id} className="overflow-hidden p-0">
              <div className="flex flex-col gap-3 border-b border-[var(--cp-border)] px-5 py-4 lg:flex-row lg:items-center lg:justify-between">
                <div>
                  <h3 className="text-base font-semibold text-[var(--cp-ink)]">{course.course.title}</h3>
                  <p className="mt-1 text-sm text-[var(--cp-muted)]">
                    {course.course.code} · {course.credits} credits · {course.semester}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Badge tone={course.status === 'complete' ? 'success' : 'neutral'}>{course.status}</Badge>
                  <Badge tone="brand">Score {course.final_score ?? '—'}</Badge>
                  <Badge tone="accent">
                    {course.grade ?? '—'} / {course.grade_point ?? '—'} GP
                  </Badge>
                </div>
              </div>
              {course.message ? (
                <p className="border-b border-[var(--cp-border)] px-5 py-3 text-sm text-[var(--cp-muted)]">
                  {course.message}
                  {course.missing_assessment_types.length > 0
                    ? ` Missing: ${course.missing_assessment_types.map(assessmentLabel).join(', ')}.`
                    : ''}
                </p>
              ) : null}
              <div className="overflow-x-auto">
                <table className="min-w-full text-left text-sm">
                  <thead className="bg-slate-50 text-[var(--cp-muted)]">
                    <tr>
                      <th className="px-5 py-3 font-medium" scope="col">
                        Assessment
                      </th>
                      <th className="px-5 py-3 font-medium" scope="col">
                        Score
                      </th>
                      <th className="px-5 py-3 font-medium" scope="col">
                        Weight
                      </th>
                      <th className="px-5 py-3 font-medium" scope="col">
                        Contribution
                      </th>
                      <th className="px-5 py-3 font-medium" scope="col">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {course.assessments.length === 0 ? (
                      <tr>
                        <td className="px-5 py-4 text-[var(--cp-muted)]" colSpan={5}>
                          No assessments recorded for this course yet.
                        </td>
                      </tr>
                    ) : (
                      course.assessments.map((item) => {
                        const mark = marksByKey.get(`${course.course.id}:${item.assessment_type}`)
                        return (
                          <tr key={item.assessment_type} className="border-t border-[var(--cp-border)]">
                            <td className="px-5 py-3 font-medium text-[var(--cp-ink)]">
                              {assessmentLabel(item.assessment_type)}
                            </td>
                            <td className="px-5 py-3 text-slate-700">
                              {item.marks_obtained}/{item.maximum_marks}
                            </td>
                            <td className="px-5 py-3 text-slate-700">{item.weight_percent}%</td>
                            <td className="px-5 py-3 text-slate-700">{item.weighted_contribution}</td>
                            <td className="px-5 py-3">
                              {mark ? (
                                <div className="flex flex-wrap gap-2">
                                  <Button size="sm" variant="secondary" onClick={() => openEdit(mark)}>
                                    Edit
                                  </Button>
                                  <Button size="sm" variant="ghost" onClick={() => void handleDelete(mark)}>
                                    Delete
                                  </Button>
                                </div>
                              ) : (
                                <span className="text-[var(--cp-muted)]">—</span>
                              )}
                            </td>
                          </tr>
                        )
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </Card>
          ))}
        </div>
      ) : null}

      <Modal
        open={editor !== null}
        title={editor?.mode === 'edit' ? 'Edit mark' : 'Add mark'}
        onClose={() => setEditor(null)}
        footer={
          <>
            <Button variant="secondary" onClick={() => setEditor(null)} disabled={submitting}>
              Cancel
            </Button>
            <Button type="submit" form="mark-form" disabled={submitting}>
              {submitting ? 'Saving' : 'Save mark'}
            </Button>
          </>
        }
      >
        <form id="mark-form" className="space-y-4" onSubmit={(event) => void handleSubmit(event)}>
          {editor?.mode === 'create' ? (
            <SelectField
              label="Course"
              name="course_id"
              value={courseId}
              required
              onChange={(event) => setCourseId(event.target.value)}
            >
              <option value="" disabled>
                Select a course
              </option>
              {enrolledCourses.map((course) => (
                <option key={course.id} value={course.id}>
                  {course.code} · {course.title}
                </option>
              ))}
            </SelectField>
          ) : (
            <p className="text-sm text-[var(--cp-muted)]">
              Course stays fixed when editing. Delete and recreate to move an assessment to another course.
            </p>
          )}
          <SelectField
            label="Assessment type"
            name="assessment_type"
            value={assessmentType}
            onChange={(event) => setAssessmentType(event.target.value as AssessmentType)}
          >
            {ASSESSMENT_TYPES.map((type) => (
              <option key={type} value={type}>
                {assessmentLabel(type)}
              </option>
            ))}
          </SelectField>
          <div className="grid gap-4 sm:grid-cols-2">
            <TextField
              label="Marks obtained"
              name="marks_obtained"
              type="number"
              min="0"
              step="0.01"
              required
              value={marksObtained}
              onChange={(event) => setMarksObtained(event.target.value)}
            />
            <TextField
              label="Maximum marks"
              name="maximum_marks"
              type="number"
              min="0.01"
              step="0.01"
              required
              value={maximumMarks}
              onChange={(event) => setMaximumMarks(event.target.value)}
            />
          </div>
          <TextField
            label="Assessment date"
            name="assessment_date"
            type="date"
            value={assessmentDate}
            onChange={(event) => setAssessmentDate(event.target.value)}
          />
          {formError ? <Alert>{formError}</Alert> : null}
        </form>
      </Modal>
    </section>
  )
}
