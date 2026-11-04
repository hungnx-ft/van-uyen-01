<script setup lang="ts">
import type { User } from '~/types'
import { isApiEnabled } from '~/utils/api'
import { DEFAULT_STUDENT_PASSWORD } from '~/utils/students'
const props = defineProps<{ student: User; mode: 'reset' | 'move' }>(),
  emit = defineEmits<{ close: [] }>()
const { data, upsert, resetRemoteStudentPassword, moveRemoteStudent } = useDatabase(),
  { requireTeacher } = useAuth(),
  { show } = useToast()
const resetDone = ref(false),
  busy = ref(false),
  classId = ref(props.student.classId || data.value.classes[0]?.id || '')
async function submit() {
  if (busy.value) return
  busy.value = true
  try {
    requireTeacher()
    if (props.mode === 'reset') {
      if (isApiEnabled()) await resetRemoteStudentPassword(props.student.id)
      else upsert('users', { ...props.student, password: DEFAULT_STUDENT_PASSWORD })
      // Keep the dialog open so the teacher can read the new credentials.
      resetDone.value = true
      show('Đã đặt lại mật khẩu!')
      return
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
  } finally {
    busy.value = false
  }
}
</script>
<template>
  <BaseModal
    :title="`${mode === 'reset' ? 'Đặt lại mật khẩu' : student.isClassStudent ? 'Chuyển lớp' : 'Thêm vào lớp'}: ${student.fullName}`"
    @close="emit('close')"
  >
    <div v-if="mode === 'reset' && resetDone" class="modal-content" role="status">
      <p class="mb-2">Đã đặt lại mật khẩu cho {{ student.fullName }}:</p>
      <p>
        Tài khoản:
        <code>{{ student.username || student.id }}</code>
      </p>
      <p class="mb-3">
        Mật khẩu:
        <code>{{ DEFAULT_STUDENT_PASSWORD }}</code>
      </p>
      <p class="text-light mb-3">Học sinh sẽ phải đổi mật khẩu ở lần đăng nhập tiếp theo.</p>
      <button type="button" class="btn btn-primary" @click="emit('close')">Đóng</button>
    </div>
    <form v-else class="modal-content" @submit.prevent="submit">
      <div class="input-group">
        <p v-if="mode === 'reset'">
          Đặt lại mật khẩu của
          <strong>{{ student.fullName }}</strong>
          về
          <code>{{ DEFAULT_STUDENT_PASSWORD }}</code>
          ? Học sinh sẽ bị đăng xuất và phải đổi mật khẩu ở lần đăng nhập tiếp theo.
        </p>
        <label v-else>
          Lớp mới
          <select v-model="classId" class="input-control" required>
            <option v-for="c in data.classes" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
        </label>
      </div>
      <button class="btn btn-primary" :disabled="busy">
        {{ mode === 'reset' ? 'Đặt lại mật khẩu' : 'Lưu' }}
      </button>
    </form>
  </BaseModal>
</template>
