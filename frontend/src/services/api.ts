import type {
  AcademicSummary,
  AnalyticsOverview,
  Assignment,
  AssignmentInput,
  AssignmentPriority,
  AssignmentStatus,
  AssignmentUpdateInput,
  AttendanceAnalytics,
  AttendanceInput,
  AttendanceOverview,
  AttendanceRecord,
  AttendanceUpdateInput,
  Course,
  CourseAnalytics,
  CourseAttendanceSummary,
  CourseMark,
  CourseMarkInput,
  CourseMarkUpdateInput,
  CoursePerformance,
  Enrollment,
  Exam,
  ExamInput,
  ExamType,
  ExamUpdateInput,
  GpaRead,
  GpaSimulationCourseInput,
  GpaSimulationResponse,
  InsightsResponse,
  MarksOverview,
  PerformanceTrend,
  Student,
} from '../types/entities.ts'
import { request } from './http.ts'

function toQuery(params: Record<string, string | number | boolean | undefined | null>): string {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === '') {
      continue
    }
    search.set(key, String(value))
  }
  const text = search.toString()
  return text ? `?${text}` : ''
}

export function getStudents(): Promise<Student[]> {
  return request<Student[]>('/api/students')
}

export function getCourses(): Promise<Course[]> {
  return request<Course[]>('/api/courses')
}

export function getEnrollments(): Promise<Enrollment[]> {
  return request<Enrollment[]>('/api/enrollments')
}

export function createEnrollment(courseId: number, semester = 'Current'): Promise<Enrollment> {
  return request<Enrollment>('/api/enrollments', {
    method: 'POST',
    body: { course_id: courseId, status: 'enrolled', semester },
  })
}

export function getMarks(): Promise<CourseMark[]> {
  return request<CourseMark[]>('/api/marks')
}

export function getMarksOverview(): Promise<MarksOverview> {
  return request<MarksOverview>('/api/marks/overview')
}

export function getMarksForCourse(courseId: number): Promise<CourseMark[]> {
  return request<CourseMark[]>(`/api/marks/courses/${courseId}`)
}

export function createMark(input: CourseMarkInput): Promise<CourseMark> {
  return request<CourseMark>('/api/marks', { method: 'POST', body: input })
}

export function updateMark(markId: number, input: CourseMarkUpdateInput): Promise<CourseMark> {
  return request<CourseMark>(`/api/marks/${markId}`, { method: 'PATCH', body: input })
}

export function deleteMark(markId: number): Promise<void> {
  return request<void>(`/api/marks/${markId}`, { method: 'DELETE' })
}

export function getAttendanceOverview(): Promise<AttendanceOverview> {
  return request<AttendanceOverview>('/api/attendance/overview')
}

export function getAttendanceForCourse(courseId: number): Promise<CourseAttendanceSummary> {
  return request<CourseAttendanceSummary>(`/api/attendance/courses/${courseId}`)
}

export function createAttendance(input: AttendanceInput): Promise<AttendanceRecord> {
  return request<AttendanceRecord>('/api/attendance', { method: 'POST', body: input })
}

export function updateAttendance(recordId: number, input: AttendanceUpdateInput): Promise<AttendanceRecord> {
  return request<AttendanceRecord>(`/api/attendance/${recordId}`, { method: 'PATCH', body: input })
}

export function deleteAttendance(recordId: number): Promise<void> {
  return request<void>(`/api/attendance/${recordId}`, { method: 'DELETE' })
}

export function getAcademicSummary(): Promise<AcademicSummary> {
  return request<AcademicSummary>('/api/academic/summary')
}

export function getAcademicCourses(): Promise<CoursePerformance[]> {
  return request<CoursePerformance[]>('/api/academic/courses')
}

export function getAcademicGpa(semester?: string): Promise<GpaRead> {
  const query = semester ? `?semester=${encodeURIComponent(semester)}` : ''
  return request<GpaRead>(`/api/academic/gpa${query}`)
}

export function getAcademicCgpa(): Promise<GpaRead> {
  return request<GpaRead>('/api/academic/cgpa')
}

export function getExams(params: {
  upcoming?: boolean
  course_id?: number
  exam_type?: ExamType
  date_from?: string
  date_to?: string
} = {}): Promise<Exam[]> {
  return request<Exam[]>(`/api/exams${toQuery(params)}`)
}

export function createExam(input: ExamInput): Promise<Exam> {
  return request<Exam>('/api/exams', { method: 'POST', body: input })
}

export function updateExam(examId: number, input: ExamUpdateInput): Promise<Exam> {
  return request<Exam>(`/api/exams/${examId}`, { method: 'PATCH', body: input })
}

export function deleteExam(examId: number): Promise<void> {
  return request<void>(`/api/exams/${examId}`, { method: 'DELETE' })
}

export function getAssignments(params: {
  upcoming?: boolean
  completed?: boolean
  course_id?: number
  priority?: AssignmentPriority
  status?: AssignmentStatus
} = {}): Promise<Assignment[]> {
  return request<Assignment[]>(`/api/assignments${toQuery(params)}`)
}

export function createAssignment(input: AssignmentInput): Promise<Assignment> {
  return request<Assignment>('/api/assignments', { method: 'POST', body: input })
}

export function updateAssignment(assignmentId: number, input: AssignmentUpdateInput): Promise<Assignment> {
  return request<Assignment>(`/api/assignments/${assignmentId}`, { method: 'PATCH', body: input })
}

export function deleteAssignment(assignmentId: number): Promise<void> {
  return request<void>(`/api/assignments/${assignmentId}`, { method: 'DELETE' })
}

export function getAnalyticsOverview(): Promise<AnalyticsOverview> {
  return request<AnalyticsOverview>('/api/analytics/overview')
}

export function getAnalyticsCourses(): Promise<CourseAnalytics[]> {
  return request<CourseAnalytics[]>('/api/analytics/courses')
}

export function getAnalyticsPerformance(): Promise<PerformanceTrend> {
  return request<PerformanceTrend>('/api/analytics/performance')
}

export function getAnalyticsAttendance(): Promise<AttendanceAnalytics> {
  return request<AttendanceAnalytics>('/api/analytics/attendance')
}

export function getAnalyticsInsights(): Promise<InsightsResponse> {
  return request<InsightsResponse>('/api/analytics/insights')
}

export function simulateGpa(courses: GpaSimulationCourseInput[]): Promise<GpaSimulationResponse> {
  return request<GpaSimulationResponse>('/api/analytics/gpa-simulation', {
    method: 'POST',
    body: { courses },
  })
}
