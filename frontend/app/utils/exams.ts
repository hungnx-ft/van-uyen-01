import type { Exam, ExamType, Question, Result } from '../types'
export const practiceGroups = [
  { id: 'doc-hieu', label: '📖 Thực hành Đọc hiểu (25p)' },
  { id: 'viet-doan', label: '✍️ Viết đoạn văn (35p)' },
  { id: 'viet-bai', label: '📝 Viết bài văn (60p)' },
  { id: 'doc-hieu-lop-6', label: '📖 Đọc hiểu · Lớp 6' },
  { id: 'doc-hieu-lop-7', label: '📖 Đọc hiểu · Lớp 7' },
  { id: 'doc-hieu-lop-8', label: '📖 Đọc hiểu · Lớp 8' },
  { id: 'doc-hieu-lop-9', label: '📖 Đọc hiểu · Lớp 9' },
  { id: 'viet-doan-lop-6', label: '✍️ Viết đoạn · Lớp 6' },
  { id: 'viet-doan-lop-7', label: '✍️ Viết đoạn · Lớp 7' },
  { id: 'viet-doan-lop-8', label: '✍️ Viết đoạn · Lớp 8' },
  { id: 'viet-doan-lop-9', label: '✍️ Viết đoạn · Lớp 9' },
  { id: 'viet-bai-lop-6', label: '📝 Viết bài · Lớp 6' },
  { id: 'viet-bai-lop-7', label: '📝 Viết bài · Lớp 7' },
  { id: 'viet-bai-lop-8', label: '📝 Viết bài · Lớp 8' },
  { id: 'viet-bai-lop-9', label: '📝 Viết bài · Lớp 9' },
  { id: 'giua-ki-lop-6', label: '🧪 Giữa kì · Lớp 6' },
  { id: 'giua-ki-lop-7', label: '🧪 Giữa kì · Lớp 7' },
  { id: 'giua-ki-lop-8', label: '🧪 Giữa kì · Lớp 8' },
  { id: 'giua-ki-lop-9', label: '🧪 Giữa kì · Lớp 9' },
  { id: 'cuoi-ki-lop-6', label: '📚 Cuối kì · Lớp 6' },
  { id: 'cuoi-ki-lop-7', label: '📚 Cuối kì · Lớp 7' },
  { id: 'cuoi-ki-lop-8', label: '📚 Cuối kì · Lớp 8' },
  { id: 'cuoi-ki-lop-9', label: '📚 Cuối kì · Lớp 9' },
  { id: 'vao-10-lop-9', label: '🎯 Đề vào 10 · Lớp 9' },
]
export const mockGroups = [
  { id: 'vao-10', label: '📝 Ôn thi vào 10 (Đại trà)' },
  { id: 'hsg', label: '🏆 Ôn thi HSG, Chuyên' },
  { id: 'giua-ki-lop-6', label: '🧪 Giữa kì · Lớp 6' },
  { id: 'giua-ki-lop-7', label: '🧪 Giữa kì · Lớp 7' },
  { id: 'giua-ki-lop-8', label: '🧪 Giữa kì · Lớp 8' },
  { id: 'giua-ki-lop-9', label: '🧪 Giữa kì · Lớp 9' },
  { id: 'cuoi-ki-lop-6', label: '📚 Cuối kì · Lớp 6' },
  { id: 'cuoi-ki-lop-7', label: '📚 Cuối kì · Lớp 7' },
  { id: 'cuoi-ki-lop-8', label: '📚 Cuối kì · Lớp 8' },
  { id: 'cuoi-ki-lop-9', label: '📚 Cuối kì · Lớp 9' },
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

function practiceBaseGroup(group: string) {
  if (group.startsWith('doc-hieu-lop-')) return 'doc-hieu'
  if (group.startsWith('viet-doan-lop-')) return 'viet-doan'
  if (group.startsWith('viet-bai-lop-')) return 'viet-bai'
  if (group.startsWith('giua-ki-lop-') || group.startsWith('cuoi-ki-lop-')) return 'dinh-ky'
  if (group === 'vao-10-lop-9') return 'vao-10'
  return group
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
  const normalizedGroup = type === 'practice' ? practiceBaseGroup(group) : group
  const scorePattern =
    type === 'mock'
      ? [0.75, 0.75, 1, 1, 0.5, 2, 4]
      : normalizedGroup === 'vao-10'
        ? [0.8, 0.8, 0.8, 0.8, 0.8, 2, 4]
        : normalizedGroup === 'viet-doan'
          ? [2]
          : normalizedGroup === 'viet-bai'
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
  const normalizedGroup = type === 'practice' ? practiceBaseGroup(group) : group
  return (
    (type === 'mock'
      ? 120
      : normalizedGroup === 'dinh-ky'
        ? 90
        : normalizedGroup === 'vao-10'
          ? 120
          : normalizedGroup === 'doc-hieu'
            ? 25
            : normalizedGroup === 'viet-doan'
              ? 35
              : normalizedGroup === 'viet-bai'
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
