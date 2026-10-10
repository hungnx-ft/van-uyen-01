<script setup lang="ts">
import { exportRawDatabase } from '~/utils/storage'
defineProps<{ message: string }>()
defineEmits<{ retry: [] }>()
const { show } = useToast()
function download() {
  try {
    const blob = new Blob([exportRawDatabase(localStorage)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'van-uyen-du-lieu-goc.json'
    link.click()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  } catch {
    show('Trình duyệt đang chặn đọc dữ liệu. Hãy cho phép lưu trữ rồi thử lại.')
  }
}
</script>
<template>
  <section class="card" style="margin: 40px auto; max-width: 700px" role="alert">
    <h1 class="font-heading text-primary mb-3">Chưa thể mở dữ liệu</h1>
    <p class="mb-3">{{ message }}</p>
    <p class="text-light mb-3">
      Bạn có thể tải bản sao dữ liệu gốc để kiểm tra. Sau khi khắc phục lỗi hoặc cho phép bộ nhớ
      trình duyệt, hãy thử lại.
    </p>
    <div class="flex gap-2" style="flex-wrap: wrap">
      <button class="btn btn-outline" @click="download">Tải bản sao dữ liệu gốc</button>
      <button class="btn btn-primary" @click="$emit('retry')">Thử lại</button>
    </div>
  </section>
</template>
