<script setup lang="ts">
const { ready, error, initialize } = useDatabase(),
  { restore, user, isTeacher } = useAuth()
const route = useRoute(),
  { state, close } = useWorkspace()
const mounted = ref(false)
onMounted(() => {
  initialize()
  if (ready.value) restore()
  mounted.value = true
})
watchEffect(() => {
  if (!mounted.value || !ready.value) return
  const authPage = ['/login', '/register'].includes(route.path)
  if (!user.value && !authPage) navigateTo('/login')
  else if (user.value && authPage) navigateTo('/')
  else if (route.path === '/manage' && !isTeacher.value) navigateTo('/')
})
</script>
<template>
  <div v-if="error" class="card" style="margin: 40px" role="alert">{{ error }}</div>
  <template v-else-if="mounted && ready">
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
