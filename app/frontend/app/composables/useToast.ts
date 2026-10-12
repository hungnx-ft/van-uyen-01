export function useToast() {
  const messages = useState<{ id: number; text: string }[]>('toasts', () => [])
  function show(text: string) {
    const id = Date.now() + Math.random()
    messages.value.push({ id, text })
    setTimeout(() => {
      messages.value = messages.value.filter((m) => m.id !== id)
    }, 4000)
  }
  return { messages, show }
}
