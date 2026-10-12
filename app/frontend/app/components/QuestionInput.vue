<script setup lang="ts">
defineProps<{ label: string; essay?: boolean }>()
const answer = defineModel<string>({ required: true })
</script>
<template>
  <div class="question-block">
    <label class="question-title" style="display: block">
      {{ label }}
      <textarea
        v-model="answer"
        class="question-textarea student-ans mt-2"
        :style="essay ? { minHeight: '400px' } : {}"
        placeholder="Nhập câu trả lời của cậu vào đây..."
      />
    </label>
  </div>
</template>
