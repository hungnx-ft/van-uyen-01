<script setup lang="ts">
const { data, getRemoteAIUsage } = useDatabase()
const { isTeacher } = useAuth()
const period = ref('all')
const classFilter = ref('all')
const typeFilter = ref('all')
const aiUsage = ref({
  total_jobs: 0,
  completed_jobs: 0,
  failed_jobs: 0,
  total_tokens: 0,
  estimated_cost_usd: 0,
  low_confidence_jobs: 0,
  average_score_deviation: null as number | null,
})
const filtered = computed(() => {
  const cutoff =
    period.value === '30'
      ? Date.now() - 30 * 86400000
      : period.value === '7'
        ? Date.now() - 7 * 86400000
        : 0
  return data.value.results.filter(
    (result) =>
      result.submittedAt >= cutoff &&
      (classFilter.value === 'all' || result.classId === classFilter.value) &&
      (typeFilter.value === 'all' || result.examType === typeFilter.value),
  )
})
const graded = computed(() => filtered.value.filter((result) => result.status === 'graded'))
const average = computed(() =>
  graded.value.length
    ? graded.value.reduce((sum, result) => sum + (result.teacherScore || 0), 0) /
      graded.value.length
    : 0,
)
const classChart = computed(() =>
  data.value.classes
    .map((item) => ({
      ...item,
      count: filtered.value.filter((result) => result.classId === item.id).length,
    }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 8),
)
const examChart = computed(() => {
  const counts = new Map<string, number>()
  filtered.value.forEach((result) =>
    counts.set(result.examTitle, (counts.get(result.examTitle) || 0) + 1),
  )
  return [...counts].sort((a, b) => b[1] - a[1]).slice(0, 8)
})
onMounted(async () => {
  if (isTeacher.value) aiUsage.value = await getRemoteAIUsage().catch(() => aiUsage.value)
})
</script>
<template>
  <section v-if="isTeacher" class="panel">
    <h2 class="section-title mb-3">📈 Góc Phân Tích</h2>
    <div class="flex gap-2 mb-3" style="flex-wrap: wrap">
      <select v-model="period" class="input-control" aria-label="Khoảng thời gian">
        <option value="all">Toàn bộ thời gian</option>
        <option value="7">7 ngày gần nhất</option>
        <option value="30">30 ngày gần nhất</option>
      </select>
      <select v-model="classFilter" class="input-control" aria-label="Lọc lớp">
        <option value="all">Tất cả lớp</option>
        <option v-for="item in data.classes" :key="item.id" :value="item.id">
          {{ item.name }} ({{ item.year }})
        </option>
      </select>
      <select v-model="typeFilter" class="input-control" aria-label="Lọc loại đề">
        <option value="all">Tất cả loại đề</option>
        <option value="practice">Luyện tập</option>
        <option value="mock">Thi thử</option>
      </select>
    </div>
    <div class="grid cols-4 mb-4">
      <div class="card text-center">
        <div class="stat-value">{{ data.users.filter((u) => u.role === 'student').length }}</div>
        <div class="text-light">Học sinh</div>
      </div>
      <div class="card text-center">
        <div class="stat-value">{{ data.classes.length }}</div>
        <div class="text-light">Lớp</div>
      </div>
      <div class="card text-center">
        <div class="stat-value">{{ filtered.length }}</div>
        <div class="text-light">Bài nộp</div>
      </div>
      <div class="card text-center">
        <div class="stat-value">{{ average.toFixed(2) }}</div>
        <div class="text-light">Điểm TB</div>
      </div>
    </div>
    <div class="grid cols-2">
      <div class="card">
        <h3 class="font-heading text-primary mb-3">Bài nộp theo lớp</h3>
        <p v-if="!classChart.length" class="empty-state">Chưa có dữ liệu.</p>
        <div v-for="item in classChart" :key="item.id" class="mb-2">
          <div class="flex justify-between">
            <span>{{ item.name }}</span>
            <b>{{ item.count }}</b>
          </div>
          <div style="height: 8px; background: var(--border-color); border-radius: 4px">
            <div
              :style="{
                width: `${Math.min(100, (item.count / Math.max(classChart[0]?.count || 1, 1)) * 100)}%`,
                height: '100%',
                background: 'var(--primary)',
                borderRadius: '4px',
              }"
            />
          </div>
        </div>
      </div>
      <div class="card">
        <h3 class="font-heading text-primary mb-3">Đề được làm nhiều</h3>
        <p v-if="!examChart.length" class="empty-state">Chưa có dữ liệu.</p>
        <div v-for="[title, count] in examChart" :key="title" class="flex justify-between mb-2">
          <span>{{ title }}</span>
          <b>{{ count }} bài</b>
        </div>
      </div>
    </div>
    <div class="card mt-4">
      <h3 class="font-heading text-primary mb-3">🤖 AI usage & chất lượng</h3>
      <div class="grid cols-4">
        <div>
          <b>{{ aiUsage.total_jobs }}</b>
          <div class="text-light">Tổng job</div>
        </div>
        <div>
          <b>{{ aiUsage.total_tokens.toLocaleString() }}</b>
          <div class="text-light">Token</div>
        </div>
        <div>
          <b>${{ aiUsage.estimated_cost_usd.toFixed(4) }}</b>
          <div class="text-light">Chi phí ước tính</div>
        </div>
        <div>
          <b>{{ aiUsage.low_confidence_jobs }}</b>
          <div class="text-light">Confidence thấp</div>
        </div>
      </div>
      <p class="text-light mt-3">
        Độ lệch điểm AI–giáo viên:
        {{
          aiUsage.average_score_deviation == null
            ? 'Chưa có dữ liệu'
            : aiUsage.average_score_deviation.toFixed(2)
        }}
        điểm
      </p>
    </div>
  </section>
</template>
