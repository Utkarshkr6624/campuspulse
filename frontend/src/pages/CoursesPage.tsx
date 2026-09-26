import { useCallback, useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Alert } from '../components/ui/Alert.tsx'
import { Badge } from '../components/ui/Badge.tsx'
import { Button } from '../components/ui/Button.tsx'
import { Card } from '../components/ui/Card.tsx'
import { EmptyState } from '../components/ui/EmptyState.tsx'
import { SelectField, TextField } from '../components/ui/Field.tsx'
import { Modal } from '../components/ui/Modal.tsx'
import { useAuth } from '../hooks/useAuth.tsx'
import { createCourse, createEnrollment, deleteCourse, getCourses, getEnrollments, getSemesters, updateCourse } from '../services/api.ts'
import type { Course, Enrollment, Semester } from '../types/entities.ts'

type Editor = { mode: 'create' } | { mode: 'edit'; course: Course } | null

export function CoursesPage() {
  const { student } = useAuth()
  const navigate = useNavigate()
  const [courses, setCourses] = useState<Course[] | null>(null)
  const [enrollments, setEnrollments] = useState<Enrollment[]>([])
  const [semesters, setSemesters] = useState<Semester[]>([])
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [formError, setFormError] = useState<string | null>(null)
  const [pendingCourseId, setPendingCourseId] = useState<number | null>(null)
  const [saving, setSaving] = useState(false)
  const [editor, setEditor] = useState<Editor>(null)
  const [code, setCode] = useState('')
  const [title, setTitle] = useState('')
  const [credits, setCredits] = useState('3')
  const [semesterId, setSemesterId] = useState('')

  const load = useCallback(async () => {
    setError(null)
    try {
      const [nextCourses, nextEnrollments, nextSemesters] = await Promise.all([getCourses(), getEnrollments(), getSemesters()])
      setCourses(nextCourses)
      setEnrollments(nextEnrollments)
      setSemesters(nextSemesters)
      setSemesterId((previous) => previous || String(nextSemesters.find((item) => item.is_current)?.id ?? nextSemesters[0]?.id ?? ''))
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Could not load courses.')
    }
  }, [])

  useEffect(() => { void load() }, [load])

  const enrollmentByCourse = useMemo(() => new Map(enrollments.map((item) => [item.course_id, item])), [enrollments])

  function openCreate() {
    setCode('')
    setTitle('')
    setCredits('3')
    setSemesterId(String(semesters.find((item) => item.is_current)?.id ?? semesters[0]?.id ?? ''))
    setFormError(null)
    setEditor({ mode: 'create' })
  }

  function openEdit(course: Course) {
    setCode(course.code)
    setTitle(course.title)
    setCredits(String(course.credits))
    setFormError(null)
    setEditor({ mode: 'edit', course })
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!editor) return
    setFormError(null)
    setSuccess(null)
    setSaving(true)
    try {
      if (editor.mode === 'create') {
        if (!semesterId) {
          setFormError('Create a semester before adding a course.')
          return
        }
        await createCourse({ code: code.trim(), title: title.trim(), credits: Number(credits), semester_id: Number(semesterId) })
        setSuccess('Course added successfully.')
      } else {
        await updateCourse(editor.course.id, { code: code.trim(), title: title.trim(), credits: Number(credits) })
        setSuccess('Course updated successfully.')
      }
      setEditor(null)
      await load()
    } catch (caught) {
      setFormError(caught instanceof Error ? caught.message : 'Could not save course.')
    } finally {
      setSaving(false)
    }
  }

  async function handleEnroll(courseId: number) {
    setSuccess(null)
    setPendingCourseId(courseId)
    try {
      await createEnrollment(courseId, 'Current', semesters.find((item) => item.is_current)?.id)
      setSuccess('Enrolled in course successfully.')
      await load()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Could not enroll.')
    } finally {
      setPendingCourseId(null)
    }
  }

  async function handleDelete(course: Course) {
    if (!window.confirm(`Delete ${course.code} — ${course.title}?`)) return
    setSuccess(null)
    setPendingCourseId(course.id)
    try {
      await deleteCourse(course.id)
      setSuccess('Course deleted successfully.')
      await load()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Could not delete course.')
    } finally {
      setPendingCourseId(null)
    }
  }

  return (
    <section className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-[var(--cp-ink)]">Courses</h2>
          <p className="mt-1 max-w-2xl text-sm leading-6 text-[var(--cp-muted)]">Add a course to one of your semesters or enroll in a shared catalog course. Your courses are private to your account.</p>
        </div>
        <Button onClick={openCreate}>Add course</Button>
      </div>
      {error ? <Alert>{error}</Alert> : null}
      {success ? <p role="status" className="text-sm font-medium text-[var(--cp-success)]">{success}</p> : null}
      {courses === null && !error ? <p className="text-sm text-[var(--cp-muted)]" role="status">Loading courses…</p> : null}
      {courses && courses.length === 0 ? (
        <EmptyState title="No courses yet" message={semesters.length ? 'Add your first course to a semester to start tracking marks and performance.' : 'Create a semester first, then add your courses.'} actionLabel={semesters.length ? 'Add course' : 'Set up semesters'} onAction={() => { if (semesters.length) openCreate(); else navigate('/semesters') }} />
      ) : null}
      {courses && courses.length > 0 ? (
        <div className="grid gap-4 md:grid-cols-2">
          {courses.map((course) => {
            const enrollment = enrollmentByCourse.get(course.id)
            const owned = course.owner_id === student?.id
            return (
              <Card key={course.id} className="flex flex-col justify-between gap-4">
                <div>
                  <div className="flex items-start justify-between gap-3">
                    <div><p className="text-sm font-semibold text-[var(--cp-ink)]">{course.title}</p><p className="mt-1 text-xs text-[var(--cp-muted)]">{course.code}</p></div>
                    <Badge tone={enrollment?.status === 'enrolled' ? 'success' : 'neutral'}>{enrollment?.status === 'enrolled' ? 'Enrolled' : `${course.credits} credits`}</Badge>
                  </div>
                  <p className="mt-3 text-sm text-slate-600">{course.credits} credit hours{enrollment?.semester ? ` · ${enrollment.semester}` : ''}</p>
                </div>
                {enrollment?.status === 'enrolled' ? (
                  <div className="flex flex-wrap items-center justify-between gap-3"><p className="text-sm font-medium text-[var(--cp-success)]">Enrolled</p><Link to="/marks" className="text-xs font-semibold text-[var(--cp-brand)] hover:underline">Add marks</Link></div>
                ) : (
                  <Button variant="secondary" disabled={pendingCourseId === course.id} onClick={() => void handleEnroll(course.id)}>{pendingCourseId === course.id ? 'Enrolling…' : 'Enroll'}</Button>
                )}
                {owned ? <div className="flex gap-2 border-t border-[var(--cp-border)] pt-3"><Button size="sm" variant="secondary" disabled={pendingCourseId === course.id} onClick={() => openEdit(course)}>Edit</Button><Button size="sm" variant="ghost" disabled={pendingCourseId === course.id} onClick={() => void handleDelete(course)}>Delete</Button></div> : null}
              </Card>
            )
          })}
        </div>
      ) : null}
      <Modal open={editor !== null} title={editor?.mode === 'edit' ? 'Edit course' : 'Add course'} onClose={() => !saving && setEditor(null)} footer={<><Button variant="secondary" disabled={saving} onClick={() => setEditor(null)}>Cancel</Button><Button type="submit" form="course-form" disabled={saving}>{saving ? 'Saving…' : 'Save course'}</Button></>}>
        <form id="course-form" className="space-y-4" onSubmit={(event) => void handleSubmit(event)}>
          <TextField label="Course name" name="course_title" value={title} onChange={(event) => setTitle(event.target.value)} required maxLength={200} />
          <TextField label="Course code" name="course_code" value={code} onChange={(event) => setCode(event.target.value)} required maxLength={32} />
          <TextField label="Credits" name="course_credits" type="number" min="1" max="40" value={credits} onChange={(event) => setCredits(event.target.value)} required />
          {editor?.mode === 'create' ? <SelectField label="Semester" name="semester_id" value={semesterId} onChange={(event) => setSemesterId(event.target.value)} required><option value="" disabled>Select a semester</option>{semesters.map((semester) => <option key={semester.id} value={semester.id}>Semester {semester.number}{semester.is_current ? ' · Current' : ''}</option>)}</SelectField> : null}
          {semesters.length === 0 && editor?.mode === 'create' ? <Alert>Create a semester first from the Semesters page.</Alert> : null}
          {formError ? <Alert>{formError}</Alert> : null}
        </form>
      </Modal>
    </section>
  )
}
