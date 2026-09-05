import type { Exam, ExamType, Question, Result } from '../types'
export const practiceGroups = [
  { id: 'doc-hieu', label: '📖 Thực hành Đọc hiểu (25p)' },
  { id: 'viet-doan', label: '✍️ Viết đoạn văn (35p)' },
  { id: 'viet-bai', label: '📝 Viết bài văn (60p)' },
]
export const mockGroups = [
  { id: 'vao-10', label: '📝 Ôn thi vào 10 (Đại trà)' },
  { id: 'hsg', label: '🏆 Ôn thi HSG, Chuyên' },
]
export const mainCategories = [
  { id: 'doc-hieu', label: '📖 Đọc hiểu' },
  { id: 'viet-doan', label: '✍️ Viết đoạn văn' },
  { id: 'viet-bai', label: '📝 Viết bài văn' },
]
export const subCategories: Record<string, { id: string; label: string }[]> = {
  'doc-hieu': [
    { id: 'doc-hieu-tho', label: '🌸 Đọc hiểu thơ' },
    { id: 'doc-hieu-truyen', label: '📖 Đọc hiểu truyện' },
    { id: 'doc-hieu-vb-thong-tin', label: '📰 Đọc hiểu VB thông tin' },
    { id: 'doc-hieu-vb-nghi-luan', label: '⚖️ Đọc hiểu VB nghị luận' },
  ],
  'viet-doan': [
    { id: 'viet-doan-nlxh', label: '✍️ Viết đoạn văn NLXH' },
    { id: 'viet-doan-nlvh', label: '✍️ Viết đoạn văn NLVH' },
  ],
  'viet-bai': [
    { id: 'viet-bai-nlxh', label: '📝 Viết bài văn NLXH' },
    { id: 'viet-bai-nlvh', label: '📝 Viết bài văn NLVH' },
  ],
}
export function questionLabel(type: ExamType, i: number, score: number) {
  const prefix =
    type === 'practice'
      ? `Câu ${i + 1}`
      : i < 5
        ? `Phần I. Đọc hiểu - Câu ${i + 1}`
        : `Phần II. Viết - Câu ${i - 4}`
  return `${prefix} (${score}đ)`
}
export function newQuestions(type: ExamType, group: string, count?: number): Question[] {
  const scorePattern =
    type === 'mock'
      ? [0.75, 0.75, 1, 1, 0.5, 2, 4]
      : group === 'viet-doan'
        ? [2]
        : group === 'viet-bai'
          ? [5]
          : [0.75, 0.75, 1, 1, 0.5]
  const total = Number.isInteger(count) && count && count > 0 ? count : scorePattern.length
  return Array.from({ length: total }, (_, index) => ({
    q: scorePattern.length === 1 ? 'Bài Viết' : '',
    a: '',
    score: scorePattern[index % scorePattern.length]!,
  }))
}
export function duration(type: ExamType, group: string, customMinutes?: number) {
  if (customMinutes && Number.isFinite(customMinutes) && customMinutes > 0) {
    return Math.round(customMinutes * 60)
  }
  return (
    (type === 'mock'
      ? 120
      : group === 'doc-hieu'
        ? 25
        : group === 'viet-doan'
          ? 35
          : group === 'viet-bai'
            ? 60
            : 45) * 60
  )
}
export function clockText(seconds: number) {
  const s = Math.abs(seconds)
  return `${seconds < 0 ? '-' : ''}${Math.floor(s / 60)
    .toString()
    .padStart(2, '0')}:${Math.floor(s % 60)
    .toString()
    .padStart(2, '0')}`
}
export function totalScore(exam: Exam) {
  return exam.questions.reduce((sum, q) => sum + q.score, 0)
}
export function scoreOptions(max: number) {
  const values = Array.from({ length: Math.floor(max * 4) + 1 }, (_, i) => i / 4)
  if (values.at(-1) !== max) values.push(max)
  return values
}
export function gradeTotal(result: Result, exam: Exam, key: 'teacherScore' | 'selfScore') {
  return exam.questions.reduce((sum, q, i) => {
    const score = Number(result.answers[`q${i}`]?.[key] ?? 0)
    if (!Number.isFinite(score) || score < 0 || score > q.score)
      throw new Error(`Điểm câu ${i + 1} phải từ 0 đến ${q.score}.`)
    return sum + score
  }, 0)
}
