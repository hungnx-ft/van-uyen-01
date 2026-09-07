<script setup lang="ts">
import type { Exam, ExamType, Result } from '~/types'
import { duration, totalScore, questionLabel, gradeTotal, clockText } from '~/utils/exams'
import { isApiEnabled } from '~/utils/api'
const props = defineProps<{
    session: { exam: Exam; type: ExamType; mode: 'take' | 'review' | 'grade'; result?: Result }
  }>(),
  emit = defineEmits<{ close: [] }>()
const {
    data,
    upsert,
    createRemoteSubmission,
    gradeRemoteSubmission,
    sendRemoteAntiCheat,
    createRemoteAIJob,
    getRemoteAIJob,
    getRemoteAIHistory,
    applyRemoteAIJob,
    saveRemoteFeedback,
  } = useDatabase(),
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
const { tabSwitches } = useAntiCheat(active)
const timer = useExamTimer(duration(type, exam.targetGroup, exam.durationMinutes), () => {
  if (type === 'mock') {
    show('⚠️ Đã hết thời gian thi! Hệ thống tự động thu bài.')
    submit()
  } else show('⚠️ Đã hết thời gian làm bài! Hãy hoàn thành nhanh nhất có thể nhé!')
})
const confirm = ref<'close' | 'submit' | null>(null),
  busy = ref(false),
  aiBusy = ref(false),
  aiJob = ref<{
    id: number
    status: string
    provider?: string
    model?: string
    rubric_version?: number
    result?: {
      total_score?: number | null
      overall_comment?: string | null
      improvement_suggestion?: string | null
      confidence?: number | null
      answers: Array<{
        practice_question_id?: number | null
        mock_question_id?: number | null
        ai_score: number
        ai_question_comment?: string | null
      }>
    } | null
  } | null>(null)
const aiHistory = ref<Array<NonNullable<typeof aiJob.value>>>([])
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
  if (mode.value === 'grade' && isApiEnabled() && result.value && /^\d+$/.test(result.value.id)) {
    getRemoteAIHistory(result.value.id)
      .then((items) => {
        aiHistory.value = items
        aiJob.value = items[0] || null
      })
      .catch(() => undefined)
  }
})
function requestClose() {
  if (mode.value === 'take') confirm.value = 'close'
  else emit('close')
}
async function submit() {
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
    const saved = isApiEnabled()
      ? await createRemoteSubmission(
          exam,
          type,
          answers.value,
          record.attempt || 1,
          record.submittedAt,
        )
      : record
    if (isApiEnabled() && tabSwitches.value > 0) {
      await Promise.all(
        Array.from({ length: tabSwitches.value }, () => sendRemoteAntiCheat(saved.id)),
      )
    }
    if (!isApiEnabled()) upsert('results', record)
    timer.stop()
    result.value = saved
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
async function saveGrade() {
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
    const saved =
      isApiEnabled() && mode.value === 'grade' ? await gradeRemoteSubmission(record, exam) : record
    if (isApiEnabled() && mode.value === 'grade') {
      await saveRemoteFeedback(
        record.id,
        record.teacherComment || '',
        record.teacherImprovementNote || '',
        !!record.feedbackPublished,
      )
    }
    result.value = saved
    if (!isApiEnabled() || mode.value !== 'grade') upsert('results', record)
    show(mode.value === 'grade' ? 'Đã chấm bài thành công! ✅' : 'Đã lưu điểm tự chấm! 🌸')
    emit('close')
  } catch (e) {
    show((e as Error).message)
  }
}
async function requestAI() {
  if (!result.value || !isApiEnabled()) return
  aiBusy.value = true
  try {
    aiJob.value = await createRemoteAIJob(result.value.id)
    aiHistory.value = [aiJob.value, ...aiHistory.value]
    show('Đã tạo yêu cầu AI chấm. Có thể tải lại trạng thái sau khi worker xử lý.')
  } catch (error) {
    show((error as Error).message)
  } finally {
    aiBusy.value = false
  }
}
async function refreshAI() {
  if (!aiJob.value) return
  aiBusy.value = true
  try {
    aiJob.value = await getRemoteAIJob(aiJob.value.id)
    aiHistory.value = aiHistory.value.map((item) =>
      item.id === aiJob.value?.id ? aiJob.value : item,
    )
  } catch (error) {
    show((error as Error).message)
  } finally {
    aiBusy.value = false
  }
}
async function applyAI() {
  if (!aiJob.value) return
  aiBusy.value = true
  try {
    aiJob.value = await applyRemoteAIJob(aiJob.value.id)
    aiHistory.value = aiHistory.value.map((item) =>
      item.id === aiJob.value?.id ? aiJob.value : item,
    )
    show('Đã áp dụng điểm AI; giáo viên có thể chỉnh sửa trước khi lưu.')
  } catch (error) {
    show((error as Error).message)
  } finally {
    aiBusy.value = false
  }
}
function aiForQuestion(index: number) {
  const questionId = Number(exam.questions[index]?.id)
  const item = aiJob.value?.result?.answers.find(
    (answer) =>
      (type === 'practice' ? answer.practice_question_id : answer.mock_question_id) === questionId,
  )
  return item ? { score: item.ai_score, comment: item.ai_question_comment } : undefined
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
              <p v-if="result.teacherImprovementNote">
                📌 Gợi ý cải thiện: {{ result.teacherImprovementNote }}
              </p>
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
            :ai-answer="mode === 'grade' ? aiForQuestion(i) : undefined"
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
            <label class="mt-2">
              Gợi ý cải thiện:
              <textarea
                v-model="result.teacherImprovementNote"
                class="input-control"
                rows="3"
                placeholder="Học sinh cần cải thiện..."
              />
            </label>
            <label class="flex items-center gap-2 mt-2">
              <input v-model="result.feedbackPublished" type="checkbox" />
              Công bố nhận xét cho học sinh
            </label>
            <div class="card mt-3" style="background: #eef4ff">
              <div class="flex gap-2" style="flex-wrap: wrap">
                <button class="btn btn-sm btn-secondary" :disabled="aiBusy" @click="requestAI">
                  🤖 Yêu cầu AI chấm
                </button>
                <button
                  v-if="aiJob"
                  class="btn btn-sm btn-outline"
                  :disabled="aiBusy"
                  @click="refreshAI"
                >
                  Tải lại AI
                </button>
                <button
                  v-if="aiJob?.status === 'completed'"
                  class="btn btn-sm btn-primary"
                  :disabled="aiBusy"
                  @click="applyAI"
                >
                  Áp dụng điểm AI
                </button>
              </div>
              <p v-if="aiJob" class="text-light mt-2">
                AI: {{ aiJob.status }}
                <span v-if="aiJob.result?.confidence != null">
                  · độ tin cậy {{ Math.round(aiJob.result.confidence * 100) }}%
                </span>
              </p>
              <p v-if="aiJob?.result?.overall_comment" class="mt-2">
                {{ aiJob.result.overall_comment }}
              </p>
              <p v-if="aiJob?.result?.improvement_suggestion" class="text-light">
                {{ aiJob.result.improvement_suggestion }}
              </p>
              <div v-if="aiHistory.length > 1" class="mt-3">
                <strong>Lịch sử các lần chấm AI</strong>
                <div
                  v-for="item in aiHistory"
                  :key="item.id"
                  class="mt-2"
                  style="border-top: 1px dashed var(--border-color); padding-top: 8px"
                >
                  <button class="btn btn-sm btn-outline" @click="aiJob = item">
                    Lần #{{ item.id }} · {{ item.status }} · {{ item.provider }} /
                    {{ item.model }} · barem v{{ item.rubric_version }}
                  </button>
                  <span v-if="item.result?.total_score != null" class="text-light ml-2">
                    {{ item.result.total_score }}đ
                  </span>
                </div>
              </div>
            </div>
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
