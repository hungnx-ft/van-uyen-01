<script setup lang="ts">
defineEmits<{ toggle: [] }>()
</script>
<template>
  <header class="mobile-header">
    <div class="sidebar-logo">🌸 VĂN UYỂN</div>
    <button class="hamburger" aria-label="Mở menu" @click="$emit('toggle')">
      <i class="fa-solid fa-bars" />
    </button>
  </header>
</template>
