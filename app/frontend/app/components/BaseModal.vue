<script setup lang="ts">
defineProps<{ title: string; wide?: boolean }>()
const emit = defineEmits<{ close: [] }>()
const dialog = ref<HTMLElement>()
let previous: HTMLElement | null = null
function keydown(e: KeyboardEvent) {
  if (e.key === 'Escape') emit('close')
  if (e.key !== 'Tab') return
  const items = Array.from(
    dialog.value?.querySelectorAll<HTMLElement>(
      'button:not(:disabled),input:not(:disabled),select:not(:disabled),textarea:not(:disabled),a[href],[tabindex="0"]',
    ) || [],
  ).filter((el) => el.getClientRects().length)
  const first = items[0],
    last = items.at(-1)
  if (e.shiftKey && document.activeElement === first) {
    e.preventDefault()
    last?.focus()
  } else if (!e.shiftKey && document.activeElement === last) {
    e.preventDefault()
    first?.focus()
  }
}
onMounted(() => {
  previous = document.activeElement as HTMLElement
  dialog.value?.focus()
})
onUnmounted(() => previous?.focus())
</script>
<template>
  <Teleport to="body">
    <div class="workspace-overlay active">
      <div
        ref="dialog"
        class="workspace-modal"
        :style="wide ? {} : { maxWidth: '900px', height: '90vh' }"
        role="dialog"
        aria-modal="true"
        :aria-label="title"
        tabindex="-1"
        @keydown="keydown"
      >
        <div class="workspace-header">
          <div class="workspace-title">{{ title }}</div>
          <div class="flex gap-2 items-center">
            <slot name="actions" />
            <button class="btn btn-secondary" @click="emit('close')">Đóng</button>
          </div>
        </div>
        <slot />
      </div>
    </div>
  </Teleport>
</template>
