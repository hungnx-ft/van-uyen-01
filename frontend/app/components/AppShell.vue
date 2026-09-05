<script setup lang="ts">
const open = ref(false),
  route = useRoute()
watch(
  () => route.path,
  () => (open.value = false),
)
</script>
<template>
  <MobileHeader @toggle="open = !open" />
  <div class="overlay" :class="{ active: open }" @click="open = false" />
  <div class="app-container">
    <AppSidebar :open="open" />
    <main class="main-content">
      <div
        class="main-header"
        style="
          display: flex;
          justify-content: flex-end;
          padding: 12px 32px;
          background: white;
          border-bottom: 1px solid var(--border-color);
          align-items: center;
          min-height: 60px;
          gap: 16px;
        "
      >
        <NotificationDropdown />
        <AccountMenu />
      </div>
      <slot />
    </main>
  </div>
</template>
