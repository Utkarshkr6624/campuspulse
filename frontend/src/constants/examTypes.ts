export const EXAM_TYPES = ['CAT1', 'CAT2', 'FAT', 'QUIZ', 'LAB', 'OTHER'] as const

export type ExamTypeOption = (typeof EXAM_TYPES)[number]

export const EXAM_TYPE_LABELS: Record<ExamTypeOption, string> = {
  CAT1: 'CAT 1',
  CAT2: 'CAT 2',
  FAT: 'FAT',
  QUIZ: 'Quiz',
  LAB: 'Lab',
  OTHER: 'Other',
}

export function examTypeLabel(type: string): string {
  if (type in EXAM_TYPE_LABELS) {
    return EXAM_TYPE_LABELS[type as ExamTypeOption]
  }
  return type
}
