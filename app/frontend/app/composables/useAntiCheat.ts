export function useAntiCheat(active: Ref<boolean>) {
  const { show } = useToast()
  const tabSwitches = ref(0)
  const context = (e: Event) => {
    if (active.value) {
      e.preventDefault()
      show('🌸 Hãy tự lực làm bài nhé!')
    }
  }
  const keys = (e: KeyboardEvent) => {
    if (
      active.value &&
      (((e.ctrlKey || e.metaKey) && ['c', 'v', 'x', 'u', 'a'].includes(e.key.toLowerCase())) ||
        e.key === 'F12' ||
        (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === 'i'))
    ) {
      e.preventDefault()
      show('🌸 Sao chép bị khóa rồi nha!')
    }
  }
  const visibility = () => {
    if (active.value && document.visibilityState === 'hidden') tabSwitches.value += 1
  }
  onMounted(() => {
    document.addEventListener('contextmenu', context)
    document.addEventListener('keydown', keys)
    document.addEventListener('visibilitychange', visibility)
  })
  onUnmounted(() => {
    document.removeEventListener('contextmenu', context)
    document.removeEventListener('keydown', keys)
    document.removeEventListener('visibilitychange', visibility)
  })
  return { tabSwitches }
}
