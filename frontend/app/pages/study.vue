<script setup lang="ts">
const { data } = useDatabase(),
  { user } = useAuth(),
  { openResult } = useWorkspace()
const results = computed(() =>
  data.value.results
    .filter((r) => r.studentId === user.value?.id)
    .sort((a, b) => b.submittedAt - a.submittedAt),
)
const pending = computed(() =>
  data.value.assignments.filter(
    (a) =>
      a.classId === user.value?.classId &&
      !results.value.some((r) => r.examId === a.examId && r.examType === a.examType),
  ),
)
</script>
<template>
  <section class="panel">
    <h2 class="section-title mb-3">📊 Góc Học Tập & Tiến Độ</h2>
    <div class="grid cols-2 mb-4">
      <div class="card text-center" style="border-left: 4px solid var(--primary)">
        <div class="stat-value">{{ results.length }}</div>
        <div class="text-light mt-1">Số đề đã làm</div>
      </div>
      <div class="card text-center" style="border-left: 4px solid var(--danger)">
        <div class="stat-value">{{ pending.length }}</div>
        <div class="text-light mt-1">Đề được giao chưa làm</div>
      </div>
    </div>
    <div class="card">
      <h3 class="font-heading mb-3 text-primary">Lịch sử làm bài chi tiết</h3>
      <ResultHistory :results="results" @review="openResult($event)" />
    </div>
  </section>
</template>
