<script setup lang="ts">
import type { Exam, ExamType } from '~/types'
import { newQuestions, questionLabel, practiceGroups, mockGroups } from '~/utils/exams'
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
        questions: newQuestions(props.type, props.group),
      },
)
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
  requested.value = ''
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
