<script setup lang="ts">
const petals = ref<{ id: number; left: string; duration: string; icon: string }[]>([])
let interval: ReturnType<typeof setInterval> | undefined,
  id = 0
const pending = new Set<ReturnType<typeof setTimeout>>()
onMounted(() => {
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return
  interval = setInterval(() => {
    const petal = {
      id: id++,
      left: Math.random() * 100 + 'vw',
      duration: Math.random() * 5 + 7 + 's',
      icon: Math.random() > 0.5 ? '🌸' : '🍃',
    }
    petals.value.push(petal)
    const handle = setTimeout(() => {
      petals.value = petals.value.filter((p) => p.id !== petal.id)
      pending.delete(handle)
    }, 12000)
    pending.add(handle)
  }, 1500)
})
onUnmounted(() => {
  clearInterval(interval)
  pending.forEach(clearTimeout)
})
</script>
<template>
  <div id="falling-container" aria-hidden="true">
    <div
      v-for="petal in petals"
      :key="petal.id"
      class="falling-petal"
      :style="{ left: petal.left, animationDuration: petal.duration }"
    >
      {{ petal.icon }}
    </div>
  </div>
</template>
