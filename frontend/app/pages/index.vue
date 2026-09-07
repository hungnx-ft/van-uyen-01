<script setup lang="ts">
const { data } = useDatabase(),
  { user } = useAuth()
if (user.value?.role === 'teacher') navigateTo('/analytics', { replace: true })
watch(() => user.value?.role, (role) => {
  if (role === 'teacher') navigateTo('/analytics', { replace: true })
})
const results = computed(() => data.value.results.filter((r) => r.studentId === user.value?.id))
</script>
<template>
  <section class="panel">
    <h2 class="section-title">🏡 Chào mừng tới Khu Vườn Văn Chương</h2>
    <div
      class="stat-grid"
      style="grid-template-columns: 1fr 1fr; max-width: 600px; margin: 0 auto 20px"
    >
      <div class="stat-card">
        <div class="stat-value">{{ results.filter((r) => r.examType === 'practice').length }}</div>
        <div class="stat-label">Đề luyện tập đã làm</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ results.filter((r) => r.examType === 'mock').length }}</div>
        <div class="stat-label">Đề thi thử đã làm</div>
      </div>
    </div>
  </section>
</template>
