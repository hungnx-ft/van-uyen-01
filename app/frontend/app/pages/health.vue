<script setup lang="ts">
type State = 'ok' | 'down' | 'off' | 'checking'
interface Check {
  name: string
  state: State
  detail: string
}

useHead({ title: 'Tình trạng hệ thống - VĂN UYỂN', meta: [{ name: 'robots', content: 'noindex' }] })

const config = useRuntimeConfig()
const apiBase = String(config.public.apiBase || '').replace(/\/$/, '')
const checks = ref<Check[]>([])
const checkedAt = ref<Date | null>(null)
const loading = ref(false)
const labels: Record<State, string> = {
  ok: 'Hoạt động',
  down: 'Gặp sự cố',
  off: 'Không dùng',
  checking: 'Đang kiểm tra',
}
const overall = computed<State>(() =>
  !checks.value.length
    ? 'checking'
    : checks.value.some((check) => check.state === 'down')
      ? 'down'
      : checks.value.some((check) => check.state === 'checking')
        ? 'checking'
        : 'ok',
)

async function run() {
  if (loading.value) return
  loading.value = true
  const frontend: Check = {
    name: 'Giao diện web',
    state: 'ok',
    detail: `Bản build ${config.app.buildId.slice(0, 8)}`,
  }
  if (!apiBase) {
    checks.value = [
      frontend,
      { name: 'Máy chủ API', state: 'off', detail: 'Chế độ lưu trữ trên trình duyệt' },
      { name: 'Cơ sở dữ liệu', state: 'off', detail: 'Chế độ lưu trữ trên trình duyệt' },
    ]
  } else {
    const started = performance.now()
    let api: Check, database: Check
    try {
      const response = await fetch(`${apiBase}/health`, { cache: 'no-store' })
      const ms = Math.round(performance.now() - started)
      const body = await response.json().catch(() => ({}))
      // 503 means the API answered but could not reach the database.
      api =
        response.ok || response.status === 503
          ? { name: 'Máy chủ API', state: 'ok', detail: `Phản hồi ${ms} ms` }
          : { name: 'Máy chủ API', state: 'down', detail: `HTTP ${response.status}` }
      database =
        body.database === 'ok'
          ? { name: 'Cơ sở dữ liệu', state: 'ok', detail: 'Kết nối bình thường' }
          : { name: 'Cơ sở dữ liệu', state: 'down', detail: 'Không kết nối được' }
    } catch {
      api = { name: 'Máy chủ API', state: 'down', detail: 'Không kết nối được' }
      database = { name: 'Cơ sở dữ liệu', state: 'down', detail: 'Không kiểm tra được' }
    }
    checks.value = [frontend, api, database]
  }
  checkedAt.value = new Date()
  loading.value = false
}

let timer: ReturnType<typeof setInterval> | undefined
onMounted(() => {
  run()
  timer = setInterval(run, 30_000)
})
onUnmounted(() => clearInterval(timer))
</script>
<template>
  <main class="health">
    <section class="card health-card">
      <h1 class="font-heading text-primary mb-3">🌸 Tình trạng hệ thống</h1>
      <p :class="['health-overall', `is-${overall}`]" role="status">
        {{
          overall === 'ok'
            ? 'Mọi thứ đang hoạt động bình thường'
            : overall === 'down'
              ? 'Hệ thống đang gặp sự cố'
              : 'Đang kiểm tra...'
        }}
      </p>
      <ul class="health-list">
        <li v-for="check in checks" :key="check.name">
          <span :class="['health-dot', `is-${check.state}`]" aria-hidden="true" />
          <strong>{{ check.name }}</strong>
          <span class="text-light">{{ check.detail }}</span>
          <span :class="['health-state', `is-${check.state}`]">{{ labels[check.state] }}</span>
        </li>
      </ul>
      <div class="health-footer">
        <span class="text-light">
          {{
            checkedAt
              ? `Cập nhật lúc ${checkedAt.toLocaleTimeString('vi-VN')} · tự làm mới mỗi 30 giây`
              : ''
          }}
        </span>
        <button class="btn btn-outline btn-sm" :disabled="loading" @click="run">
          Kiểm tra lại
        </button>
      </div>
    </section>
  </main>
</template>
<style scoped>
.health {
  padding: 40px 16px;
}
.health-card {
  max-width: 640px;
  margin: 0 auto;
}
.health-overall {
  padding: 12px 16px;
  border-radius: var(--radius-sm);
  font-weight: 600;
  margin-bottom: 16px;
  background: var(--secondary);
}
.health-overall.is-ok {
  background: color-mix(in srgb, var(--success) 35%, white);
}
.health-overall.is-down {
  background: color-mix(in srgb, var(--danger) 40%, white);
}
.health-list {
  list-style: none;
}
.health-list li {
  display: grid;
  grid-template-columns: auto 1fr auto;
  grid-template-areas: 'dot name state' 'dot detail state';
  column-gap: 12px;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid var(--border-color);
}
.health-list .health-dot {
  grid-area: dot;
}
.health-list strong {
  grid-area: name;
}
.health-list .text-light {
  grid-area: detail;
  font-size: 0.9rem;
}
.health-list .health-state {
  grid-area: state;
  font-size: 0.9rem;
  font-weight: 600;
}
.health-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--border-color);
}
.health-dot.is-ok {
  background: var(--success);
}
.health-dot.is-down {
  background: var(--danger);
}
.health-dot.is-checking {
  background: var(--warning);
}
.health-state.is-ok {
  color: #5f8f66;
}
.health-state.is-down {
  color: #c25b5b;
}
.health-footer {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
  font-size: 0.85rem;
}
</style>
