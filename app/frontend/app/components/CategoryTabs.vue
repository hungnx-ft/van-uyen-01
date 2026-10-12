<script setup lang="ts">
defineProps<{ items: { id: string; label: string; count?: number }[] }>()
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
      {{ item.label }} <span v-if="item.count !== undefined" class="tab-count">({{ item.count }})</span>
    </button>
  </div>
</template>
