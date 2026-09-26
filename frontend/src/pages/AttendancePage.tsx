import { useCallback, useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { Alert } from '../components/ui/Alert.tsx'
import { Badge } from '../components/ui/Badge.tsx'
import { Button } from '../components/ui/Button.tsx'
import { Card, CardTitle } from '../components/ui/Card.tsx'
import { EmptyState } from '../components/ui/EmptyState.tsx'
import { SelectField, TextField } from '../components/ui/Field.tsx'
import { Modal } from '../components/ui/Modal.tsx'
import { ProgressBar } from '../components/ui/ProgressBar.tsx'
import { ATTENDANCE_STATUSES, ATTENDANCE_STATUS_LABELS } from '../constants/attendanceStatus.ts'
import type { AttendanceStatusOption } from '../constants/attendanceStatus.ts'
import {
  createAttendance,
  deleteAttendance,
  getAttendanceOverview,
  getCourses,
  getEnrollments,
  updateAttendance,
} from '../services/api.ts'
import { ApiError } from '../services/http.ts'
import type {
  AttendanceOverview,
  AttendanceRecord,
  Course,
  Enrollment,
} from '../types/entities.ts'

type EditorState =
  | { mode: 'create' }
  | { mode: 'edit'; record: AttendanceRecord }
  | null

export function AttendancePage() {
  const [overview, setOverview] = useState<AttendanceOverview | null>(null)
  const [courses, setCourses] = useState<Course[]>([])
  const [enrollments, setEnrollments] = useState<Enrollment[]>([])
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [editor, setEditor] = useState<EditorState>(null)
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [deletingId, setDeletingId] = useState<number | null>(null)
  const [courseId, setCourseId] = useState('')
  const [attendanceDate, setAttendanceDate] = useState('')
  const [status, setStatus] = useState<AttendanceStatusOption>('present')

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [nextOverview, nextCourses, nextEnrollments] = await Promise.all([
        getAttendanceOverview(),
        getCourses(),
        getEnrollments(),
      ])
      setOverview(nextOverview)
      setCourses(nextCourses)
      setEnrollments(nextEnrollments)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Could not load attendance.')
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

  function openCreate() {
    setFormError(null)
    setCourseId(enrolledCourses[0] ? String(enrolledCourses[0].id) : '')
    setAttendanceDate(new Date().toISOString().slice(0, 10))
    setStatus('present')
    setEditor({ mode: 'create' })
  }

  function openEdit(record: AttendanceRecord) {
    setFormError(null)
    setCourseId(String(record.course_id))
    setAttendanceDate(record.attendance_date)
    setStatus(record.status)
    setEditor({ mode: 'edit', record })
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
      if (editor.mode === 'create') {
        if (!courseId) {
          setFormError('Select a course.')
          return
        }
        await createAttendance({
          course_id: Number(courseId),
          attendance_date: attendanceDate,
          status,
        })
      } else {
        await updateAttendance(editor.record.id, {
          attendance_date: attendanceDate,
          status,
        })
      }
      setSuccess(editor.mode === 'create' ? 'Attendance recorded successfully.' : 'Attendance updated successfully.')
      setEditor(null)
      await load()
    } catch (caught) {
      setFormError(caught instanceof ApiError ? caught.message : 'Could not save attendance.')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleDelete(record: AttendanceRecord) {
    const confirmed = window.confirm(
      `Delete attendance for ${record.course.code} on ${record.attendance_date}?`,
    )
    if (!confirmed) {
      return
    }
    try {
      setDeletingId(record.id)
      await deleteAttendance(record.id)
      setSuccess('Attendance record deleted.')
      await load()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Could not delete attendance.')
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <section className="space-y-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-base font-semibold text-[var(--cp-ink)]">Attendance</h2>
          <p className="mt-1 max-w-2xl text-sm leading-6 text-[var(--cp-muted)]">
            Record class sessions by date. Totals and percentages are calculated from those records.
          </p>
        </div>
        <div className="flex flex-wrap gap-2"><Link to="/assistant" state={{ prompt: 'Where is my attendance at risk based on the configured threshold?' }} className="inline-flex min-h-10 items-center rounded-[var(--cp-radius-sm)] border border-[var(--cp-border)] bg-white px-3.5 text-xs font-semibold text-[var(--cp-ink)] hover:bg-[var(--cp-brand-wash)]">Ask about attendance</Link><Button onClick={openCreate} disabled={enrolledCourses.length === 0 && !loading}>Add attendance</Button></div>
      </div>

      {error ? <Alert>{error}</Alert> : null}
      {success ? <p role="status" className="text-sm font-medium text-[var(--cp-success)]">{success}</p> : null}
      {loading ? (
        <p className="text-sm text-[var(--cp-muted)]" role="status">
          Loading attendance
        </p>
      ) : null}

      {!loading && overview ? (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <Card>
              <CardTitle>Overall</CardTitle>
              <p className="mt-4 text-2xl font-semibold">
                {overview.attendance_percentage === null ? '—' : `${overview.attendance_percentage}%`}
              </p>
              <p className="mt-2 text-sm text-[var(--cp-muted)]">
                {overview.attended_classes}/{overview.total_classes} classes attended
              </p>
            </Card>
            <Card>
              <CardTitle>Attended</CardTitle>
              <p className="mt-4 text-2xl font-semibold">{overview.attended_classes}</p>
            </Card>
            <Card>
              <CardTitle>Missed</CardTitle>
              <p className="mt-4 text-2xl font-semibold">{overview.missed_classes}</p>
            </Card>
            <Card>
              <CardTitle>Courses tracked</CardTitle>
              <p className="mt-4 text-2xl font-semibold">{overview.courses_tracked}</p>
            </Card>
          </div>

          {overview.courses.length === 0 ? (
            <EmptyState
              title="No attendance yet"
              message={
                enrolledCourses.length === 0
                  ? 'Enroll in a course first, then record class attendance here.'
                  : 'Add your first class session to start tracking attendance percentages.'
              }
              actionLabel={enrolledCourses.length === 0 ? undefined : 'Add attendance'}
              onAction={enrolledCourses.length === 0 ? undefined : openCreate}
            />
          ) : (
            <div className="space-y-4">
              {overview.courses.map((course) => (
                <Card key={course.course.id} className="space-y-4">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <h3 className="text-base font-semibold text-[var(--cp-ink)]">{course.course.title}</h3>
                      <p className="mt-1 text-sm text-[var(--cp-muted)]">{course.course.code}</p>
                    </div>
                    <Badge tone="brand">
                      {course.attended_classes}/{course.total_classes}
                      {course.attendance_percentage === null ? '' : ` · ${course.attendance_percentage}%`}
                    </Badge>
                  </div>
                  <ProgressBar value={course.attendance_percentage} label="Attendance" />
                  <div className="overflow-x-auto">
                    <table className="min-w-full text-left text-sm">
                      <thead className="text-[var(--cp-muted)]">
                        <tr>
                          <th className="py-2 pr-4 font-medium" scope="col">
                            Date
                          </th>
                          <th className="py-2 pr-4 font-medium" scope="col">
                            Status
                          </th>
                          <th className="py-2 font-medium" scope="col">
                            Actions
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {course.records.map((record) => (
                          <tr key={record.id} className="border-t border-[var(--cp-border)]">
                            <td className="py-3 pr-4 font-medium text-[var(--cp-ink)]">{record.attendance_date}</td>
                            <td className="py-3 pr-4 capitalize text-slate-700">{record.status}</td>
                            <td className="py-3">
                              <div className="flex flex-wrap gap-2">
                                <Button size="sm" variant="secondary" disabled={deletingId === record.id} onClick={() => openEdit(record)}>
                                  Edit
                                </Button>
                                <Button size="sm" variant="ghost" disabled={deletingId === record.id} onClick={() => void handleDelete(record)}>
                                  {deletingId === record.id ? 'Deleting…' : 'Delete'}
                                </Button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </>
      ) : null}

      <Modal
        open={editor !== null}
        title={editor?.mode === 'edit' ? 'Edit attendance' : 'Add attendance'}
        onClose={() => setEditor(null)}
        footer={
          <>
            <Button variant="secondary" onClick={() => setEditor(null)} disabled={submitting}>
              Cancel
            </Button>
            <Button type="submit" form="attendance-form" disabled={submitting}>
              {submitting ? 'Saving' : 'Save'}
            </Button>
          </>
        }
      >
        <form id="attendance-form" className="space-y-4" onSubmit={(event) => void handleSubmit(event)}>
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
            <p className="text-sm text-[var(--cp-muted)]">Course stays fixed when editing an attendance record.</p>
          )}
          <TextField
            label="Date"
            name="attendance_date"
            type="date"
            required
            value={attendanceDate}
            onChange={(event) => setAttendanceDate(event.target.value)}
          />
          <SelectField
            label="Status"
            name="status"
            value={status}
            onChange={(event) => setStatus(event.target.value as AttendanceStatusOption)}
          >
            {ATTENDANCE_STATUSES.map((item) => (
              <option key={item} value={item}>
                {ATTENDANCE_STATUS_LABELS[item]}
              </option>
            ))}
          </SelectField>
          {formError ? <Alert>{formError}</Alert> : null}
        </form>
      </Modal>
    </section>
  )
}
