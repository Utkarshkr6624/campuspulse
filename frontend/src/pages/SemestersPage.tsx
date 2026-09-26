import { useCallback, useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { Alert } from '../components/ui/Alert.tsx'
import { Badge } from '../components/ui/Badge.tsx'
import { Button } from '../components/ui/Button.tsx'
import { Card, CardTitle } from '../components/ui/Card.tsx'
import { EmptyState } from '../components/ui/EmptyState.tsx'
import { GpaHistoryLineChart } from '../components/charts/AnalyticsCharts.tsx'
import { SelectField, TextField } from '../components/ui/Field.tsx'
import { useAuth } from '../hooks/useAuth.tsx'
import {
  addSemesterCourseHistory,
  createSemester,
  deleteSemesterCourseHistory,
  getCourses,
  getAcademicCgpa,
  getAnalyticsOverview,
  getSemester,
  getSemesters,
  setCurrentSemester,
  setupSemesters,
  updateSemesterCourseHistory,
  updateSemester,
  updateAcademicProfile,
} from '../services/api.ts'
import type { Course, Semester, SemesterCourse, SemesterCourseInput, SemesterDetail } from '../types/entities.ts'

function readableGpa(value: number | null | undefined): string {
  return value === null || value === undefined ? '—' : value.toFixed(2)
}

function statusLabel(status: Semester['status']): string {
  return status[0] + status.slice(1).toLowerCase()
}

export function SemestersPage() {
  const { student, updateStudent } = useAuth()
  const [semesters, setSemesters] = useState<Semester[]>([])
  const [catalogCourses, setCatalogCourses] = useState<Course[]>([])
  const [detail, setDetail] = useState<SemesterDetail | null>(null)
  const [cgpa, setCgpa] = useState<number | null>(null)
  const [gradeLetters, setGradeLetters] = useState<string[]>([])
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [setupNumber, setSetupNumber] = useState(1)
  const [addHistoryNow, setAddHistoryNow] = useState(true)
  const [newNumber, setNewNumber] = useState('')
  const [newAcademicYear, setNewAcademicYear] = useState('')
  const [newSgpa, setNewSgpa] = useState('')
  const [newCredits, setNewCredits] = useState('')
  const [newCurrent, setNewCurrent] = useState(false)
  const [editAcademicYear, setEditAcademicYear] = useState('')
  const [editRecordedSgpa, setEditRecordedSgpa] = useState('')
  const [editRecordedCredits, setEditRecordedCredits] = useState('')
  const [officialCgpa, setOfficialCgpa] = useState('')
  const [profileSaving, setProfileSaving] = useState(false)
  const [success, setSuccess] = useState<string | null>(null)
  const [courseName, setCourseName] = useState('')
  const [catalogCourseId, setCatalogCourseId] = useState('')
  const [courseCode, setCourseCode] = useState('')
  const [credits, setCredits] = useState('3')
  const [grade, setGrade] = useState('')
  const [finalScore, setFinalScore] = useState('')
  const [component, setComponent] = useState('')
  const [editingId, setEditingId] = useState<number | null>(null)

  const refresh = useCallback(async (preferredId?: number | null) => {
    setError(null)
    const [next, cgpaResult, analytics, catalog] = await Promise.all([
      getSemesters(),
      getAcademicCgpa(),
      getAnalyticsOverview(),
      getCourses(),
    ])
    setSemesters(next)
    setCgpa(cgpaResult.value)
    setGradeLetters(analytics.available_grade_letters)
    setCatalogCourses(catalog)
    setSelectedId((previousId) => {
      const nextId = preferredId ?? previousId
      const selected = next.find((item) => item.id === nextId) ?? next.find((item) => item.is_current) ?? next[0]
      return selected?.id ?? null
    })
  }, [])

  useEffect(() => {
    let active = true
    void refresh().catch((caught: unknown) => {
      if (active) setError(caught instanceof Error ? caught.message : 'Could not load semesters.')
    }).finally(() => {
      if (active) setLoading(false)
    })
    return () => { active = false }
  }, [refresh])

  useEffect(() => {
    if (selectedId === null) return
    let active = true
    getSemester(selectedId).then((next) => {
      if (active) setDetail(next)
    }).catch((caught: unknown) => {
      if (active) setError(caught instanceof Error ? caught.message : 'Could not load semester details.')
    })
    return () => { active = false }
  }, [selectedId, semesters])

  const current = useMemo(() => semesters.find((item) => item.is_current) ?? null, [semesters])
  const gpaHistory = useMemo(
    () => semesters
      .filter((item) => item.gpa.value !== null)
      .map((item) => ({ semester: `Sem ${item.number}`, gpa: item.gpa.value as number })),
    [semesters],
  )
  const visibleDetail = detail?.id === selectedId ? detail : null

  useEffect(() => {
    if (!visibleDetail) return
    setEditAcademicYear(visibleDetail.academic_year ?? '')
    setEditRecordedSgpa(visibleDetail.recorded_sgpa == null ? '' : String(visibleDetail.recorded_sgpa))
    setEditRecordedCredits(String(visibleDetail.recorded_credits ?? 0))
  }, [visibleDetail])

  useEffect(() => {
    setOfficialCgpa(student?.official_cgpa == null ? '' : String(student.official_cgpa))
  }, [student?.official_cgpa])

  async function runAction(action: () => Promise<unknown>, preferredId?: number | null) {
    setSaving(true)
    setError(null)
    setSuccess(null)
    try {
      await action()
      await refresh(preferredId)
      setSuccess('Changes saved successfully.')
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'The request could not be completed.')
    } finally {
      setSaving(false)
    }
  }

  async function finishSetup() {
    setSaving(true)
    setError(null)
    try {
      const created = await setupSemesters(setupNumber)
      const initialSelection = addHistoryNow && setupNumber > 1
        ? created.find((item) => item.number === 1)?.id
        : created.find((item) => item.is_current)?.id
      await refresh(initialSelection)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Academic setup could not be saved.')
    } finally {
      setSaving(false)
    }
  }

  function editCourse(course: SemesterCourse) {
    setEditingId(course.id)
    setCourseName(course.course_name)
    setCatalogCourseId(course.course_id === null ? '' : String(course.course_id))
    setCourseCode(course.course_code ?? '')
    setCredits(String(course.credits))
    setGrade(course.grade)
    setFinalScore(course.final_score === null ? '' : String(course.final_score))
    setComponent(course.course_component ?? '')
  }

  function resetCourseForm() {
    setEditingId(null)
    setCourseName('')
    setCatalogCourseId('')
    setCourseCode('')
    setCredits('3')
    setGrade('')
    setFinalScore('')
    setComponent('')
  }

  async function saveCourse(event: FormEvent) {
    event.preventDefault()
    if (!detail || detail.id !== selectedId) return
    const input: SemesterCourseInput = {
      course_id: catalogCourseId ? Number(catalogCourseId) : null,
      course_name: courseName.trim(),
      course_code: courseCode.trim() || null,
      credits: Number(credits),
      grade: grade || null,
      final_score: finalScore === '' ? null : Number(finalScore),
      course_component: component ? component as SemesterCourseInput['course_component'] : null,
    }
    setSaving(true)
    setError(null)
    try {
      if (editingId === null) {
        await addSemesterCourseHistory(detail.id, input)
      } else {
        await updateSemesterCourseHistory(detail.id, editingId, input)
      }
      resetCourseForm()
      await refresh(detail.id)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Course history could not be saved.')
    } finally {
      setSaving(false)
    }
  }

  async function saveSemester(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const number = Number(newNumber)
    const sgpa = newSgpa === '' ? null : Number(newSgpa)
    const recordedCredits = newCredits === '' ? 0 : Number(newCredits)
    if (!Number.isInteger(number) || number < 1 || number > 8) {
      setError('Semester number must be between 1 and 8.')
      return
    }
    if (sgpa !== null && (!Number.isFinite(sgpa) || sgpa < 0 || sgpa > 10 || recordedCredits < 1)) {
      setError('Enter an SGPA from 0 to 10 and its credits.')
      return
    }
    setSaving(true)
    setError(null)
    setSuccess(null)
    try {
      const created = await createSemester({
        number,
        set_current: newCurrent,
        academic_year: newAcademicYear.trim() || null,
        recorded_sgpa: sgpa,
        recorded_credits: recordedCredits,
      })
      await refresh(created.id)
      setSuccess(`Semester ${number} saved successfully.`)
      setNewNumber('')
      setNewAcademicYear('')
      setNewSgpa('')
      setNewCredits('')
      setNewCurrent(false)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Semester could not be saved.')
    } finally {
      setSaving(false)
    }
  }

  async function saveOfficialCgpa(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const value = officialCgpa.trim() === '' ? null : Number(officialCgpa)
    if (value !== null && (!Number.isFinite(value) || value < 0 || value > 10)) {
      setError('Official CGPA must be between 0 and 10.')
      return
    }
    setProfileSaving(true)
    setError(null)
    setSuccess(null)
    try {
      const updatedStudent = await updateAcademicProfile(value)
      updateStudent(updatedStudent)
      setSuccess('Official CGPA saved. Calculated CGPA remains separate.')
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Official CGPA could not be saved.')
    } finally {
      setProfileSaving(false)
    }
  }

  async function saveSemesterDetails(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!visibleDetail) return
    const sgpa = editRecordedSgpa.trim() === '' ? null : Number(editRecordedSgpa)
    const recordedCredits = Number(editRecordedCredits || 0)
    if (sgpa !== null && (!Number.isFinite(sgpa) || sgpa < 0 || sgpa > 10 || recordedCredits < 1)) {
      setError('Enter an SGPA from 0 to 10 and its credits.')
      return
    }
    setSaving(true)
    setError(null)
    setSuccess(null)
    try {
      await updateSemester(visibleDetail.id, {
        academic_year: editAcademicYear.trim() || null,
        recorded_sgpa: sgpa,
        recorded_credits: recordedCredits,
      })
      await refresh(visibleDetail.id)
      setSuccess(`Semester ${visibleDetail.number} updated successfully.`)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Semester details could not be saved.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <section className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="cp-kicker">Academic journey</p>
          <h2 className="cp-page-title mt-2">Your semesters</h2>
          <p className="mt-1 max-w-2xl text-sm text-[var(--cp-muted)]">
            Organize your academic history and keep current course activity connected to your semester.
          </p>
        </div>
        <Card className="min-w-44">
          <p className="text-xs font-medium text-[var(--cp-muted)]">Calculated CGPA</p>
          <p className="mt-1 text-2xl font-semibold">{readableGpa(cgpa)}</p>
          <p className="mt-2 text-xs text-[var(--cp-muted)]">Official / recorded: {readableGpa(officialCgpa === '' ? null : Number(officialCgpa))}</p>
        </Card>
      </div>

      {error ? <Alert>{error}</Alert> : null}
      {success ? <p role="status" className="text-sm font-medium text-[var(--cp-success)]">{success}</p> : null}
      {loading ? <p role="status" className="text-sm text-[var(--cp-muted)]">Loading academic history…</p> : null}

      {!loading && (semesters.length === 0 || current === null) ? (
        <Card className="space-y-5">
          <div>
            <CardTitle>Welcome to CampusPulse</CardTitle>
            <p className="mt-2 text-sm text-[var(--cp-muted)]">Let’s set up your academic profile. What semester are you currently studying in?</p>
          </div>
          <div className="grid gap-4 sm:grid-cols-[1fr_auto] sm:items-end">
            <SelectField label="Current semester" value={setupNumber} onChange={(event) => setSetupNumber(Number(event.target.value))}>
              {Array.from({ length: 8 }, (_, index) => index + 1).map((number) => (
                <option key={number} value={number}>Semester {number}</option>
              ))}
            </SelectField>
            <Button disabled={saving} onClick={() => void finishSetup()}>
              {saving ? 'Saving…' : 'Set up semesters'}
            </Button>
          </div>
          {setupNumber > 1 ? (
            <label className="flex items-start gap-3 text-sm text-[var(--cp-ink)]">
              <input type="checkbox" checked={addHistoryNow} onChange={(event) => setAddHistoryNow(event.target.checked)} className="mt-1" />
              <span><span className="font-medium">Yes, add previous semesters now</span><span className="mt-1 block text-[var(--cp-muted)]">We’ll open Semester 1 so you can enter any history you have. You can also skip and add it later.</span></span>
            </label>
          ) : <p className="text-sm text-[var(--cp-muted)]">You can add previous or future semesters later.</p>}
        </Card>
      ) : null}

      {!loading && semesters.length > 0 ? (
        <>
        <div className="cp-panel flex gap-2 overflow-x-auto p-3 sm:p-4" aria-label="Academic journey">
          {semesters.map((semester, index) => (
            <div key={semester.id} className="flex min-w-[9.5rem] flex-1 items-center gap-2">
              <button type="button" aria-pressed={selectedId === semester.id} onClick={() => setSelectedId(semester.id)} className={`min-w-0 flex-1 rounded-[0.8rem] border px-3 py-3 text-left transition ${selectedId === semester.id ? 'border-[#c7d9cc] bg-[var(--cp-brand-wash)]' : 'border-transparent hover:border-[var(--cp-border)] hover:bg-[var(--cp-surface-raised)]'}`}>
                <span className="flex items-center gap-2"><span className={`h-2 w-2 rounded-full ${semester.is_current ? 'bg-[var(--cp-success)]' : 'bg-[#bac6be]'}`} /><span className="text-xs font-semibold text-[var(--cp-ink)]">Semester {semester.number}</span></span>
                <span className="mt-2 block text-[0.68rem] text-[var(--cp-muted)]">{semester.academic_year ? `${semester.academic_year} · ` : ''}{semester.is_current ? 'Current period' : `${statusLabel(semester.status)} · ${semester.total_credits} credits`}</span>
                <span className="mt-1 block text-xs font-semibold text-[var(--cp-brand)]">SGPA {readableGpa(semester.gpa.value)}</span>
              </button>
              {index < semesters.length - 1 ? <span aria-hidden="true" className="hidden h-px w-4 shrink-0 bg-[var(--cp-border)] sm:block" /> : null}
            </div>
          ))}
        </div>
        <div className="grid gap-6 xl:grid-cols-[0.85fr_1.4fr]">
          <div className="space-y-4">
            <Card className="space-y-3">
              <CardTitle>Current semester</CardTitle>
              {current ? (
                <div className="flex items-center justify-between gap-3 rounded-xl bg-slate-50 px-4 py-3">
                  <div>
                    <p className="font-semibold">Semester {current.number}</p>
                    <p className="text-sm text-[var(--cp-muted)]">{current.total_credits} credits · SGPA {readableGpa(current.gpa.value)}</p>
                  </div>
                  <Badge tone="success">Current</Badge>
                </div>
              ) : <p className="text-sm text-[var(--cp-muted)]">Choose a semester below to mark it current.</p>}
            </Card>
            <Card className="space-y-4">
              <div>
                <CardTitle>Academic history</CardTitle>
                <p className="mt-1 text-sm text-[var(--cp-muted)]">Select a semester to view or enter its records.</p>
              </div>
              <div className="space-y-2">
                {semesters.map((semester) => (
                  <button key={semester.id} type="button" onClick={() => setSelectedId(semester.id)}
                    className={`w-full rounded-xl border px-4 py-3 text-left transition ${selectedId === semester.id ? 'border-[var(--cp-brand)] bg-blue-50/60' : 'border-[var(--cp-border)] hover:bg-slate-50'}`}>
                    <span className="flex items-center justify-between gap-3">
                      <span className="font-medium">Semester {semester.number}</span>
                      <Badge tone={semester.status === 'CURRENT' ? 'success' : 'neutral'}>{statusLabel(semester.status)}</Badge>
                    </span>
                    <span className="mt-1 block text-sm text-[var(--cp-muted)]">SGPA {readableGpa(semester.gpa.value)} · {semester.total_credits} credits</span>
                  </button>
                ))}
              </div>
              {gpaHistory.length >= 2 ? (
                <div className="border-t border-[var(--cp-border)] pt-4">
                  <p className="mb-2 text-sm font-semibold">SGPA history</p>
                  <GpaHistoryLineChart data={gpaHistory} />
                </div>
              ) : null}
              <form className="grid gap-3 border-t border-[var(--cp-border)] pt-4 sm:grid-cols-2" onSubmit={(event) => void saveSemester(event)}>
                <TextField label="Semester number" type="number" min="1" max="8" value={newNumber} onChange={(event) => setNewNumber(event.target.value)} required />
                <TextField label="Academic year (optional)" placeholder="2026–27" value={newAcademicYear} onChange={(event) => setNewAcademicYear(event.target.value)} />
                <TextField label="Recorded SGPA (optional)" type="number" min="0" max="10" step="0.01" value={newSgpa} onChange={(event) => setNewSgpa(event.target.value)} />
                <TextField label="Credits for recorded SGPA" type="number" min="0" max="500" value={newCredits} onChange={(event) => setNewCredits(event.target.value)} />
                <label className="flex items-center gap-2 text-sm sm:col-span-2"><input type="checkbox" checked={newCurrent} onChange={(event) => setNewCurrent(event.target.checked)} /> Set this as the current semester</label>
                <Button type="submit" variant="secondary" disabled={saving || !newNumber}>{saving ? 'Saving…' : 'Add semester'}</Button>
              </form>
              <form className="space-y-3 border-t border-[var(--cp-border)] pt-4" onSubmit={(event) => void saveOfficialCgpa(event)}>
                <div><p className="text-sm font-semibold">Official / recorded CGPA</p><p className="mt-1 text-xs text-[var(--cp-muted)]">Stored separately; it never replaces the calculated CGPA.</p></div>
                <div className="flex items-end gap-3"><TextField label="Official CGPA" type="number" min="0" max="10" step="0.01" value={officialCgpa} onChange={(event) => setOfficialCgpa(event.target.value)} /><Button type="submit" variant="secondary" disabled={profileSaving}>{profileSaving ? 'Saving…' : 'Save'}</Button></div>
              </form>
            </Card>
          </div>

          <div className="space-y-4">
            {visibleDetail ? (
              <Card className="space-y-5">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <CardTitle>Semester {visibleDetail.number} details</CardTitle>
                    <p className="mt-1 text-sm text-[var(--cp-muted)]">{statusLabel(visibleDetail.status)} · {visibleDetail.total_credits} credits · SGPA {readableGpa(visibleDetail.gpa.value)}</p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Link to="/assistant" state={{ prompt: `Analyze my results for Semester ${visibleDetail.number}.` }} className="inline-flex min-h-9 items-center rounded-[var(--cp-radius-sm)] px-3 text-xs font-semibold text-[var(--cp-brand)] hover:bg-[var(--cp-brand-wash)]">Analyze this semester</Link>
                    {!visibleDetail.is_current ? <Button size="sm" variant="secondary" disabled={saving} onClick={() => void runAction(() => setCurrentSemester(visibleDetail.id), visibleDetail.id)}>Make current</Button> : null}
                  </div>
                </div>

                <form className="grid gap-3 rounded-xl border border-[var(--cp-border)] bg-slate-50/60 p-4 sm:grid-cols-2" onSubmit={(event) => void saveSemesterDetails(event)}>
                  <TextField label="Academic year" placeholder="2026–27" value={editAcademicYear} onChange={(event) => setEditAcademicYear(event.target.value)} />
                  <TextField label="Recorded SGPA (optional)" type="number" min="0" max="10" step="0.01" value={editRecordedSgpa} onChange={(event) => setEditRecordedSgpa(event.target.value)} />
                  <TextField label="Credits for recorded SGPA" type="number" min="0" max="500" value={editRecordedCredits} onChange={(event) => setEditRecordedCredits(event.target.value)} />
                  <div className="flex items-end"><Button type="submit" variant="secondary" disabled={saving}>{saving ? 'Saving…' : 'Save semester details'}</Button></div>
                  <p className="text-xs text-[var(--cp-muted)] sm:col-span-2">Calculated SGPA from course results takes precedence. Recorded SGPA is used when course-level results are not available.</p>
                </form>

                {visibleDetail.is_current ? (
                  <div className="space-y-3">
                    <h3 className="text-sm font-semibold">Current courses</h3>
                    {visibleDetail.enrolled_courses.length === 0 ? <EmptyState title="No courses yet" message="Enroll in courses to connect them to this semester." /> : (
                      <div className="space-y-2">
                        {visibleDetail.enrolled_courses.map((item) => (
                          <div key={item.course.id} className="rounded-xl border border-[var(--cp-border)] px-4 py-3">
                            <div className="flex flex-wrap justify-between gap-2">
                              <p className="font-medium">{item.course.title} <span className="text-[var(--cp-muted)]">{item.course.code}</span></p>
                              <p className="text-sm">{item.credits} credits · {item.grade ?? 'Grade pending'} · {item.grade_point?.toFixed(2) ?? '—'} points</p>
                            </div>
                            <p className="mt-1 text-xs text-[var(--cp-muted)]">{item.final_score === null ? 'Marks in progress' : `Final score ${item.final_score}%`} · {item.assessments.length} recorded assessments</p>
                          </div>
                        ))}
                      </div>
                    )}
                    <p className="text-xs text-[var(--cp-muted)]">Manage enrollments, marks, attendance, exams, and assignments in their existing sections.</p>
                  </div>
                ) : visibleDetail.status === 'PREVIOUS' ? (
                  <div className="space-y-3">
                    <h3 className="text-sm font-semibold">Previous-semester courses</h3>
                    {visibleDetail.enrolled_courses.length > 0 ? (
                      <div className="space-y-2">
                        {visibleDetail.enrolled_courses.map((item) => (
                          <div key={`enrolled-${item.course.id}`} className="rounded-xl border border-[var(--cp-border)] px-4 py-3">
                            <div className="flex flex-wrap justify-between gap-2">
                              <p className="font-medium">{item.course.title} <span className="text-[var(--cp-muted)]">{item.course.code}</span></p>
                              <p className="text-sm">{item.credits} credits · {item.grade ?? 'Grade pending'} · {item.grade_point?.toFixed(2) ?? '—'} points</p>
                            </div>
                            <p className="mt-1 text-xs text-[var(--cp-muted)]">{item.final_score === null ? 'Marks in progress' : `Final score ${item.final_score}%`}</p>
                          </div>
                        ))}
                      </div>
                    ) : null}
                    {visibleDetail.historical_courses.length === 0 ? <EmptyState title="No history entered" message="Add the courses and grades you have available. You can also leave this semester empty and return later." /> : (
                      <div className="overflow-x-auto">
                        <table className="w-full text-left text-sm">
                          <thead className="text-xs text-[var(--cp-muted)]"><tr><th className="py-2">Course</th><th>Credits</th><th>Grade</th><th>Points</th><th>Score</th><th /></tr></thead>
                          <tbody>{visibleDetail.historical_courses.map((course) => (
                            <tr key={course.id} className="border-t border-[var(--cp-border)]">
                              <td className="py-3">{course.course_name}<span className="ml-2 text-xs text-[var(--cp-muted)]">{course.course_code}</span>{course.course_component ? <span className="ml-2 text-xs text-[var(--cp-muted)]">{course.course_component}</span> : null}</td>
                              <td>{course.credits}</td><td>{course.grade}</td><td>{course.grade_point.toFixed(2)}</td><td>{course.final_score === null ? '—' : `${course.final_score}%`}</td>
                              <td className="whitespace-nowrap text-right"><button className="px-2 text-[var(--cp-brand)]" onClick={() => editCourse(course)}>Edit</button><button className="px-2 text-red-700" onClick={() => void runAction(() => deleteSemesterCourseHistory(visibleDetail.id, course.id), visibleDetail.id)}>Delete</button></td>
                            </tr>
                          ))}</tbody>
                        </table>
                      </div>
                    )}
                    <form className="grid gap-3 border-t border-[var(--cp-border)] pt-4 sm:grid-cols-2" onSubmit={(event) => void saveCourse(event)}>
                      <div className="sm:col-span-2"><CardTitle>{editingId === null ? 'Add a course result' : 'Edit course result'}</CardTitle></div>
                      <SelectField label="Link an existing course (optional)" value={catalogCourseId} onChange={(event) => {
                        const selected = catalogCourses.find((item) => item.id === Number(event.target.value))
                        setCatalogCourseId(event.target.value)
                        if (selected) {
                          setCourseName(selected.title)
                          setCourseCode(selected.code)
                          setCredits(String(selected.credits))
                        }
                      }}>
                        <option value="">Enter a historical course</option>
                        {catalogCourses.map((course) => <option key={course.id} value={course.id}>{course.code} · {course.title}</option>)}
                      </SelectField>
                      <TextField label="Course name" value={courseName} onChange={(event) => setCourseName(event.target.value)} required />
                      <TextField label="Course code (optional)" value={courseCode} onChange={(event) => setCourseCode(event.target.value)} />
                      <TextField label="Credits" type="number" min="1" max="40" value={credits} onChange={(event) => setCredits(event.target.value)} required />
                      <SelectField label="Grade" value={grade} onChange={(event) => setGrade(event.target.value)}>
                        <option value="">Select a grade</option>
                        {gradeLetters.map((letter) => <option key={letter} value={letter}>{letter}</option>)}
                      </SelectField>
                      <TextField label="Final score (optional)" type="number" min="0" max="100" step="0.01" value={finalScore} onChange={(event) => setFinalScore(event.target.value)} />
                      <SelectField label="Course component (optional)" value={component} onChange={(event) => setComponent(event.target.value)}>
                        <option value="">Not specified</option><option value="THEORY">Theory</option><option value="LAB">Lab</option><option value="COMBINED">Theory and lab</option><option value="OTHER">Other</option>
                      </SelectField>
                      <div className="flex gap-2 sm:col-span-2">
                        <Button type="submit" disabled={saving || (grade === '' && finalScore === '')}>{saving ? 'Saving…' : editingId === null ? 'Save course' : 'Save changes'}</Button>
                        {editingId !== null ? <Button type="button" variant="secondary" onClick={resetCourseForm}>Cancel</Button> : null}
                      </div>
                      <p className="text-xs text-[var(--cp-muted)] sm:col-span-2">Grade points are derived from the configured grading scheme. Add either a grade or a final score; if both are entered they must agree.</p>
                    </form>
                  </div>
                ) : (
                  <EmptyState title="Upcoming semester" message="This semester will become the current term when you are ready. You can make it current when it starts." />
                )}
              </Card>
            ) : null}
          </div>
        </div>
        </>
      ) : null}
    </section>
  )
}
