<script setup lang="ts">
const { messages } = useToast()
</script>
<template>
  <div class="toast-container" role="status" aria-live="polite">
    <div v-for="message in messages" :key="message.id" class="toast show">{{ message.text }}</div>
  </div>
</template>
