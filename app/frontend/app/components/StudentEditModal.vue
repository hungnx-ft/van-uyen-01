<script setup lang="ts">
import type { User } from '~/types'
import { isApiEnabled } from '~/utils/api'
const props = defineProps<{ student: User; mode: 'reset' | 'move' }>(),
  emit = defineEmits<{ close: [] }>()
const { data, upsert, resetRemoteStudentPassword, moveRemoteStudent } = useDatabase(),
  { requireTeacher } = useAuth(),
  { show } = useToast()
const password = ref(''),
  classId = ref(props.student.classId || data.value.classes[0]?.id || '')
async function submit() {
  try {
    requireTeacher()
    if (props.mode === 'reset') {
      if (!password.value.trim()) return
      if (isApiEnabled()) await resetRemoteStudentPassword(props.student.id, password.value)
      else upsert('users', { ...props.student, password: password.value })
    } else {
      const c = data.value.classes.find((c) => c.id === classId.value)
      if (!c) throw new Error('Chọn lớp hợp lệ.')
      if (isApiEnabled()) await moveRemoteStudent(props.student.id, c.id)
      else
        upsert('users', {
          ...props.student,
          classId: c.id,
          className: c.name,
          isClassStudent: true,
        })
    }
    show('Đã cập nhật học sinh!')
    emit('close')
  } catch (e) {
    show((e as Error).message)
  }
}
</script>
<template>
  <BaseModal
    :title="`${mode === 'reset' ? 'Đặt lại mật khẩu' : student.isClassStudent ? 'Chuyển lớp' : 'Thêm vào lớp'}: ${student.fullName}`"
    @close="emit('close')"
  >
    <form class="modal-content" @submit.prevent="submit">
      <div class="input-group">
        <label v-if="mode === 'reset'">
          Mật khẩu mới
          <input v-model="password" type="password" class="input-control" required />
        </label>
        <label v-else>
          Lớp mới
          <select v-model="classId" class="input-control" required>
            <option v-for="c in data.classes" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
        </label>
      </div>
      <button class="btn btn-primary">Lưu</button>
    </form>
  </BaseModal>
</template>
