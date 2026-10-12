<script setup lang="ts">
import { tables, versionKey } from '~/utils/storage'
const { ready, error, initialize, refresh } = useDatabase(),
  { restore, user, isTeacher, authReady } = useAuth()
const route = useRoute(),
  { state, close } = useWorkspace()
const mounted = ref(false)
// The status page must load without storage or a session, so it skips the app shell.
const statusPage = computed(() => route.path.replace(/\/$/, '') === '/health')
function retry() {
  initialize()
  if (ready.value) restore()
}
function syncStorage(event: StorageEvent) {
  if (event.storageArea !== localStorage) return
  if (
    event.key !== null &&
    event.key !== versionKey &&
    !tables.some((table) => event.key === `vu_${table}`)
  )
    return
  refresh()
  if (ready.value) restore()
}
onMounted(() => {
  retry()
  mounted.value = true
  window.addEventListener('storage', syncStorage)
})
onUnmounted(() => window.removeEventListener('storage', syncStorage))
watch([() => user.value?.id, () => user.value?.role], () => close())
watchEffect(() => {
  if (statusPage.value || !mounted.value || !ready.value || !authReady.value) return
  const authPage = ['/login', '/register'].includes(route.path)
  if (!user.value && !authPage) navigateTo('/login')
  else if (user.value && authPage) navigateTo('/')
  else if (['/manage', '/analytics'].includes(route.path) && !isTeacher.value) navigateTo('/')
})
</script>
<template>
  <NuxtPage v-if="statusPage" />
  <StorageError v-else-if="error" :message="error" @retry="retry" />
  <template v-else-if="mounted && ready && authReady">
    <AppShell v-if="user"><NuxtPage /></AppShell>
    <NuxtPage v-else />
    <ExamWorkspace
      v-if="state"
      :key="state.result?.id || state.exam.id"
      :session="state"
      @close="close"
    />
    <Mascot />
    <FlowerEffects />
  </template>
  <div v-else class="empty-state">🌸 Đang mở khu vườn văn chương...</div>
  <AppToast />
</template>
