import { clockText } from '~/utils/exams'
export function useExamTimer(limit: number, onExpired: () => void) {
  const seconds = ref(limit),
    elapsed = ref(0)
  let started = 0,
    interval: ReturnType<typeof setInterval> | undefined,
    warned = false
  function update() {
    elapsed.value = Math.floor((Date.now() - started) / 1000)
    seconds.value = limit - elapsed.value
    if (seconds.value <= 0 && !warned) {
      warned = true
      onExpired()
    }
  }
  function start() {
    stop()
    started = Date.now()
    interval = setInterval(update, 250)
  }
  function stop() {
    if (interval) clearInterval(interval)
    interval = undefined
  }
  onUnmounted(stop)
  return { seconds, elapsed, label: computed(() => clockText(seconds.value)), start, stop }
}
