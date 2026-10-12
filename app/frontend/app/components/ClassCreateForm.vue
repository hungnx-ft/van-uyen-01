<script setup lang="ts">
import { isApiEnabled } from '~/utils/api'
const { data, set, createRemoteClass } = useDatabase(),
  { requireTeacher } = useAuth(),
  { show } = useToast()
const name = ref(''),
  year = ref('2025-2026')
async function submit() {
  try {
    requireTeacher()
    if (!name.value.trim()) return
    if (isApiEnabled()) await createRemoteClass(name.value.trim(), year.value.trim())
    else
      set('classes', [
        ...data.value.classes,
        { id: crypto.randomUUID(), name: name.value.trim(), year: year.value.trim() },
      ])
    name.value = ''
    show('Đã tạo lớp! 🍀')
  } catch (e) {
    show((e as Error).message)
  }
}
</script>
<template>
  <form @submit.prevent="submit">
    <h3 class="font-heading mb-3 text-primary">Tạo Lớp Học Mới</h3>
    <div class="input-group">
      <label>
        Tên lớp (VD: 9A1)
        <input v-model="name" class="input-control" required />
      </label>
    </div>
    <div class="input-group">
      <label>
        Năm học (VD: 2025-2026)
        <input v-model="year" class="input-control" required />
      </label>
    </div>
    <button class="btn btn-primary w-full">Tạo Lớp</button>
  </form>
</template>
