export const DOCUMENT_CATEGORIES = [
  'ACADEMIC',
  'EXAMINATION',
  'ATTENDANCE',
  'FEES',
  'HOSTEL',
  'PLACEMENT',
  'GENERAL',
  'OTHER',
] as const

export type DocumentCategoryOption = (typeof DOCUMENT_CATEGORIES)[number]

export const DOCUMENT_CATEGORY_LABELS: Record<DocumentCategoryOption, string> = {
  ACADEMIC: 'Academic',
  EXAMINATION: 'Examination',
  ATTENDANCE: 'Attendance',
  FEES: 'Fees',
  HOSTEL: 'Hostel',
  PLACEMENT: 'Placement',
  GENERAL: 'General',
  OTHER: 'Other',
}

export const PROCESSING_STATUS_LABELS: Record<string, string> = {
  PENDING: 'Pending',
  PROCESSING: 'Processing',
  COMPLETED: 'Processed',
  FAILED: 'Failed',
}
