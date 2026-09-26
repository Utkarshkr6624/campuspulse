import { useCallback, useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { Alert } from '../components/ui/Alert.tsx'
import { Badge } from '../components/ui/Badge.tsx'
import { Button } from '../components/ui/Button.tsx'
import { Card } from '../components/ui/Card.tsx'
import { EmptyState } from '../components/ui/EmptyState.tsx'
import { SelectField, TextAreaField, TextField } from '../components/ui/Field.tsx'
import { Modal } from '../components/ui/Modal.tsx'
import {
  ASSIGNMENT_PRIORITIES,
  ASSIGNMENT_PRIORITY_LABELS,
  ASSIGNMENT_STATUSES,
  ASSIGNMENT_STATUS_LABELS,
} from '../constants/assignmentEnums.ts'
import type { AssignmentPriorityOption, AssignmentStatusOption } from '../constants/assignmentEnums.ts'
import {
  createAssignment,
  deleteAssignment,
  getAssignments,
  getCourses,
  getEnrollments,
  updateAssignment,
} from '../services/api.ts'
import { ApiError } from '../services/http.ts'
import type { Assignment, Course, Enrollment } from '../types/entities.ts'
import { relativeDayLabel } from '../utils/plannerEvents.ts'

type EditorState =
  | { mode: 'create' }
  | { mode: 'edit'; assignment: Assignment }
  | null

function formatDate(value: string): string {
  return new Date(`${value}T12:00:00`).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

function formatTime(value: string | null): string | null {
  if (!value) {
    return null
  }
  const [hours, minutes] = value.split(':')
  const date = new Date()
  date.setHours(Number(hours), Number(minutes), 0, 0)
  return date.toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' })
}

function statusTone(assignment: Assignment): 'danger' | 'accent' | 'brand' | 'success' | 'neutral' {
  if (assignment.status === 'COMPLETED') {
    return 'success'
  }
  if (assignment.is_overdue) {
    return 'danger'
  }
  if (assignment.is_due_today) {
    return 'accent'
  }
  if (assignment.days_until <= 7) {
    return 'brand'
  }
  return 'neutral'
}

function priorityTone(priority: AssignmentPriorityOption): 'danger' | 'accent' | 'neutral' {
  if (priority === 'HIGH') {
    return 'danger'
  }
  if (priority === 'MEDIUM') {
    return 'accent'
  }
  return 'neutral'
}

function dueBucketLabel(assignment: Assignment): string {
  if (assignment.status === 'COMPLETED') {
    return 'Completed'
  }
  if (assignment.is_overdue) {
    return 'Overdue'
  }
  if (assignment.is_due_today) {
    return 'Due today'
  }
  if (assignment.days_until <= 7) {
    return 'Due soon'
  }
  return relativeDayLabel(assignment.days_until)
}

export function AssignmentsPage() {
  const [assignments, setAssignments] = useState<Assignment[]>([])
  const [courses, setCourses] = useState<Course[]>([])
  const [enrollments, setEnrollments] = useState<Enrollment[]>([])
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [editor, setEditor] = useState<EditorState>(null)
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [pendingId, setPendingId] = useState<number | null>(null)

  const [filterStatus, setFilterStatus] = useState('')
  const [filterCourseId, setFilterCourseId] = useState('')
  const [filterPriority, setFilterPriority] = useState('')
  const [filterLens, setFilterLens] = useState('open')

  const [courseId, setCourseId] = useState('')
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [dueDate, setDueDate] = useState('')
  const [dueTime, setDueTime] = useState('')
  const [status, setStatus] = useState<AssignmentStatusOption>('TODO')
  const [priority, setPriority] = useState<AssignmentPriorityOption>('MEDIUM')

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const params: {
        upcoming?: boolean
        completed?: boolean
        course_id?: number
        priority?: AssignmentPriorityOption
        status?: AssignmentStatusOption
      } = {}
      if (filterLens === 'upcoming') {
        params.upcoming = true
      } else if (filterLens === 'completed') {
        params.completed = true
      } else if (filterLens === 'open') {
        params.completed = false
      }
      if (filterCourseId) {
        params.course_id = Number(filterCourseId)
      }
      if (filterPriority) {
        params.priority = filterPriority as AssignmentPriorityOption
      }
      if (filterStatus) {
        params.status = filterStatus as AssignmentStatusOption
      }

      const [nextAssignments, nextCourses, nextEnrollments] = await Promise.all([
        getAssignments(params),
        getCourses(),
        getEnrollments(),
      ])
      setAssignments(nextAssignments)
      setCourses(nextCourses)
      setEnrollments(nextEnrollments)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Could not load assignments.')
    } finally {
      setLoading(false)
    }
  }, [filterCourseId, filterLens, filterPriority, filterStatus])

  useEffect(() => {
    void load()
  }, [load])

  const enrolledCourses = useMemo(() => {
    const enrolledIds = new Set(
      enrollments.filter((item) => item.status === 'enrolled').map((item) => item.course_id),
    )
    return courses.filter((course) => enrolledIds.has(course.id))
  }, [courses, enrollments])

  function resetForm(seed?: Assignment) {
    setFormError(null)
    setCourseId(seed ? String(seed.course_id) : enrolledCourses[0] ? String(enrolledCourses[0].id) : '')
    setTitle(seed?.title ?? '')
    setDescription(seed?.description ?? '')
    setDueDate(seed?.due_date ?? '')
    setDueTime(seed?.due_time?.slice(0, 5) ?? '')
    setStatus((seed?.status as AssignmentStatusOption) ?? 'TODO')
    setPriority((seed?.priority as AssignmentPriorityOption) ?? 'MEDIUM')
  }

  function openCreate() {
    resetForm()
    setEditor({ mode: 'create' })
  }

  function openEdit(assignment: Assignment) {
    resetForm(assignment)
    setEditor({ mode: 'edit', assignment })
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!editor) {
      return
    }
    setFormError(null)
    setSuccess(null)
    setSubmitting(true)
    try {
      const payload = {
        title: title.trim(),
        description: description.trim() || null,
        due_date: dueDate,
        due_time: dueTime || null,
        status,
        priority,
      }
      if (editor.mode === 'create') {
        if (!courseId) {
          setFormError('Select a course.')
          return
        }
        await createAssignment({ course_id: Number(courseId), ...payload })
      } else {
        await updateAssignment(editor.assignment.id, payload)
      }
      setSuccess(editor.mode === 'create' ? 'Assignment added successfully.' : 'Assignment updated successfully.')
      setEditor(null)
      await load()
    } catch (caught) {
      setFormError(caught instanceof ApiError ? caught.message : 'Could not save assignment.')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleStatusChange(assignment: Assignment, nextStatus: AssignmentStatusOption) {
    setPendingId(assignment.id)
    try {
      await updateAssignment(assignment.id, { status: nextStatus })
      setSuccess('Assignment status updated.')
      await load()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Could not update status.')
    } finally {
      setPendingId(null)
    }
  }

  async function handleDelete(assignment: Assignment) {
    const confirmed = window.confirm(`Delete assignment “${assignment.title}”?`)
    if (!confirmed) {
      return
    }
    setPendingId(assignment.id)
    try {
      await deleteAssignment(assignment.id)
      setSuccess('Assignment deleted successfully.')
      await load()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Could not delete assignment.')
    } finally {
      setPendingId(null)
    }
  }

  return (
    <section className="space-y-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-base font-semibold text-[var(--cp-ink)]">Assignments</h2>
          <p className="mt-1 max-w-2xl text-sm leading-6 text-[var(--cp-muted)]">
            Manage coursework deadlines with clear priority and status.
          </p>
        </div>
        <Button onClick={openCreate} disabled={enrolledCourses.length === 0 && !loading}>
          Add assignment
        </Button>
      </div>

      <Card className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <SelectField
          label="View"
          name="filter_lens"
          value={filterLens}
          onChange={(event) => setFilterLens(event.target.value)}
        >
          <option value="open">Open</option>
          <option value="upcoming">Upcoming</option>
          <option value="completed">Completed</option>
          <option value="all">All</option>
        </SelectField>
        <SelectField
          label="Status"
          name="filter_status"
          value={filterStatus}
          onChange={(event) => setFilterStatus(event.target.value)}
        >
          <option value="">Any status</option>
          {ASSIGNMENT_STATUSES.map((item) => (
            <option key={item} value={item}>
              {ASSIGNMENT_STATUS_LABELS[item]}
            </option>
          ))}
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
          label="Priority"
          name="filter_priority"
          value={filterPriority}
          onChange={(event) => setFilterPriority(event.target.value)}
        >
          <option value="">Any priority</option>
          {ASSIGNMENT_PRIORITIES.map((item) => (
            <option key={item} value={item}>
              {ASSIGNMENT_PRIORITY_LABELS[item]}
            </option>
          ))}
        </SelectField>
      </Card>

      {success ? <p role="status" className="text-sm font-medium text-[var(--cp-success)]">{success}</p> : null}

      {error ? <Alert>{error}</Alert> : null}
      {loading ? (
        <p className="text-sm text-[var(--cp-muted)]" role="status">
          Loading assignments
        </p>
      ) : null}

      {!loading && assignments.length === 0 ? (
        <EmptyState
          title="No assignments yet"
          message={
            enrolledCourses.length === 0
              ? 'Enroll in a course first, then track assignment deadlines here.'
              : 'Add a due date for your next lab report, homework, or project.'
          }
          actionLabel={enrolledCourses.length === 0 ? undefined : 'Add assignment'}
          onAction={enrolledCourses.length === 0 ? undefined : openCreate}
        />
      ) : null}

      {!loading && assignments.length > 0 ? (
        <div className="space-y-3">
          {assignments.map((assignment) => {
            const timeLabel = formatTime(assignment.due_time)
            return (
              <Card key={assignment.id} className="space-y-4">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                  <div className="min-w-0 space-y-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="text-base font-semibold text-[var(--cp-ink)]">{assignment.title}</h3>
                      <Badge tone={statusTone(assignment)}>{dueBucketLabel(assignment)}</Badge>
                      <Badge tone={priorityTone(assignment.priority)}>
                        {ASSIGNMENT_PRIORITY_LABELS[assignment.priority]}
                      </Badge>
                    </div>
                    <p className="text-sm text-[var(--cp-muted)]">
                      {assignment.course.code} · {assignment.course.title}
                    </p>
                    <p className="text-sm text-slate-700">
                      Due {formatDate(assignment.due_date)}
                      {timeLabel ? ` · ${timeLabel}` : ''}
                      {' · '}
                      {ASSIGNMENT_STATUS_LABELS[assignment.status]}
                    </p>
                    {assignment.description ? (
                      <p className="text-sm leading-6 text-slate-600">{assignment.description}</p>
                    ) : null}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Button size="sm" variant="secondary" disabled={pendingId === assignment.id} onClick={() => openEdit(assignment)}>
                      Edit
                    </Button>
                    <Button size="sm" variant="ghost" disabled={pendingId === assignment.id} onClick={() => void handleDelete(assignment)}>
                      {pendingId === assignment.id ? 'Saving…' : 'Delete'}
                    </Button>
                  </div>
                </div>
                <div className="flex flex-wrap gap-2">
                  {ASSIGNMENT_STATUSES.map((item) => (
                    <Button
                      key={item}
                      size="sm"
                      variant={assignment.status === item ? 'primary' : 'secondary'}
                      onClick={() => void handleStatusChange(assignment, item)}
                      disabled={assignment.status === item || pendingId === assignment.id}
                    >
                      {ASSIGNMENT_STATUS_LABELS[item]}
                    </Button>
                  ))}
                </div>
              </Card>
            )
          })}
        </div>
      ) : null}

      <Modal
        open={editor !== null}
        title={editor?.mode === 'edit' ? 'Edit assignment' : 'Add assignment'}
        onClose={() => setEditor(null)}
        footer={
          <>
            <Button variant="secondary" onClick={() => setEditor(null)} disabled={submitting}>
              Cancel
            </Button>
            <Button type="submit" form="assignment-form" disabled={submitting}>
              {submitting ? 'Saving' : 'Save'}
            </Button>
          </>
        }
      >
        <form id="assignment-form" className="space-y-4" onSubmit={(event) => void handleSubmit(event)}>
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
            <p className="text-sm text-[var(--cp-muted)]">Course stays fixed when editing an assignment.</p>
          )}
          <TextField
            label="Title"
            name="title"
            required
            value={title}
            onChange={(event) => setTitle(event.target.value)}
          />
          <TextAreaField
            label="Description"
            name="description"
            rows={3}
            value={description}
            onChange={(event) => setDescription(event.target.value)}
          />
          <div className="grid gap-4 sm:grid-cols-2">
            <TextField
              label="Due date"
              name="due_date"
              type="date"
              required
              value={dueDate}
              onChange={(event) => setDueDate(event.target.value)}
            />
            <TextField
              label="Due time"
              name="due_time"
              type="time"
              value={dueTime}
              onChange={(event) => setDueTime(event.target.value)}
            />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <SelectField
              label="Status"
              name="status"
              value={status}
              onChange={(event) => setStatus(event.target.value as AssignmentStatusOption)}
            >
              {ASSIGNMENT_STATUSES.map((item) => (
                <option key={item} value={item}>
                  {ASSIGNMENT_STATUS_LABELS[item]}
                </option>
              ))}
            </SelectField>
            <SelectField
              label="Priority"
              name="priority"
              value={priority}
              onChange={(event) => setPriority(event.target.value as AssignmentPriorityOption)}
            >
              {ASSIGNMENT_PRIORITIES.map((item) => (
                <option key={item} value={item}>
                  {ASSIGNMENT_PRIORITY_LABELS[item]}
                </option>
              ))}
            </SelectField>
          </div>
          {formError ? <Alert>{formError}</Alert> : null}
        </form>
      </Modal>
    </section>
  )
}
