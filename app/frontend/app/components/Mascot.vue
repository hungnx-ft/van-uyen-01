<script setup lang="ts">
const face = ref('🌱'),
  message = ref(''),
  messages = [
    'Văn học là nhân học! 🌿',
    'Cậu đang làm rất tốt! 🌸',
    'Cố gắng lên nhé! 🐝',
    'Chữ nghĩa nở hoa 🌷',
    'Hãy tự tin lên! 🌱',
  ]
let timer: ReturnType<typeof setTimeout> | undefined
function poke() {
  face.value = ['🌱', '🌸', '🐝'][Math.floor(Math.random() * 3)]!
  message.value = messages[Math.floor(Math.random() * messages.length)]!
  clearTimeout(timer)
  timer = setTimeout(() => (message.value = ''), 3000)
}
onUnmounted(() => clearTimeout(timer))
</script>
<template>
  <div
    class="mascot"
    role="button"
    tabindex="0"
    aria-label="Lời động viên"
    @click="poke"
    @keydown.enter="poke"
  >
    <div class="mascot-img">{{ face }}</div>
    <div v-if="message" class="mascot-bubble" style="display: block">{{ message }}</div>
  </div>
</template>
