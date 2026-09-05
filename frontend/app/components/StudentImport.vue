<script setup lang="ts">
import type { User } from '~/types'
const { data, set } = useDatabase(),
  { requireTeacher } = useAuth(),
  { readNames } = useExcel(),
  { show } = useToast()
const classId = ref(data.value.classes[0]?.id || ''),
  file = ref<File>(),
  busy = ref(false),
  input = ref<HTMLInputElement>()
watch(
  () => data.value.classes.length,
  () => {
    if (!classId.value) classId.value = data.value.classes[0]?.id || ''
  },
)
async function submit() {
  if (busy.value) return
  busy.value = true
  try {
    requireTeacher()
    const c = data.value.classes.find((c) => c.id === classId.value)
    if (!c) throw new Error('Hãy tạo và chọn lớp trước nha!')
    if (!file.value) throw new Error('Vui lòng chọn file Excel!')
    const names = await readNames(file.value)
    if (!names.length) throw new Error('Không tìm thấy danh sách học sinh!')
    const ids = new Set(data.value.users.map((u) => u.id))
    const users: User[] = names.map((name) => {
      const base = name
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .replace(/đ/gi, 'd')
        .toLowerCase()
        .replace(/\s+/g, '')
      let id = base + Math.floor(10 + Math.random() * 90)
      while (ids.has(id)) id = base + crypto.randomUUID().slice(0, 8)
      ids.add(id)
      return {
        id,
        password: 'demo@123',
        role: 'student',
        fullName: name,
        classId: c.id,
        className: c.name,
        schoolName: 'THCS Yên Phong',
        isClassStudent: true,
      }
    })
    set('users', [...data.value.users, ...users])
    file.value = undefined
    if (input.value) input.value.value = ''
    show(`Tạo thành công ${users.length} tài khoản lớp ${c.name}! ⚡`)
  } catch (e) {
    show((e as Error).message)
  } finally {
    busy.value = false
  }
}
</script>
<template>
  <form @submit.prevent="submit">
    <h3 class="font-heading mb-3 text-primary">Tạo Tài Khoản Hàng Loạt</h3>
    <div class="input-group">
      <label>
        Chọn Lớp
        <select v-model="classId" class="input-control" required>
          <option v-for="c in data.classes" :key="c.id" :value="c.id">
            {{ c.name }} ({{ c.year }})
          </option>
        </select>
      </label>
    </div>
    <div class="input-group">
      <label>
        Tải lên File Excel danh sách Học sinh (Cột đầu tiên chứa tên)
        <input
          ref="input"
          type="file"
          class="input-control"
          accept=".xlsx,.xls"
          @change="file = ($event.target as HTMLInputElement).files?.[0]"
        />
      </label>
    </div>
    <button class="btn btn-accent w-full" :disabled="busy">
      {{ busy ? 'Đang đọc Excel...' : '⚡ Tạo Tài Khoản Nhanh' }}
    </button>
  </form>
</template>
