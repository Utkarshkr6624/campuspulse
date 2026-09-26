export const ASSIGNMENT_STATUSES = ['TODO', 'IN_PROGRESS', 'COMPLETED'] as const
export const ASSIGNMENT_PRIORITIES = ['LOW', 'MEDIUM', 'HIGH'] as const

export type AssignmentStatusOption = (typeof ASSIGNMENT_STATUSES)[number]
export type AssignmentPriorityOption = (typeof ASSIGNMENT_PRIORITIES)[number]

export const ASSIGNMENT_STATUS_LABELS: Record<AssignmentStatusOption, string> = {
  TODO: 'To do',
  IN_PROGRESS: 'In progress',
  COMPLETED: 'Completed',
}

export const ASSIGNMENT_PRIORITY_LABELS: Record<AssignmentPriorityOption, string> = {
  LOW: 'Low',
  MEDIUM: 'Medium',
  HIGH: 'High',
}
