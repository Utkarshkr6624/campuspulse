import { useCallback, useEffect, useMemo, useState } from 'react'
import { QueryState } from '../components/QueryState.tsx'
import { Badge } from '../components/ui/Badge.tsx'
import { Button } from '../components/ui/Button.tsx'
import { Card } from '../components/ui/Card.tsx'
import { createEnrollment, getCourses, getEnrollments } from '../services/api.ts'
import { ApiError } from '../services/http.ts'
import type { Course, Enrollment } from '../types/entities.ts'

export function CoursesPage() {
  const [courses, setCourses] = useState<Course[] | null>(null)
  const [enrollments, setEnrollments] = useState<Enrollment[]>([])
  const [error, setError] = useState<string | null>(null)
  const [pendingCourseId, setPendingCourseId] = useState<number | null>(null)

  const load = useCallback(async () => {
    setError(null)
    try {
      const [nextCourses, nextEnrollments] = await Promise.all([getCourses(), getEnrollments()])
      setCourses(nextCourses)
      setEnrollments(nextEnrollments)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Could not load courses.')
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const enrollmentByCourse = useMemo(() => {
    const map = new Map<number, Enrollment>()
    for (const enrollment of enrollments) {
      map.set(enrollment.course_id, enrollment)
    }
    return map
  }, [enrollments])

  async function handleEnroll(courseId: number) {
    setPendingCourseId(courseId)
    try {
      await createEnrollment(courseId)
      await load()
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'Could not enroll.')
    } finally {
      setPendingCourseId(null)
    }
  }

  return (
    <section className="space-y-6">
      <p className="max-w-2xl text-sm leading-6 text-[var(--cp-muted)]">
        Browse the course catalog and enroll to unlock marks tracking for each subject.
      </p>
      <QueryState
        data={courses}
        error={error}
        loading={courses === null && error === null}
        loadingLabel="Loading courses"
        emptyTitle="No courses yet"
        emptyMessage="No courses have been added to CampusPulse yet."
      >
        {(items) => (
          <div className="grid gap-4 md:grid-cols-2">
            {items.map((course) => {
              const enrollment = enrollmentByCourse.get(course.id)
              return (
                <Card key={course.id} className="flex flex-col justify-between gap-4">
                  <div>
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-[var(--cp-ink)]">{course.title}</p>
                        <p className="mt-1 text-xs text-[var(--cp-muted)]">{course.code}</p>
                      </div>
                      <Badge tone={enrollment?.status === 'enrolled' ? 'success' : 'neutral'}>
                        {enrollment?.status === 'enrolled' ? 'Enrolled' : `${course.credits} credits`}
                      </Badge>
                    </div>
                    <p className="mt-3 text-sm text-slate-600">{course.credits} credit hours</p>
                  </div>
                  {enrollment?.status === 'enrolled' ? (
                    <p className="text-sm font-medium text-teal-800">You are enrolled in this course.</p>
                  ) : (
                    <Button
                      variant="secondary"
                      disabled={pendingCourseId === course.id}
                      onClick={() => void handleEnroll(course.id)}
                    >
                      {pendingCourseId === course.id ? 'Enrolling' : 'Enroll'}
                    </Button>
                  )}
                </Card>
              )
            })}
          </div>
        )}
      </QueryState>
    </section>
  )
}
