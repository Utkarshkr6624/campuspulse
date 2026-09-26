export const ASSESSMENT_TYPES = [
  'CAT1',
  'CAT2',
  'FAT',
  'INTERNAL',
  'LAB',
  'ASSIGNMENT',
  'OTHER',
] as const

export type AssessmentType = (typeof ASSESSMENT_TYPES)[number]

export const ASSESSMENT_TYPE_LABELS: Record<AssessmentType, string> = {
  CAT1: 'CAT 1',
  CAT2: 'CAT 2',
  FAT: 'FAT',
  INTERNAL: 'Internal',
  LAB: 'Lab',
  ASSIGNMENT: 'Assignment',
  OTHER: 'Other',
}

export function assessmentLabel(type: string): string {
  if (type in ASSESSMENT_TYPE_LABELS) {
    return ASSESSMENT_TYPE_LABELS[type as AssessmentType]
  }
  return type
}
