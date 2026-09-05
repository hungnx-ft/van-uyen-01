export type ExamType = 'practice' | 'mock'
export interface User {
  id: string
  password: string
  role: 'teacher' | 'student'
  fullName: string
  classId?: string
  className?: string
  schoolName?: string
  isClassStudent?: boolean
}
export interface SchoolClass {
  id: string
  name: string
  year: string
}
export interface TheoryArticle {
  id: string
  title: string
  mainCat: string
  subCat: string
  type: string
  format: string
  icon: string
  desc: string
  content: string
  fileData?: string
}
export interface Question {
  q: string
  a: string
  score: number
}
export interface Exam {
  id: string
  title: string
  targetGroup: string
  genre?: string
  passage: string
  questions: Question[]
}
export interface Answer {
  ans: string
  selfScore: number
  teacherScore: number
  teacherComment?: string
}
export interface Result {
  id: string
  studentId: string
  studentName: string
  className?: string
  schoolName?: string
  classId?: string
  isClassStudent?: boolean
  examType: ExamType
  examId: string
  examTitle: string
  maxScore: number
  status: 'pending' | 'graded'
  answers: Record<string, Answer>
  timeSpent: number
  submittedAt: number
  attempt?: number
  selfScore?: number
  teacherScore?: number
  teacherComment?: string
  examSnapshot?: Exam
}
export interface Assignment {
  id: string
  examId: string
  examType: ExamType
  classId: string
  createdAt: number
  examTitle: string
}
export interface Database {
  users: User[]
  classes: SchoolClass[]
  theory_articles: TheoryArticle[]
  practice_exams: Exam[]
  mock_exams: Exam[]
  results: Result[]
  assignments: Assignment[]
}
