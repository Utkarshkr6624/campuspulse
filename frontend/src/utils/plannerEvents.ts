import type { Assignment, Exam, PlannerEvent } from '../types/entities.ts'
import { examTypeLabel } from '../constants/examTypes.ts'
import { ASSIGNMENT_PRIORITY_LABELS, ASSIGNMENT_STATUS_LABELS } from '../constants/assignmentEnums.ts'

function formatTime(value: string | null): string | null {
  if (!value) {
    return null
  }
  const [hours, minutes] = value.split(':')
  const date = new Date()
  date.setHours(Number(hours), Number(minutes), 0, 0)
  return date.toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' })
}

function examUrgency(exam: Exam): PlannerEvent['urgency'] {
  if (exam.days_until < 0) {
    return 'later'
  }
  if (exam.days_until === 0) {
    return 'today'
  }
  if (exam.days_until <= 7) {
    return 'soon'
  }
  return 'later'
}

function assignmentUrgency(assignment: Assignment): PlannerEvent['urgency'] {
  if (assignment.status === 'COMPLETED') {
    return 'done'
  }
  if (assignment.is_overdue) {
    return 'overdue'
  }
  if (assignment.is_due_today) {
    return 'today'
  }
  if (assignment.days_until <= 7) {
    return 'soon'
  }
  return 'later'
}

export function examToPlannerEvent(exam: Exam): PlannerEvent {
  const start = formatTime(exam.start_time)
  const end = formatTime(exam.end_time)
  let timeLabel: string | null = null
  if (start && end) {
    timeLabel = `${start} – ${end}`
  } else if (start) {
    timeLabel = start
  }

  return {
    id: `exam-${exam.id}`,
    kind: 'exam',
    title: exam.title,
    courseCode: exam.course.code,
    courseTitle: exam.course.title,
    date: exam.exam_date,
    timeLabel,
    meta: `${examTypeLabel(exam.exam_type)}${exam.location ? ` · ${exam.location}` : ''}`,
    sourceId: exam.id,
    urgency: examUrgency(exam),
  }
}

export function assignmentToPlannerEvent(assignment: Assignment): PlannerEvent {
  return {
    id: `assignment-${assignment.id}`,
    kind: 'assignment',
    title: assignment.title,
    courseCode: assignment.course.code,
    courseTitle: assignment.course.title,
    date: assignment.due_date,
    timeLabel: formatTime(assignment.due_time),
    meta: `${ASSIGNMENT_STATUS_LABELS[assignment.status]} · ${ASSIGNMENT_PRIORITY_LABELS[assignment.priority]}`,
    sourceId: assignment.id,
    urgency: assignmentUrgency(assignment),
  }
}

export function buildUpcomingEvents(exams: Exam[], assignments: Assignment[]): PlannerEvent[] {
  const events = [
    ...exams.filter((exam) => exam.is_upcoming).map(examToPlannerEvent),
    ...assignments
      .filter((item) => item.status !== 'COMPLETED' && item.days_until >= 0)
      .map(assignmentToPlannerEvent),
  ]
  return events.sort((a, b) => {
    if (a.date === b.date) {
      return a.title.localeCompare(b.title)
    }
    return a.date.localeCompare(b.date)
  })
}

export function buildCalendarEvents(exams: Exam[], assignments: Assignment[]): PlannerEvent[] {
  const events = [...exams.map(examToPlannerEvent), ...assignments.map(assignmentToPlannerEvent)]
  return events.sort((a, b) => a.date.localeCompare(b.date) || a.title.localeCompare(b.title))
}

export function relativeDayLabel(daysUntil: number): string {
  if (daysUntil < 0) {
    return `${Math.abs(daysUntil)} day${Math.abs(daysUntil) === 1 ? '' : 's'} ago`
  }
  if (daysUntil === 0) {
    return 'Today'
  }
  if (daysUntil === 1) {
    return 'Tomorrow'
  }
  return `In ${daysUntil} days`
}
