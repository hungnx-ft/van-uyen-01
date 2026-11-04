<script setup lang="ts">
import { isApiEnabled } from '~/utils/api'
import { DEFAULT_STUDENT_PASSWORD, studentUsername } from '~/utils/students'
const { data, set, createRemoteStudent } = useDatabase()
const { requireTeacher } = useAuth()
const { show } = useToast()
const fullName = ref('')
const classId = ref('')
const schoolName = ref('')
const busy = ref(false)
const created = ref<{ fullName: string; username: string; password: string } | null>(null)
watch(
  () => data.value.classes,
  (classes) => {
    if (!classId.value) classId.value = classes[0]?.id || ''
  },
  { immediate: true },
)
// Offline mode has no database id, so number accounts by the next free sequence.
function localUsername(name: string) {
  const used = new Set(data.value.users.map((item) => item.username || item.id))
  let next = data.value.users.length + 1
  while (used.has(studentUsername(name, next))) next++
  return studentUsername(name, next)
}
async function submit() {
  if (busy.value) return
  busy.value = true
  try {
    requireTeacher()
    const name = fullName.value.trim()
    if (!name || !classId.value) throw new Error('Vui lòng điền đủ thông tin học sinh.')
    if (isApiEnabled()) {
      const student = await createRemoteStudent({
        fullName: name,
        classId: classId.value,
        schoolName: schoolName.value.trim(),
      })
      created.value = {
        fullName: student.fullName,
        username: student.username || student.id,
        password: student.password,
      }
    } else {
      const classroom = data.value.classes.find((item) => item.id === classId.value)
      if (!classroom) throw new Error('Chọn lớp hợp lệ.')
      const username = localUsername(name)
      set('users', [
        ...data.value.users,
        {
          id: username,
          username,
          password: DEFAULT_STUDENT_PASSWORD,
          role: 'student',
          fullName: name,
          classId: classroom.id,
          className: classroom.name,
          schoolName: schoolName.value.trim() || undefined,
          isClassStudent: true,
        },
      ])
      created.value = { fullName: name, username, password: DEFAULT_STUDENT_PASSWORD }
    }
    fullName.value = ''
    schoolName.value = ''
    show('Đã tạo học sinh thành công!')
  } catch (error) {
    show((error as Error).message)
  } finally {
    busy.value = false
  }
}
</script>
<template>
  <form @submit.prevent="submit">
    <h3 class="font-heading mb-3 text-primary">Tạo Học Sinh</h3>
    <p class="text-light mb-3">
      Tài khoản tự tạo theo mẫu
      <code>hs_hovaten_mã</code>
      , mật khẩu mặc định
      <code>{{ DEFAULT_STUDENT_PASSWORD }}</code>
      . Học sinh phải đổi mật khẩu khi đăng nhập lần đầu.
    </p>
    <div class="input-group">
      <label>
        Họ và tên
        <input v-model="fullName" class="input-control" required />
      </label>
    </div>
    <div class="input-group">
      <label>
        Lớp
        <select v-model="classId" class="input-control" required>
          <option v-for="item in data.classes" :key="item.id" :value="item.id">
            {{ item.name }} ({{ item.year }})
          </option>
        </select>
      </label>
    </div>
    <div class="input-group">
      <label>
        Trường
        <input v-model="schoolName" class="input-control" />
      </label>
    </div>
    <button class="btn btn-primary w-full" :disabled="busy">Tạo tài khoản</button>
    <div v-if="created" class="card mt-3 created-account" role="status">
      <strong>{{ created.fullName }}</strong>
      <div>
        Tài khoản:
        <code>{{ created.username }}</code>
      </div>
      <div>
        Mật khẩu:
        <code>{{ created.password }}</code>
      </div>
    </div>
  </form>
</template>

<style scoped>
.created-account {
  display: grid;
  gap: 4px;
}
</style>
