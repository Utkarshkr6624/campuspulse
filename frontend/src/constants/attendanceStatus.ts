export const ATTENDANCE_STATUSES = ['present', 'absent', 'late', 'excused'] as const

export type AttendanceStatusOption = (typeof ATTENDANCE_STATUSES)[number]

export const ATTENDANCE_STATUS_LABELS: Record<AttendanceStatusOption, string> = {
  present: 'Present',
  absent: 'Absent',
  late: 'Late',
  excused: 'Excused',
}
