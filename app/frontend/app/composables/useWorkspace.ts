import type { Exam, ExamType, Result } from '~/types'
export function useWorkspace() {
  const state = useState<{
    exam: Exam
    type: ExamType
    mode: 'take' | 'review' | 'grade'
    result?: Result
  } | null>('workspace', () => null)
  const { data } = useDatabase(),
    { user, isTeacher } = useAuth(),
    { show } = useToast()
  function start(type: ExamType, exam: Exam) {
    if (!user.value || isTeacher.value) return
    state.value = { type, exam: JSON.parse(JSON.stringify(exam)), mode: 'take' }
  }
  function openResult(result: Result, grade = false) {
    if (!user.value || (!isTeacher.value && result.studentId !== user.value.id)) return
    if (grade && !isTeacher.value) return
    const exam =
      result.examSnapshot ||
      data.value[result.examType === 'practice' ? 'practice_exams' : 'mock_exams'].find(
        (e) => e.id === result.examId,
      )
    if (!exam) {
      show('Đề gốc đã bị xóa, không thể mở bài làm này.')
      return
    }
    state.value = {
      exam: JSON.parse(JSON.stringify(exam)),
      type: result.examType,
      mode: grade ? 'grade' : 'review',
      result: JSON.parse(JSON.stringify(result)),
    }
  }
  return {
    state,
    start,
    openResult,
    close: () => {
      state.value = null
    },
  }
}
