import { useCallback, useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { Alert } from '../components/ui/Alert.tsx'
import { Badge } from '../components/ui/Badge.tsx'
import { Button } from '../components/ui/Button.tsx'
import { Card } from '../components/ui/Card.tsx'
import { EmptyState } from '../components/ui/EmptyState.tsx'
import { SelectField, TextAreaField, TextField } from '../components/ui/Field.tsx'
import { Modal } from '../components/ui/Modal.tsx'
import { EXAM_TYPES, examTypeLabel } from '../constants/examTypes.ts'
import type { ExamTypeOption } from '../constants/examTypes.ts'
import {
  createExam,
  deleteExam,
  getCourses,
  getEnrollments,
  getExams,
  updateExam,
} from '../services/api.ts'
import { ApiError } from '../services/http.ts'
import type { Course, Enrollment, Exam } from '../types/entities.ts'
import { relativeDayLabel } from '../utils/plannerEvents.ts'

type EditorState = { mode: 'create' } | { mode: 'edit'; exam: Exam } | null

function formatDate(value: string): string {
  return new Date(`${value}T12:00:00`).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

function formatTimeRange(start: string | null, end: string | null): string | null {
  if (!start && !end) {
    return null
  }
  const format = (value: string) => {
    const [hours, minutes] = value.split(':')
    const date = new Date()
    date.setHours(Number(hours), Number(minutes), 0, 0)
    return date.toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' })
  }
  if (start && end) {
    return `${format(start)} – ${format(end)}`
  }
  return format(start ?? end!)
}

function urgencyTone(exam: Exam): 'danger' | 'accent' | 'brand' | 'neutral' {
  if (exam.days_until < 0) {
    return 'neutral'
  }
  if (exam.days_until === 0) {
    return 'accent'
  }
  if (exam.days_until <= 7) {
    return 'brand'
  }
  return 'neutral'
}

export function ExamsPage() {
  const [exams, setExams] = useState<Exam[]>([])
  const [courses, setCourses] = useState<Course[]>([])
  const [enrollments, setEnrollments] = useState<Enrollment[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [editor, setEditor] = useState<EditorState>(null)
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const [filterCourseId, setFilterCourseId] = useState('')
  const [filterType, setFilterType] = useState('')
  const [filterUpcoming, setFilterUpcoming] = useState('upcoming')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')

  const [courseId, setCourseId] = useState('')
  const [title, setTitle] = useState('')
  const [examType, setExamType] = useState<ExamTypeOption>('CAT1')
  const [examDate, setExamDate] = useState('')
  const [startTime, setStartTime] = useState('')
  const [endTime, setEndTime] = useState('')
  const [location, setLocation] = useState('')
  const [description, setDescription] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const params: {
        upcoming?: boolean
        course_id?: number
        exam_type?: ExamTypeOption
        date_from?: string
        date_to?: string
      } = {}
      if (filterUpcoming === 'upcoming') {
        params.upcoming = true
      } else if (filterUpcoming === 'past') {
        params.upcoming = false
      }
      if (filterCourseId) {
        params.course_id = Number(filterCourseId)
      }
      if (filterType) {
        params.exam_type = filterType as ExamTypeOption
      }
      if (dateFrom) {
        params.date_from = dateFrom
      }
      if (dateTo) {
        params.date_to = dateTo
      }

      const [nextExams, nextCourses, nextEnrollments] = await Promise.all([
        getExams(params),
        getCourses(),
        getEnrollments(),
      ])
      setExams(nextExams)
      setCourses(nextCourses)
      setEnrollments(nextEnrollments)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Could not load exams.')
    } finally {
      setLoading(false)
    }
  }, [dateFrom, dateTo, filterCourseId, filterType, filterUpcoming])

  useEffect(() => {
    void load()
  }, [load])

  const enrolledCourses = useMemo(() => {
    const enrolledIds = new Set(
      enrollments.filter((item) => item.status === 'enrolled').map((item) => item.course_id),
    )
    return courses.filter((course) => enrolledIds.has(course.id))
  }, [courses, enrollments])

  function resetForm(seed?: Exam) {
    setFormError(null)
    setCourseId(seed ? String(seed.course_id) : enrolledCourses[0] ? String(enrolledCourses[0].id) : '')
    setTitle(seed?.title ?? '')
    setExamType((seed?.exam_type as ExamTypeOption) ?? 'CAT1')
    setExamDate(seed?.exam_date ?? '')
    setStartTime(seed?.start_time?.slice(0, 5) ?? '')
    setEndTime(seed?.end_time?.slice(0, 5) ?? '')
    setLocation(seed?.location ?? '')
    setDescription(seed?.description ?? '')
  }

  function openCreate() {
    resetForm()
    setEditor({ mode: 'create' })
  }

  function openEdit(exam: Exam) {
    resetForm(exam)
    setEditor({ mode: 'edit', exam })
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!editor) {
      return
    }
    setFormError(null)
    setSubmitting(true)
    try {
      const payload = {
        title: title.trim(),
        exam_type: examType,
        exam_date: examDate,
        start_time: startTime || null,
        end_time: endTime || null,
        location: location.trim() || null,
        description: description.trim() || null,
      }
      if (editor.mode === 'create') {
        if (!courseId) {
          setFormError('Select a course.')
          return
        }
        await createExam({ course_id: Number(courseId), ...payload })
      } else {
        await updateExam(editor.exam.id, payload)
      }
      setEditor(null)
      await load()
    } catch (caught) {
      setFormError(caught instanceof ApiError ? caught.message : 'Could not save exam.')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleDelete(exam: Exam) {
    const confirmed = window.confirm(`Delete exam “${exam.title}”?`)
    if (!confirmed) {
      return
    }
    try {
      await deleteExam(exam.id)
      await load()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Could not delete exam.')
    }
  }

  return (
    <section className="space-y-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-base font-semibold text-[var(--cp-ink)]">Exams</h2>
          <p className="mt-1 max-w-2xl text-sm leading-6 text-[var(--cp-muted)]">
            Track CATs, FATs, quizzes, and labs for your enrolled courses.
          </p>
        </div>
        <Button onClick={openCreate} disabled={enrolledCourses.length === 0 && !loading}>
          Add exam
        </Button>
      </div>

      <Card className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        <SelectField
          label="Timeline"
          name="filter_upcoming"
          value={filterUpcoming}
          onChange={(event) => setFilterUpcoming(event.target.value)}
        >
          <option value="upcoming">Upcoming</option>
          <option value="past">Past</option>
          <option value="all">All</option>
        </SelectField>
        <SelectField
          label="Course"
          name="filter_course"
          value={filterCourseId}
          onChange={(event) => setFilterCourseId(event.target.value)}
        >
          <option value="">All courses</option>
          {enrolledCourses.map((course) => (
            <option key={course.id} value={course.id}>
              {course.code}
            </option>
          ))}
        </SelectField>
        <SelectField
          label="Exam type"
          name="filter_type"
          value={filterType}
          onChange={(event) => setFilterType(event.target.value)}
        >
          <option value="">All types</option>
          {EXAM_TYPES.map((type) => (
            <option key={type} value={type}>
              {examTypeLabel(type)}
            </option>
          ))}
        </SelectField>
        <TextField
          label="From"
          name="date_from"
          type="date"
          value={dateFrom}
          onChange={(event) => setDateFrom(event.target.value)}
        />
        <TextField
          label="To"
          name="date_to"
          type="date"
          value={dateTo}
          onChange={(event) => setDateTo(event.target.value)}
        />
      </Card>

      {error ? <Alert>{error}</Alert> : null}
      {loading ? (
        <p className="text-sm text-[var(--cp-muted)]" role="status">
          Loading exams
        </p>
      ) : null}

      {!loading && exams.length === 0 ? (
        <EmptyState
          title="No exams scheduled"
          message={
            enrolledCourses.length === 0
              ? 'Enroll in a course first, then add your exam schedule here.'
              : 'Add your next CAT, FAT, or quiz to keep deadlines visible.'
          }
          actionLabel={enrolledCourses.length === 0 ? undefined : 'Add exam'}
          onAction={enrolledCourses.length === 0 ? undefined : openCreate}
        />
      ) : null}

      {!loading && exams.length > 0 ? (
        <div className="space-y-3">
          {exams.map((exam) => {
            const timeLabel = formatTimeRange(exam.start_time, exam.end_time)
            return (
              <Card key={exam.id} className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div className="min-w-0 space-y-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="text-base font-semibold text-[var(--cp-ink)]">{exam.course.title}</h3>
                    <Badge tone={urgencyTone(exam)}>{examTypeLabel(exam.exam_type)}</Badge>
                    <Badge tone="neutral">{relativeDayLabel(exam.days_until)}</Badge>
                  </div>
                  <p className="text-sm font-medium text-slate-700">{exam.title}</p>
                  <p className="text-sm text-[var(--cp-muted)]">
                    {formatDate(exam.exam_date)}
                    {timeLabel ? ` · ${timeLabel}` : ''}
                    {exam.location ? ` · ${exam.location}` : ''}
                  </p>
                  {exam.description ? (
                    <p className="text-sm leading-6 text-slate-600">{exam.description}</p>
                  ) : null}
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button size="sm" variant="secondary" onClick={() => openEdit(exam)}>
                    Edit
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => void handleDelete(exam)}>
                    Delete
                  </Button>
                </div>
              </Card>
            )
          })}
        </div>
      ) : null}

      <Modal
        open={editor !== null}
        title={editor?.mode === 'edit' ? 'Edit exam' : 'Add exam'}
        onClose={() => setEditor(null)}
        footer={
          <>
            <Button variant="secondary" onClick={() => setEditor(null)} disabled={submitting}>
              Cancel
            </Button>
            <Button type="submit" form="exam-form" disabled={submitting}>
              {submitting ? 'Saving' : 'Save'}
            </Button>
          </>
        }
      >
        <form id="exam-form" className="space-y-4" onSubmit={(event) => void handleSubmit(event)}>
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
            <p className="text-sm text-[var(--cp-muted)]">Course stays fixed when editing an exam.</p>
          )}
          <TextField
            label="Title"
            name="title"
            required
            value={title}
            onChange={(event) => setTitle(event.target.value)}
          />
          <SelectField
            label="Exam type"
            name="exam_type"
            value={examType}
            onChange={(event) => setExamType(event.target.value as ExamTypeOption)}
          >
            {EXAM_TYPES.map((type) => (
              <option key={type} value={type}>
                {examTypeLabel(type)}
              </option>
            ))}
          </SelectField>
          <TextField
            label="Date"
            name="exam_date"
            type="date"
            required
            value={examDate}
            onChange={(event) => setExamDate(event.target.value)}
          />
          <div className="grid gap-4 sm:grid-cols-2">
            <TextField
              label="Start time"
              name="start_time"
              type="time"
              value={startTime}
              onChange={(event) => setStartTime(event.target.value)}
            />
            <TextField
              label="End time"
              name="end_time"
              type="time"
              value={endTime}
              onChange={(event) => setEndTime(event.target.value)}
            />
          </div>
          <TextField
            label="Location"
            name="location"
            value={location}
            onChange={(event) => setLocation(event.target.value)}
            placeholder="Room AB-204"
          />
          <TextAreaField
            label="Description"
            name="description"
            rows={3}
            value={description}
            onChange={(event) => setDescription(event.target.value)}
          />
          {formError ? <Alert>{formError}</Alert> : null}
        </form>
      </Modal>
    </section>
  )
}
