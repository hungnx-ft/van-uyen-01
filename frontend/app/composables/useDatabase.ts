import type { Database, Exam, Result } from '~/types'
import { emptyDatabase } from '~/utils/storage'
import { createLocalDatabase } from '~/repositories/localDatabase'
import { apiRequest, isApiEnabled } from '~/utils/api'

export function useDatabase() {
  const data = useState<Database>('database', emptyDatabase)
  const ready = useState('database-ready', () => false)
  const error = useState('database-error', () => '')
  function initialize() {
    if (ready.value) return
    error.value = ''
    try {
      const loaded = createLocalDatabase(localStorage).initialize()
      data.value = loaded
      ready.value = true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Không thể đọc dữ liệu trình duyệt.'
    }
  }
  function refresh() {
    try {
      data.value = createLocalDatabase(localStorage).read()
      error.value = ''
      ready.value = true
    } catch (e) {
      ready.value = false
      error.value = e instanceof Error ? e.message : 'Không thể đọc dữ liệu trình duyệt.'
    }
  }
  function set<K extends keyof Database>(table: K, rows: Database[K]) {
    if (!ready.value) throw new Error('Kho dữ liệu chưa sẵn sàng.')
    const saved = createLocalDatabase(localStorage).save(table, rows)
    // Publish state only after persistence succeeds.
    Object.assign(data.value, { [table]: saved })
  }
  function upsert<K extends keyof Database>(table: K, row: Database[K][number]) {
    const rows = [...data.value[table]] as Database[K][number][]
    const index = rows.findIndex((item) => item.id === row.id)
    if (index < 0) rows.push(row)
    else rows[index] = row
    set(table, rows as Database[K])
  }
  function remove<K extends keyof Database>(table: K, id: string) {
    set(table, data.value[table].filter((row) => row.id !== id) as Database[K])
  }
  async function syncRemote() {
    if (!isApiEnabled()) return
    const [theory, practice, mock, assignments, classes, students] = await Promise.all([
      apiRequest<ApiTheory[]>('/theory/'),
      apiRequest<ApiExam[]>('/exams/practice'),
      apiRequest<ApiExam[]>('/exams/mock'),
      apiRequest<ApiAssignment[]>('/assignments/').catch(() => []),
      apiRequest<ApiClass[]>('/classes/').catch(() => []),
      apiRequest<ApiStudentPage>('/users/students?limit=100').catch(() => ({ items: [] })),
    ])
    data.value = {
      ...data.value,
      theory_articles: theory.map(mapTheory),
      practice_exams: practice.map((exam) => mapExam(exam)),
      mock_exams: mock.map((exam) => mapExam(exam)),
      assignments: assignments.map(mapAssignment),
      classes: classes.map((item) => ({
        id: String(item.id),
        name: item.name,
        year: item.year || '',
      })),
      users: [
        ...data.value.users.filter((user) => user.role === 'teacher'),
        ...students.items.map(mapStudent),
      ],
    }
    const [studentSubmissions, teacherSubmissions] = await Promise.all([
      apiRequest<ApiSubmission[]>('/submissions/my-submissions').catch(() => []),
      apiRequest<ApiSubmission[]>('/submissions/teacher-submissions').catch(() => []),
    ])
    const submissions = [...studentSubmissions, ...teacherSubmissions]
    data.value.results = submissions
      .filter(
        (submission, index, all) => all.findIndex((item) => item.id === submission.id) === index,
      )
      .map((submission) => mapSubmission(submission, data.value))
  }
  async function createRemoteTheory(article: Database['theory_articles'][number]) {
    const created = await apiRequest<ApiTheory>('/theory/', {
      method: 'POST',
      body: JSON.stringify({
        title: article.title,
        content_type: article.format,
        content: article.content || article.fileData || '',
        main_category: article.mainCat,
        sub_category: article.subCat,
        description: article.desc,
        icon: article.icon,
      }),
    })
    const mapped = mapTheory(created)
    data.value.theory_articles = [...data.value.theory_articles, mapped]
    return mapped
  }
  async function updateRemoteTheory(article: Database['theory_articles'][number]) {
    const updated = await apiRequest<ApiTheory>(`/theory/${Number(article.id)}`, {
      method: 'PATCH',
      body: JSON.stringify({
        title: article.title,
        content_type: article.format,
        content: article.content || article.fileData || '',
        main_category: article.mainCat,
        sub_category: article.subCat,
        description: article.desc,
        icon: article.icon,
      }),
    })
    const mapped = mapTheory(updated)
    data.value.theory_articles = data.value.theory_articles.map((item) =>
      item.id === mapped.id ? mapped : item,
    )
    return mapped
  }
  async function deleteRemoteTheory(articleId: string) {
    await apiRequest(`/theory/${Number(articleId)}`, { method: 'DELETE' })
    data.value.theory_articles = data.value.theory_articles.filter((item) => item.id !== articleId)
  }
  async function createRemoteExam(
    exam: Database['practice_exams'][number],
    type: 'practice' | 'mock',
  ) {
    const endpoint = type === 'practice' ? '/exams/practice' : '/exams/mock'
    const payload = {
      title: exam.title,
      target_group: exam.targetGroup,
      passage: exam.passage,
      genre: exam.genre,
      questions: exam.questions.map((question, index) => ({
        content: question.q,
        max_score: question.score,
        answer_key: question.a,
        ...(type === 'mock' ? { section: index < 5 ? 1 : 2 } : {}),
      })),
    }
    const created = await apiRequest<ApiExam>(endpoint, {
      method: 'POST',
      body: JSON.stringify(payload),
    })
    const mapped = mapExam(created)
    const table = type === 'practice' ? 'practice_exams' : 'mock_exams'
    data.value[table] = [...data.value[table], mapped]
    return mapped
  }
  async function createRemoteAssignment(exam: Exam, type: 'practice' | 'mock', classId: string) {
    const assignment = await apiRequest<ApiAssignment>('/assignments/', {
      method: 'POST',
      body: JSON.stringify({
        class_id: Number(classId),
        exam_type: type === 'practice' ? 'Practice' : 'Mock',
        practice_exam_id: type === 'practice' ? Number(exam.id) : null,
        mock_exam_id: type === 'mock' ? Number(exam.id) : null,
        exam_title: exam.title,
        instructions: '',
      }),
    })
    const mapped = mapAssignment(assignment)
    data.value.assignments = [...data.value.assignments, mapped]
    return mapped
  }
  async function updateRemoteExam(exam: Exam, type: 'practice' | 'mock') {
    const endpoint =
      type === 'practice' ? `/exams/practice/${Number(exam.id)}` : `/exams/mock/${Number(exam.id)}`
    const payload = {
      title: exam.title,
      target_group: exam.targetGroup,
      passage: exam.passage,
      genre: exam.genre,
      questions: exam.questions.map((question, index) => ({
        content: question.q,
        max_score: question.score,
        answer_key: question.a,
        ...(type === 'mock' ? { section: index < 5 ? 1 : 2 } : {}),
      })),
    }
    const updated = await apiRequest<ApiExam>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(payload),
    })
    const mapped = mapExam(updated)
    const table = type === 'practice' ? 'practice_exams' : 'mock_exams'
    data.value[table] = data.value[table].map((item) => (item.id === mapped.id ? mapped : item))
    return mapped
  }
  async function deleteRemoteExam(examId: string, type: 'practice' | 'mock') {
    await apiRequest(`/exams/${type}/${Number(examId)}`, { method: 'DELETE' })
    const table = type === 'practice' ? 'practice_exams' : 'mock_exams'
    data.value[table] = data.value[table].filter((item) => item.id !== examId)
    data.value.assignments = data.value.assignments.filter(
      (item) => !(item.examId === examId && item.examType === type),
    )
  }
  async function createRemoteClass(name: string, year: string) {
    const created = await apiRequest<ApiClass>('/classes/', {
      method: 'POST',
      body: JSON.stringify({ name, year }),
    })
    const mapped = { id: String(created.id), name: created.name, year: created.year || '' }
    data.value.classes = [...data.value.classes, mapped]
    return mapped
  }
  async function resetRemoteStudentPassword(studentId: string, password: string) {
    const student = await apiRequest<ApiStudent>(`/users/students/${Number(studentId)}/password`, {
      method: 'PUT',
      body: JSON.stringify({ password }),
    })
    const mapped = mapStudent(student)
    data.value.users = data.value.users.map((user) => (user.id === mapped.id ? mapped : user))
    return mapped
  }
  async function createRemoteStudent(input: {
    username: string
    password: string
    fullName: string
    classId: string
    schoolName?: string
  }) {
    const student = await apiRequest<ApiStudent>('/users/students', {
      method: 'POST',
      body: JSON.stringify({
        username: input.username,
        password: input.password,
        full_name: input.fullName,
        school_name: input.schoolName || null,
        class_id: Number(input.classId),
        role: 'Student',
      }),
    })
    const mapped = mapStudent(student)
    data.value.users = [...data.value.users, mapped]
    return mapped
  }
  async function moveRemoteStudent(studentId: string, classId: string) {
    const student = await apiRequest<ApiStudent>(
      `/classes/${Number(classId)}/students/${Number(studentId)}`,
      {
        method: 'PUT',
      },
    )
    const mapped = mapStudent(student)
    data.value.users = data.value.users.map((user) => (user.id === mapped.id ? mapped : user))
    return mapped
  }
  async function setRemoteStudentStatus(studentId: string, isActive: boolean) {
    const student = await apiRequest<ApiStudent>(`/users/students/${Number(studentId)}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ is_active: isActive }),
    })
    const mapped = mapStudent(student)
    data.value.users = data.value.users.map((user) => (user.id === mapped.id ? mapped : user))
    return mapped
  }
  async function deleteRemoteStudent(studentId: string) {
    await apiRequest(`/users/students/${Number(studentId)}`, { method: 'DELETE' })
    data.value.users = data.value.users.filter((user) => user.id !== studentId)
    data.value.results = data.value.results.filter((result) => result.studentId !== studentId)
  }
  async function createRemoteSubmission(
    exam: Exam,
    type: 'practice' | 'mock',
    answers: string[],
    attempt: number,
    submittedAt: number,
  ) {
    const questionAnswers = exam.questions.map((question, index) => {
      if (!question.id) throw new Error('Đề chưa có mã câu hỏi từ backend.')
      return type === 'practice'
        ? { practice_question_id: Number(question.id), student_answer: answers[index] || '' }
        : { mock_question_id: Number(question.id), student_answer: answers[index] || '' }
    })
    const submission = await apiRequest<ApiSubmission>('/submissions/', {
      method: 'POST',
      body: JSON.stringify({
        exam_type: type === 'practice' ? 'Practice' : 'Mock',
        practice_exam_id: type === 'practice' ? Number(exam.id) : null,
        mock_exam_id: type === 'mock' ? Number(exam.id) : null,
        answers: questionAnswers,
        attempt,
        submitted_at: new Date(submittedAt).toISOString(),
      }),
    })
    const mapped = mapSubmission(submission, data.value, exam)
    data.value.results = [...data.value.results, mapped]
    return mapped
  }
  async function gradeRemoteSubmission(result: Result, exam: Exam) {
    const scores = exam.questions.map((_, index) => {
      const answer = result.answers[`q${index}`]
      if (!answer?.answerId) throw new Error('Bài làm thiếu mã câu trả lời từ backend.')
      return {
        answer_id: Number(answer.answerId),
        score: answer.teacherScore || 0,
        teacher_comment: answer.teacherComment || null,
      }
    })
    const submission = await apiRequest<ApiSubmission>(`/submissions/${Number(result.id)}/grade`, {
      method: 'POST',
      body: JSON.stringify({ scores, teacher_comment: result.teacherComment || null }),
    })
    const mapped = mapSubmission(submission, data.value, exam)
    data.value.results = data.value.results.map((item) => (item.id === result.id ? mapped : item))
    return mapped
  }
  async function sendRemoteAntiCheat(submissionId: string) {
    await apiRequest('/anti-cheat/event', {
      method: 'POST',
      body: JSON.stringify({ submission_id: Number(submissionId), event_type: 'tab_switch' }),
    })
  }
  return {
    data,
    ready,
    error,
    initialize,
    refresh,
    set,
    upsert,
    remove,
    syncRemote,
    createRemoteTheory,
    updateRemoteTheory,
    deleteRemoteTheory,
    createRemoteExam,
    updateRemoteExam,
    deleteRemoteExam,
    createRemoteAssignment,
    createRemoteClass,
    resetRemoteStudentPassword,
    createRemoteStudent,
    moveRemoteStudent,
    setRemoteStudentStatus,
    deleteRemoteStudent,
    createRemoteSubmission,
    gradeRemoteSubmission,
    sendRemoteAntiCheat,
  }
}

interface ApiTheory {
  id: number
  title: string
  content_type: string
  content: string
  main_category?: string | null
  sub_category?: string | null
  description?: string
  icon?: string
}
interface ApiQuestion {
  id: number
  content: string
  max_score: number
  answer_key?: string
}
interface ApiExam {
  id: number
  title: string
  target_group?: string | null
  genre?: string | null
  passage: string
  questions: ApiQuestion[]
}
interface ApiAssignment {
  id: number
  class_id: number
  exam_type: 'Practice' | 'Mock'
  practice_exam_id?: number | null
  mock_exam_id?: number | null
  exam_title: string
  created_at: string
}
interface ApiClass {
  id: number
  name: string
  year: string | null
}
interface ApiStudent {
  id: number
  username: string
  full_name: string
  school_name: string | null
  class_id: number | null
  class_name: string | null
  is_active: boolean
}
interface ApiStudentPage {
  items: ApiStudent[]
}
interface ApiSubmissionAnswer {
  id: number
  student_answer: string
  score?: { score: number; teacher_comment?: string | null } | null
}
interface ApiSubmission {
  id: number
  student_id: number
  student_name?: string
  exam_type: 'Practice' | 'Mock'
  practice_exam_id?: number | null
  mock_exam_id?: number | null
  status: string
  created_at: string
  submitted_at?: string | null
  attempt: number
  self_score?: number | null
  teacher_score?: number | null
  teacher_comment?: string | null
  answers: ApiSubmissionAnswer[]
}

function mapTheory(article: ApiTheory) {
  return {
    id: String(article.id),
    title: article.title,
    mainCat: article.main_category || '',
    subCat: article.sub_category || '',
    type: article.content_type,
    format: article.content_type,
    icon: article.icon || '📚',
    desc: article.description || '',
    content: article.content,
  }
}

function mapStudent(student: ApiStudent) {
  return {
    id: String(student.id),
    password: '',
    role: 'student' as const,
    fullName: student.full_name,
    classId: student.class_id === null ? undefined : String(student.class_id),
    className: student.class_name || undefined,
    schoolName: student.school_name || undefined,
    isClassStudent: student.class_id !== null,
    isActive: student.is_active,
  }
}

function mapExam(exam: ApiExam) {
  return {
    id: String(exam.id),
    title: exam.title,
    targetGroup: exam.target_group || '',
    genre: exam.genre || undefined,
    passage: exam.passage || '',
    questions: exam.questions.map((question) => ({
      id: String(question.id),
      q: question.content,
      a: question.answer_key || '',
      score: question.max_score,
    })),
  }
}

function mapSubmission(submission: ApiSubmission, database: Database, examOverride?: Exam): Result {
  const type = submission.exam_type === 'Practice' ? 'practice' : 'mock'
  const examId = String(submission.practice_exam_id ?? submission.mock_exam_id ?? '')
  const exam =
    examOverride ||
    database[type === 'practice' ? 'practice_exams' : 'mock_exams'].find(
      (item) => item.id === examId,
    )
  const answers = Object.fromEntries(
    (exam?.questions || []).map((_, index) => {
      const apiAnswer = submission.answers[index]
      return [
        `q${index}`,
        {
          answerId: apiAnswer ? String(apiAnswer.id) : undefined,
          ans: apiAnswer?.student_answer || '',
          selfScore: 0,
          teacherScore: apiAnswer?.score?.score || 0,
          teacherComment: apiAnswer?.score?.teacher_comment || undefined,
        },
      ]
    }),
  )
  return {
    id: String(submission.id),
    studentId: String(submission.student_id),
    studentName: submission.student_name || '',
    examType: type,
    examId,
    examTitle: exam?.title || '',
    maxScore: exam?.questions.reduce((total, question) => total + question.score, 0) || 0,
    status: submission.status.toLowerCase() === 'graded' ? 'graded' : 'pending',
    answers,
    timeSpent: 0,
    submittedAt: Date.parse(submission.submitted_at || submission.created_at),
    attempt: submission.attempt,
    selfScore: submission.self_score ?? undefined,
    teacherScore: submission.teacher_score ?? undefined,
    teacherComment: submission.teacher_comment ?? undefined,
    examSnapshot: exam ? JSON.parse(JSON.stringify(exam)) : undefined,
  }
}

function mapAssignment(assignment: ApiAssignment) {
  return {
    id: String(assignment.id),
    examId: String(assignment.practice_exam_id ?? assignment.mock_exam_id ?? ''),
    examType: assignment.exam_type === 'Practice' ? ('practice' as const) : ('mock' as const),
    classId: String(assignment.class_id),
    createdAt: Date.parse(assignment.created_at),
    examTitle: assignment.exam_title,
  }
}
