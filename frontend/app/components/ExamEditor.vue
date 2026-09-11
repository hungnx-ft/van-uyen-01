<script setup lang="ts">
import type { Exam, ExamType } from '~/types'
import { duration, newQuestions, questionLabel, practiceGroups, mockGroups } from '~/utils/exams'
const props = defineProps<{ type: ExamType; exam?: Exam; group: string }>(),
  emit = defineEmits<{ save: [exam: Exam, rubricFile?: File]; close: [] }>()
const form = reactive<Exam>(
  props.exam
    ? JSON.parse(JSON.stringify(props.exam))
    : {
        id: crypto.randomUUID(),
        title: '',
        targetGroup: props.group,
        genre: 'tho',
        passage: '',
        durationMinutes: duration(props.type, props.group) / 60,
        questions: newQuestions(props.type, props.group),
      },
)
if (props.type === 'mock') {
  // Older exams did not store a section. Preserve their historical 5/remaining split.
  form.questions.forEach((question, index) => {
    question.section =
      question.section === 1 || question.section === 2 ? question.section : index < 5 ? 1 : 2
  })
}
if (props.exam && !form.durationMinutes)
  form.durationMinutes = duration(props.type, props.exam.targetGroup) / 60
const questionCount = ref(form.questions.length)
const mockSections = [1, 2] as const
const mockSectionCounts = reactive<Record<1 | 2, number>>({
  1: props.type === 'mock' ? Math.max(1, form.questions.filter((q) => q.section === 1).length) : 1,
  2: props.type === 'mock' ? Math.max(1, form.questions.filter((q) => q.section === 2).length) : 1,
})
const requested = ref('')
const rubricFile = ref<File | undefined>()
function chooseRubric(event: Event) {
  rubricFile.value = (event.target as HTMLInputElement).files?.[0]
}
function changeGroup(event: Event) {
  const value = (event.target as HTMLSelectElement).value
  if (value === form.targetGroup) return
  if (props.type === 'practice' && form.questions.some((q) => q.a || (q.q && q.q !== 'Bài Viết'))) {
    requested.value = value
    ;(event.target as HTMLSelectElement).value = form.targetGroup
  } else applyGroup(value)
}
function applyGroup(value: string) {
  form.targetGroup = value
  form.questions = newQuestions(props.type, value)
  if (props.type === 'mock') {
    form.questions.forEach((question, index) => {
      question.section = index < 5 ? 1 : 2
    })
    mockSectionCounts[1] = Math.max(1, form.questions.filter((q) => q.section === 1).length)
    mockSectionCounts[2] = Math.max(1, form.questions.filter((q) => q.section === 2).length)
  }
  questionCount.value = form.questions.length
  requested.value = ''
}
function resizeQuestions(value: unknown) {
  const parsed = Number(value)
  if (!Number.isFinite(parsed)) {
    questionCount.value = form.questions.length
    return
  }
  const count = Math.max(1, Math.min(100, Math.floor(parsed)))
  const defaults = newQuestions(props.type, form.targetGroup, count)
  form.questions = Array.from({ length: count }, (_, index) => {
    const current = form.questions[index]
    const fallback = defaults[index]!
    return {
      id: current?.id,
      q: current?.q ?? fallback.q,
      a: current?.a ?? fallback.a,
      score: current?.score ?? fallback.score,
      section: current?.section,
    }
  })
  questionCount.value = count
}
function resizeMockSection(section: 1 | 2, value: unknown) {
  const parsed = Number(value)
  if (!Number.isFinite(parsed)) return
  const count = Math.max(1, Math.min(100, Math.floor(parsed)))
  const current = form.questions.filter((question) => question.section === section)
  const defaults = newQuestions('mock', form.targetGroup, count)
  const resized = Array.from({ length: count }, (_, index) => {
    const existing = current[index]
    const fallback = defaults[index]!
    return {
      id: existing?.id,
      q: existing?.q ?? fallback.q,
      a: existing?.a ?? fallback.a,
      score: existing?.score ?? fallback.score,
      section,
    }
  })
  const other = form.questions.filter((question) => question.section !== section)
  form.questions = section === 1 ? [...resized, ...other] : [...other, ...resized]
  mockSectionCounts[section] = count
}
function sectionQuestionIndex(index: number) {
  const section = form.questions[index]?.section
  return (
    form.questions.slice(0, index).filter((question) => question.section === section).length + 1
  )
}
</script>
<template>
  <BaseModal
    :title="`${exam ? '🌻 Sửa' : '🌻 Thêm'} Đề ${type === 'practice' ? 'Luyện Tập' : 'Thi Thử'}`"
    @close="emit('close')"
  >
    <form
      class="modal-content"
      @submit.prevent="emit('save', JSON.parse(JSON.stringify(form)), rubricFile)"
    >
      <div class="input-group">
        <label>
          Tên đề
          <input v-model="form.title" class="input-control" required />
        </label>
      </div>
      <div class="form-row">
        <div v-if="type === 'practice'" class="input-group">
          <label>
            Thể loại
            <select v-model="form.genre" class="input-control">
              <option value="tho">Thơ 🌸</option>
              <option value="truyen">Truyện 🍁</option>
              <option value="thong-tin">Thông tin 🌿</option>
              <option value="nghi-luan">Nghị luận 🍀</option>
            </select>
          </label>
        </div>
        <div class="input-group">
          <label>
            {{ type === 'practice' ? 'Loại bài luyện tập' : 'Cấp độ ôn tập' }}
            <select :value="form.targetGroup" class="input-control" @change="changeGroup">
              <option
                v-for="g in type === 'practice' ? practiceGroups : mockGroups"
                :key="g.id"
                :value="g.id"
              >
                {{ g.label }}
              </option>
            </select>
          </label>
        </div>
      </div>
      <div class="input-group">
        <label>
          {{ form.questions.length === 1 ? 'Đề bài (Yêu cầu viết)' : 'Ngữ liệu đọc hiểu' }}
          <textarea v-model="form.passage" class="input-control" required />
        </label>
      </div>
      <div class="input-group">
        <label>
          Thời lượng làm bài (phút)
          <input
            v-model.number="form.durationMinutes"
            type="number"
            class="input-control"
            min="1"
            max="1440"
            step="1"
            required
          />
        </label>
        <small class="text-light">Từ 1 đến 1440 phút.</small>
      </div>
      <div v-if="type === 'practice'" class="input-group">
        <label>
          Số lượng câu hỏi
          <input
            v-model.number="questionCount"
            type="number"
            class="input-control"
            min="1"
            max="100"
            step="1"
            required
            @change="resizeQuestions(questionCount)"
          />
        </label>
        <small class="text-light">
          Từ 1 đến 100 câu. Thay đổi số lượng sẽ giữ lại nội dung câu hiện có.
        </small>
      </div>
      <div v-else class="form-row">
        <div v-for="section in mockSections" :key="section" class="input-group">
          <label>
            {{ section === 1 ? 'Số câu Phần I · Đọc hiểu' : 'Số câu Phần II · Viết' }}
            <input
              v-model.number="mockSectionCounts[section]"
              type="number"
              class="input-control"
              min="1"
              max="100"
              step="1"
              required
              @change="resizeMockSection(section, mockSectionCounts[section])"
            />
          </label>
          <small class="text-light">
            Mỗi phần có số câu riêng, nội dung đã nhập sẽ được giữ lại.
          </small>
        </div>
      </div>
      <h4 class="font-heading mb-3 text-primary">Phần Câu hỏi & Hướng dẫn chấm</h4>
      <template v-for="(q, i) in form.questions" :key="`${form.targetGroup}-${i}`">
        <h5
          v-if="type === 'mock' && (i === 0 || q.section !== form.questions[i - 1]?.section)"
          class="font-heading mt-3 mb-2 text-secondary"
        >
          {{ q.section === 1 ? 'Phần I · Đọc hiểu' : 'Phần II · Viết' }}
        </h5>
        <div class="question-block">
          <strong>
            {{
              type === 'mock'
                ? `Câu ${sectionQuestionIndex(i)} (${q.score}đ)`
                : questionLabel(type, i, q.score)
            }}
          </strong>
          <div class="form-row mt-2">
            <label v-if="form.questions.length > 1">
              Câu hỏi
              <textarea
                v-model="q.q"
                class="input-control"
                placeholder="Nhập câu hỏi..."
                required
              />
            </label>
            <label>
              Đáp án chuẩn / Hướng dẫn chấm
              <textarea
                v-model="q.a"
                class="input-control"
                placeholder="Nhập đáp án chuẩn / Hướng dẫn chấm..."
                required
              />
            </label>
          </div>
        </div>
      </template>
      <div class="input-group">
        <label>
          Barem chấm (tuỳ chọn)
          <input type="file" accept=".pdf,.docx,.txt,.md,.markdown" @change="chooseRubric" />
        </label>
        <small class="text-light">
          Có thể upload ngay khi tạo đề; hệ thống sẽ lưu barem sau khi tạo đề.
        </small>
      </div>
      <button class="btn btn-primary">Lưu Đề</button>
    </form>
  </BaseModal>
  <ConfirmDialog
    v-if="requested"
    message="Đổi loại bài sẽ tạo lại phần câu hỏi và đáp án. Tiếp tục?"
    @close="requested = ''"
    @confirm="applyGroup(requested)"
  />
</template>
