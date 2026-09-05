<script setup lang="ts">
import type { Exam, ExamType, Result } from '~/types'
import { duration, totalScore, questionLabel, gradeTotal, clockText } from '~/utils/exams'
const props = defineProps<{
    session: { exam: Exam; type: ExamType; mode: 'take' | 'review' | 'grade'; result?: Result }
  }>(),
  emit = defineEmits<{ close: [] }>()
const { data, upsert } = useDatabase(),
  { user, requireTeacher } = useAuth(),
  { show } = useToast()
const exam = props.session.exam,
  type = props.session.type,
  mode = ref<'take' | 'self' | 'review' | 'grade'>(props.session.mode)
const answers = ref(exam.questions.map(() => '')),
  result = ref<Result | null>(
    props.session.result ? JSON.parse(JSON.stringify(props.session.result)) : null,
  )
const active = computed(() => mode.value === 'take')
useAntiCheat(active)
const timer = useExamTimer(duration(type, exam.targetGroup), () => {
  if (type === 'mock') {
    show('⚠️ Đã hết thời gian thi! Hệ thống tự động thu bài.')
    submit()
  } else show('⚠️ Đã hết thời gian làm bài! Hãy hoàn thành nhanh nhất có thể nhé!')
})
const confirm = ref<'close' | 'submit' | null>(null),
  busy = ref(false)
const isEssay = computed(() => type === 'practice' && exam.questions.length === 1)
const title = computed(() =>
  mode.value === 'take'
    ? exam.title
    : mode.value === 'grade'
      ? `CHẤM BÀI: ${result.value?.studentName} - ${exam.title}`
      : mode.value === 'self'
        ? `Tự đánh giá: ${exam.title}`
        : `Xem lại: ${exam.title} (Lần ${result.value?.attempt || 1})`,
)
const ranking = computed(() => {
  if (!result.value || result.value.status !== 'graded') return ''
  const list = data.value.results
    .filter((r) => r.examType === type && r.examId === exam.id && r.status === 'graded')
    .sort((a, b) => (b.teacherScore || 0) - (a.teacherScore || 0) || a.timeSpent - b.timeSpent)
  return `${list.findIndex((r) => r.id === result.value?.id) + 1} / ${list.length}`
})
onMounted(() => {
  if (mode.value === 'take') timer.start()
})
function requestClose() {
  if (mode.value === 'take') confirm.value = 'close'
  else emit('close')
}
function submit() {
  if (mode.value !== 'take' || busy.value || !user.value) return
  busy.value = true
  try {
    const record: Result = {
      id: crypto.randomUUID(),
      studentId: user.value.id,
      studentName: user.value.fullName,
      className: user.value.className,
      schoolName: user.value.schoolName,
      isClassStudent: user.value.isClassStudent,
      classId: user.value.classId,
      examType: type,
      examId: exam.id,
      examTitle: exam.title,
      maxScore: totalScore(exam),
      status: 'pending',
      answers: Object.fromEntries(
        exam.questions.map((_, i) => [
          `q${i}`,
          { ans: answers.value[i] || '', selfScore: 0, teacherScore: 0 },
        ]),
      ),
      timeSpent: timer.elapsed.value,
      submittedAt: Date.now(),
      attempt:
        data.value.results.filter(
          (r) => r.studentId === user.value!.id && r.examId === exam.id && r.examType === type,
        ).length + 1,
      examSnapshot: JSON.parse(JSON.stringify(exam)),
    }
    upsert('results', record)
    timer.stop()
    result.value = record
    if (type === 'practice') mode.value = 'self'
    else {
      mode.value = 'review'
      show('Nộp bài thi thành công! Chờ cô giáo chấm nhé 🌸')
      emit('close')
    }
  } catch (e) {
    show((e as Error).message)
  } finally {
    busy.value = false
    confirm.value = null
  }
}
function saveGrade() {
  if (!result.value) return
  try {
    const record = JSON.parse(JSON.stringify(result.value)) as Result
    if (mode.value === 'grade') {
      requireTeacher()
      record.teacherScore = gradeTotal(record, exam, 'teacherScore')
      record.status = 'graded'
    } else {
      record.selfScore = gradeTotal(record, exam, 'selfScore')
    }
    upsert('results', record)
    show(mode.value === 'grade' ? 'Đã chấm bài thành công! ✅' : 'Đã lưu điểm tự chấm! 🌸')
    emit('close')
  } catch (e) {
    show((e as Error).message)
  }
}
function confirmed() {
  if (confirm.value === 'submit') submit()
  else {
    timer.stop()
    confirm.value = null
    emit('close')
  }
}
function printResult() {
  window.print()
}
function label(i: number) {
  return isEssay.value
    ? `Yêu cầu: ${exam.passage}`
    : `${questionLabel(type, i, exam.questions[i]!.score)}: ${exam.questions[i]!.q}`
}
</script>
<template>
  <BaseModal :title="title" wide @close="requestClose">
    <template #actions>
      <div class="timer-badge" :style="timer.seconds.value < 0 ? { color: 'var(--danger)' } : {}">
        ⏱️
        {{ mode === 'take' ? timer.label.value : `Đã làm: ${clockText(result?.timeSpent || 0)}` }}
      </div>
      <button
        v-if="mode === 'take'"
        class="btn btn-primary"
        :disabled="busy"
        @click="confirm = 'submit'"
      >
        Nộp bài
      </button>
      <button
        v-else-if="mode === 'self' || mode === 'grade'"
        class="btn btn-primary"
        @click="saveGrade"
      >
        {{ mode === 'self' ? 'Lưu Điểm' : 'Xác nhận Điểm' }}
      </button>
      <button v-else class="btn btn-accent" @click="printResult">Tải bài (PDF)</button>
    </template>
    <div class="workspace-body">
      <div v-if="!isEssay" class="workspace-left">
        <h3 class="font-heading mb-2 text-primary">📖 Ngữ liệu</h3>
        <div class="unselectable" style="white-space: pre-wrap; font-size: 1.05rem">
          {{ exam.passage }}
        </div>
      </div>
      <div class="workspace-right">
        <template v-if="mode === 'take'">
          <QuestionInput
            v-for="(_, i) in exam.questions"
            :key="i"
            v-model="answers[i]!"
            :label="label(i)"
            :essay="isEssay"
          />
        </template>
        <template v-else-if="result">
          <div v-if="mode === 'self'" class="card mb-3" style="background: var(--warning)">
            🌸 Hãy đối chiếu bài làm với đáp án và tự chọn điểm ở Cột 3 nhé!
          </div>
          <div
            v-if="mode === 'review'"
            class="card mb-3"
            :style="{
              background: result.status === 'graded' ? 'var(--success)' : 'var(--warning)',
            }"
          >
            <template v-if="result.status === 'graded'">
              <strong>🎉 Điểm cô chấm: {{ result.teacherScore }}/{{ result.maxScore }}đ</strong>
              <p>Lời phê: {{ result.teacherComment }}</p>
              <p>🏆 Xếp hạng: {{ ranking }}</p>
            </template>
            <template v-else>⌛ Bài làm đang chờ cô Hằng chấm để được xếp hạng.</template>
          </div>
          <GradingQuestion
            v-for="(q, i) in exam.questions"
            :key="i"
            v-model="result.answers[`q${i}`]!"
            :question="q"
            :label="label(i)"
            :practice="type === 'practice'"
            :mode="mode"
            :graded="result.status === 'graded'"
          />
          <div v-if="mode === 'grade'" class="input-group">
            <label>
              Lời phê tổng hợp (Tuỳ chọn):
              <input
                v-model="result.teacherComment"
                class="input-control"
                placeholder="Bài làm tốt, cần chú ý thêm phần..."
              />
            </label>
          </div>
        </template>
      </div>
    </div>
  </BaseModal>
  <ConfirmDialog
    v-if="confirm"
    :message="
      confirm === 'submit'
        ? 'Cậu đã chắc chắn muốn nộp bài chưa?'
        : 'Bài đang làm chưa được lưu. Cậu muốn đóng và bỏ bài này?'
    "
    @close="confirm = null"
    @confirm="confirmed"
  />
</template>
