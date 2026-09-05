<script setup lang="ts">
import type { Exam, ExamType } from '~/types'
const props = defineProps<{ exam: Exam; type: ExamType }>(),
  emit = defineEmits<{ close: [] }>()
const { data, upsert } = useDatabase(),
  { requireTeacher } = useAuth(),
  { show } = useToast(),
  classId = ref(data.value.classes[0]?.id || '')
function submit() {
  try {
    requireTeacher()
    if (!classId.value) return
    upsert('assignments', {
      id: crypto.randomUUID(),
      examId: props.exam.id,
      examType: props.type,
      classId: classId.value,
      createdAt: Date.now(),
      examTitle: props.exam.title,
    })
    show('Đã giao đề thành công! ✅')
    emit('close')
  } catch (e) {
    show((e as Error).message)
  }
}
</script>
<template>
  <BaseModal title="Giao Đề Cho Học Sinh" @close="emit('close')">
    <form class="modal-content" @submit.prevent="submit">
      <h4 class="font-heading mb-3">Đề: {{ exam.title }}</h4>
      <template v-if="data.classes.length">
        <div class="input-group">
          <label>
            Chọn Lớp để Giao đề
            <select v-model="classId" class="input-control" required>
              <option v-for="c in data.classes" :key="c.id" :value="c.id">
                {{ c.name }} ({{ c.year }})
              </option>
            </select>
          </label>
        </div>
        <button class="btn btn-primary">Giao Đề ✅</button>
      </template>
      <p v-else>Cô cần tạo lớp học trước khi giao đề!</p>
    </form>
  </BaseModal>
</template>
