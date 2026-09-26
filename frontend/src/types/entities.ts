export type UserRole = 'STUDENT' | 'ADMIN'

export type Student = {
  id: number
  full_name: string
  email: string
  university_id: string
  role: UserRole
  created_at: string
  updated_at: string
}

export type Course = {
  id: number
  code: string
  title: string
  credits: number
  grading_scheme_id: number | null
  created_at: string
  updated_at: string
}

export type Enrollment = {
  id: number
  student_id: number
  course_id: number
  status: 'enrolled' | 'withdrawn'
  semester: string
  semester_id: number | null
  created_at: string
  updated_at: string
}

export type SemesterCourse = {
  id: number
  course_id: number | null
  course_name: string
  course_code: string | null
  credits: number
  grade: string
  grade_point: number
  final_score: number | null
  course_component: 'THEORY' | 'LAB' | 'COMBINED' | 'OTHER' | null
  notes: string | null
}

export type Semester = {
  id: number
  number: number
  status: 'PREVIOUS' | 'CURRENT' | 'UPCOMING'
  is_current: boolean
  course_count: number
  total_credits: number
  gpa: GpaRead
  created_at: string
  updated_at: string
}

export type SemesterDetail = Semester & {
  historical_courses: SemesterCourse[]
  enrolled_courses: CoursePerformance[]
}

export type SemesterCourseInput = {
  course_id?: number | null
  course_name: string
  course_code?: string | null
  credits: number
  grade?: string | null
  final_score?: number | null
  course_component?: 'THEORY' | 'LAB' | 'COMBINED' | 'OTHER' | null
  notes?: string | null
}

export type CourseSummary = {
  id: number
  code: string
  title: string
  credits: number
}

export type AssessmentType =
  | 'CAT1'
  | 'CAT2'
  | 'FAT'
  | 'INTERNAL'
  | 'LAB'
  | 'ASSIGNMENT'
  | 'OTHER'

export type CourseMark = {
  id: number
  student_id: number
  course_id: number
  assessment_type: AssessmentType
  marks_obtained: number
  maximum_marks: number
  assessment_date: string | null
  created_at: string
  updated_at: string
  course: CourseSummary
  percentage: number
}

export type CourseMarksGroup = {
  course: CourseSummary
  assessments: CourseMark[]
  assessment_count: number
  average_percentage: number | null
}

export type MarksOverview = {
  total_assessments: number
  courses_with_marks: number
  average_percentage: number | null
  groups: CourseMarksGroup[]
}

export type CourseMarkInput = {
  course_id: number
  assessment_type: AssessmentType
  marks_obtained: number
  maximum_marks: number
  assessment_date?: string | null
}

export type CourseMarkUpdateInput = {
  assessment_type?: AssessmentType
  marks_obtained?: number
  maximum_marks?: number
  assessment_date?: string | null
}

export type AttendanceStatus = 'present' | 'absent' | 'late' | 'excused'

export type AttendanceRecord = {
  id: number
  student_id: number
  course_id: number
  attendance_date: string
  status: AttendanceStatus
  created_at: string
  updated_at: string
  course: CourseSummary
}

export type CourseAttendanceSummary = {
  course: CourseSummary
  total_classes: number
  attended_classes: number
  missed_classes: number
  attendance_percentage: number | null
  records: AttendanceRecord[]
}

export type AttendanceOverview = {
  total_classes: number
  attended_classes: number
  missed_classes: number
  attendance_percentage: number | null
  courses_tracked: number
  courses: CourseAttendanceSummary[]
}

export type AttendanceInput = {
  course_id: number
  attendance_date: string
  status: AttendanceStatus
}

export type AttendanceUpdateInput = {
  attendance_date?: string
  status?: AttendanceStatus
}

export type AssessmentPerformance = {
  assessment_type: string
  marks_obtained: number
  maximum_marks: number
  weight_percent: number
  normalized_score: number
  weighted_contribution: number
}

export type CoursePerformance = {
  course: CourseSummary
  semester: string
  credits: number
  status: string
  final_score: number | null
  grade: string | null
  grade_point: number | null
  missing_assessment_types: string[]
  message: string | null
  assessments: AssessmentPerformance[]
}

export type GpaRead = {
  status: string
  value: number | null
  credited_courses: number
  total_credits: number
  semester: string | null
  message: string | null
}

export type AcademicSummary = {
  enrolled_courses: number
  completed_courses: number
  incomplete_courses: number
  gpa: GpaRead
  cgpa: GpaRead
  courses: CoursePerformance[]
}

export type ExamType = 'CAT1' | 'CAT2' | 'FAT' | 'QUIZ' | 'LAB' | 'OTHER'

export type Exam = {
  id: number
  student_id: number
  course_id: number
  title: string
  exam_type: ExamType
  exam_date: string
  start_time: string | null
  end_time: string | null
  location: string | null
  description: string | null
  created_at: string
  updated_at: string
  course: CourseSummary
  is_upcoming: boolean
  days_until: number
}

export type ExamInput = {
  course_id: number
  title: string
  exam_type: ExamType
  exam_date: string
  start_time?: string | null
  end_time?: string | null
  location?: string | null
  description?: string | null
}

export type ExamUpdateInput = {
  title?: string
  exam_type?: ExamType
  exam_date?: string
  start_time?: string | null
  end_time?: string | null
  location?: string | null
  description?: string | null
}

export type AssignmentStatus = 'TODO' | 'IN_PROGRESS' | 'COMPLETED'
export type AssignmentPriority = 'LOW' | 'MEDIUM' | 'HIGH'

export type Assignment = {
  id: number
  student_id: number
  course_id: number
  title: string
  description: string | null
  due_date: string
  due_time: string | null
  status: AssignmentStatus
  priority: AssignmentPriority
  created_at: string
  updated_at: string
  course: CourseSummary
  is_overdue: boolean
  is_due_today: boolean
  days_until: number
}

export type AssignmentInput = {
  course_id: number
  title: string
  description?: string | null
  due_date: string
  due_time?: string | null
  status?: AssignmentStatus
  priority?: AssignmentPriority
}

export type AssignmentUpdateInput = {
  title?: string
  description?: string | null
  due_date?: string
  due_time?: string | null
  status?: AssignmentStatus
  priority?: AssignmentPriority
}

export type PlannerEventKind = 'exam' | 'assignment'

export type PlannerEvent = {
  id: string
  kind: PlannerEventKind
  title: string
  courseCode: string
  courseTitle: string
  date: string
  timeLabel: string | null
  meta: string
  sourceId: number
  urgency: 'overdue' | 'today' | 'soon' | 'later' | 'done'
}

export type AttendanceHealth = 'HEALTHY' | 'WARNING' | 'CRITICAL' | 'UNKNOWN'
export type InsightType =
  | 'LOW_ATTENDANCE'
  | 'LOW_SCORE'
  | 'MISSING_ASSESSMENT'
  | 'PERFORMANCE_IMPROVEMENT'
  | 'PERFORMANCE_DECLINE'
  | 'UPCOMING_EXAM'
  | 'OVERDUE_ASSIGNMENT'
export type InsightSeverity = 'INFO' | 'WARNING' | 'CRITICAL'

export type GradeDistributionBucket = {
  letter: string
  count: number
}

export type AttentionCourse = {
  course: CourseSummary
  reasons: string[]
}

export type AnalyticsOverview = {
  gpa: GpaRead
  cgpa: GpaRead
  total_courses: number
  completed_courses: number
  incomplete_courses: number
  total_credits: number
  completed_credits: number
  overall_attendance: number | null
  grade_distribution: GradeDistributionBucket[]
  courses_requiring_attention: AttentionCourse[]
  available_grade_letters: string[]
  data_status: string
  message: string | null
}

export type CourseAnalytics = {
  course: CourseSummary
  semester: string
  credits: number
  status: string
  current_score: number | null
  grade: string | null
  grade_point: number | null
  completed_assessments: number
  required_assessments: number
  missing_assessments: string[]
  attendance_percentage: number | null
  attendance_health: AttendanceHealth
  message: string | null
}

export type PerformancePoint = {
  assessment_name: string
  assessment_type: string
  assessment_date: string | null
  percentage: number
  course: CourseSummary
  change_from_previous: number | null
}

export type PerformanceTrend = {
  status: string
  points: PerformancePoint[]
  message: string | null
}

export type AttendanceCourseAnalytics = {
  course: CourseSummary
  attended: number
  total: number
  missed: number
  percentage: number | null
  health: AttendanceHealth
  message: string
}

export type AttendanceAnalytics = {
  overall_percentage: number | null
  overall_health: AttendanceHealth
  overall_message: string
  courses: AttendanceCourseAnalytics[]
}

export type AcademicInsight = {
  id: string
  type: InsightType
  severity: InsightSeverity
  title: string
  message: string
  course_id: number | null
  course_code: string | null
  supporting_value: number | string | null
  navigation_target: string | null
}

export type InsightsResponse = {
  insights: AcademicInsight[]
  status: string
  message: string | null
}

export type GpaSimulationCourseInput = {
  course_id: number
  letter_grade: string
}

export type GpaSimulationCourseResult = {
  course: CourseSummary
  credits: number
  source: string
  letter_grade: string | null
  grade_point: number | null
}

export type GpaSimulationResponse = {
  label: string
  current_gpa: GpaRead
  projected_gpa: GpaRead
  courses: GpaSimulationCourseResult[]
  message: string | null
}

export type IntelligenceInsight = {
  type: string
  severity: InsightSeverity
  title: string
  description: string
  supporting_data: Record<string, number | string | null>
  source_metric: string
}

export type IntelligenceAssessment = {
  assessment_type: AssessmentType
  percentage: number
}

export type IntelligenceCourse = {
  semester_id: number | null
  semester_number: number | null
  course_id: number | null
  course_code: string | null
  course_name: string
  credits: number
  status: string
  score: number | null
  grade: string | null
  grade_point: number | null
  attendance_percentage: number | null
  attendance_health: AttendanceHealth
  performance_category: string
  assessments: IntelligenceAssessment[]
  cat1_to_cat2_change: number | null
}

export type SemesterTrendPoint = {
  semester_id: number
  semester_number: number
  status: string
  sgpa: number | null
  cumulative_gpa: number | null
  completed_credits: number
  known_credits: number
  course_count: number
  average_marks: number | null
  gpa_change: number | null
}

export type SemesterComparison = {
  first_semester_id: number
  first_semester_number: number
  second_semester_id: number
  second_semester_number: number
  sgpa_difference: number | null
  average_marks_difference: number | null
  credits_difference: number
  course_count_difference: number
  attendance_difference: number | null
  attendance_note: string
}

export type AcademicIntelligence = {
  data_status: string
  message: string | null
  current_sgpa: number | null
  previous_sgpa: number | null
  sgpa_change: number | null
  cgpa: GpaRead
  completed_credits: number
  current_semester_credits: number
  total_known_credits: number
  average_marks: number | null
  overall_attendance: number | null
  completed_courses: number
  ongoing_courses: number
  attendance_warning_threshold: number
  attendance_healthy_threshold: number
  low_score_threshold: number
  strong_score_threshold: number
  semester_trend: SemesterTrendPoint[]
  credits_by_semester: Array<{
    semester_id: number
    semester_number: number
    known_credits: number
    completed_credits: number
  }>
  courses: IntelligenceCourse[]
  course_trends: Array<Record<string, number | string | null>>
  insights: IntelligenceInsight[]
  comparison: SemesterComparison | null
}

export type DocumentCategory =
  | 'ACADEMIC'
  | 'EXAMINATION'
  | 'ATTENDANCE'
  | 'FEES'
  | 'HOSTEL'
  | 'PLACEMENT'
  | 'GENERAL'
  | 'OTHER'

export type ProcessingStatus = 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED'

export type CampusDocument = {
  id: number
  title: string
  description: string | null
  original_filename: string
  file_type: string
  file_size: number
  category: DocumentCategory
  uploaded_by: number
  processing_status: ProcessingStatus
  processing_error: string | null
  chunk_count: number
  created_at: string
  updated_at: string
}

export type DocumentChunk = {
  id: number
  document_id: number
  chunk_index: number
  content: string
  page_number: number | null
  created_at: string
}

export type DocumentContent = {
  document: CampusDocument
  chunks: DocumentChunk[]
}

export type DocumentSearchHit = {
  document_id: number
  title: string
  category: DocumentCategory
  file_type: string
  page_number: number | null
  snippet: string
  score: number
  matched_in: string
}

export type DocumentSearchResponse = {
  query: string
  total: number
  results: DocumentSearchHit[]
}

export type ChatSource = {
  document_id: number
  title: string
  page_number: number | null
  snippet: string | null
  category: string | null
}

export type ChatResponse = {
  conversation_id: number
  message_id: number
  answer: string
  sources: ChatSource[]
  tools_used: string[]
  grounding: string[]
}

export type ChatMessage = {
  id: number
  conversation_id: number
  role: 'USER' | 'ASSISTANT'
  content: string
  sources: ChatSource[]
  tools_used: string[]
  grounding: string[]
  created_at: string
}

export type ConversationSummary = {
  id: number
  title: string
  created_at: string
  updated_at: string
  message_count: number
}

export type ConversationDetail = {
  id: number
  student_id: number
  title: string
  created_at: string
  updated_at: string
  messages: ChatMessage[]
}
