export function memoryStorage(): Storage {
  const records = new Map<string, string>()
  return {
    get length() {
      return records.size
    },
    getItem: (key) => records.get(key) ?? null,
    setItem: (key, value) => {
      records.set(key, value)
    },
    removeItem: (key) => {
      records.delete(key)
    },
    clear: () => records.clear(),
    key: (i) => [...records.keys()][i] ?? null,
  }
}
