<script setup lang="ts">
defineProps<{ items: { id: string; label: string }[] }>()
const model = defineModel<string>({ required: true })
</script>
<template>
  <div class="tabs">
    <button
      v-for="item in items"
      :key="item.id"
      class="tab-btn"
      :class="{ active: model === item.id }"
      :aria-pressed="model === item.id"
      @click="model = item.id"
    >
      {{ item.label }}
    </button>
  </div>
</template>
