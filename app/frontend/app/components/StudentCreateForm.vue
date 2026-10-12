<script setup lang="ts">
import { isApiEnabled } from '~/utils/api'
const { data, set, createRemoteStudent } = useDatabase()
const { requireTeacher } = useAuth()
const { show } = useToast()
const fullName = ref('')
const username = ref('')
const password = ref('')
const classId = ref('')
const schoolName = ref('')
const busy = ref(false)
watch(
  () => data.value.classes,
  (classes) => {
    if (!classId.value) classId.value = classes[0]?.id || ''
  },
  { immediate: true },
)
async function submit() {
  if (busy.value) return
  busy.value = true
  try {
    requireTeacher()
    if (!fullName.value.trim() || !username.value.trim() || !password.value || !classId.value)
      throw new Error('Vui lòng điền đủ thông tin học sinh.')
    if (isApiEnabled()) {
      await createRemoteStudent({
        username: username.value.trim(),
        password: password.value,
        fullName: fullName.value.trim(),
        classId: classId.value,
        schoolName: schoolName.value.trim(),
      })
    } else {
      const classroom = data.value.classes.find((item) => item.id === classId.value)
      if (!classroom) throw new Error('Chọn lớp hợp lệ.')
      if (data.value.users.some((item) => item.id === username.value.trim()))
        throw new Error('Tên đăng nhập đã tồn tại.')
      set('users', [
        ...data.value.users,
        {
          id: username.value.trim(),
          password: password.value,
          role: 'student',
          fullName: fullName.value.trim(),
          classId: classroom.id,
          className: classroom.name,
          schoolName: schoolName.value.trim() || undefined,
          isClassStudent: true,
        },
      ])
    }
    fullName.value = ''
    username.value = ''
    password.value = ''
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
    <div class="input-group">
      <label>
        Họ và tên
        <input v-model="fullName" class="input-control" required />
      </label>
    </div>
    <div class="input-group">
      <label>
        Tên đăng nhập
        <input v-model="username" class="input-control" required />
      </label>
    </div>
    <div class="input-group">
      <label>
        Mật khẩu
        <input v-model="password" type="password" class="input-control" minlength="8" required />
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
  </form>
</template>
