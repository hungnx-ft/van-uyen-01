<script setup lang="ts">
import type { Exam, ExamType } from '~/types'
import { duration, newQuestions, questionLabel, practiceGroups, mockGroups } from '~/utils/exams'
const props = defineProps<{ type: ExamType; exam?: Exam; group: string }>(),
  emit = defineEmits<{ save: [exam: Exam]; close: [] }>()
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
if (props.exam && !form.durationMinutes)
  form.durationMinutes = duration(props.type, props.exam.targetGroup) / 60
const questionCount = ref(form.questions.length)
const requested = ref('')
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
  if (props.type === 'practice') form.questions = newQuestions(props.type, value)
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
    }
  })
  questionCount.value = count
}
</script>
<template>
  <BaseModal
    :title="`${exam ? '🌻 Sửa' : '🌻 Thêm'} Đề ${type === 'practice' ? 'Luyện Tập' : 'Thi Thử'}`"
    @close="emit('close')"
  >
    <form class="modal-content" @submit.prevent="emit('save', JSON.parse(JSON.stringify(form)))">
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
      <div class="input-group">
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
      <h4 class="font-heading mb-3 text-primary">Phần Câu hỏi & Hướng dẫn chấm</h4>
      <div
        v-for="(q, i) in form.questions"
        :key="`${form.targetGroup}-${i}`"
        class="question-block"
      >
        <strong>{{ questionLabel(type, i, q.score) }}</strong>
        <div class="form-row mt-2">
          <label v-if="form.questions.length > 1">
            Câu hỏi
            <textarea v-model="q.q" class="input-control" placeholder="Nhập câu hỏi..." required />
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
