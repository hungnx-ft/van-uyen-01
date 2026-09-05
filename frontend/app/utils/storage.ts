import type { Database } from '../types'
export const tables = [
  'users',
  'classes',
  'theory_articles',
  'practice_exams',
  'mock_exams',
  'results',
  'assignments',
] as const
export const emptyDatabase = (): Database => ({
  users: [],
  classes: [],
  theory_articles: [],
  practice_exams: [],
  mock_exams: [],
  results: [],
  assignments: [],
})
export function readDatabase(storage: Storage): Database {
  const db = emptyDatabase()
  for (const table of tables) {
    const raw = storage.getItem(`vu_${table}`)
    if (!raw) continue
    const data: unknown = JSON.parse(raw)
    if (
      !Array.isArray(data) ||
      data.some((row) => !row || typeof row !== 'object' || typeof row.id !== 'string')
    )
      throw new Error(`Dữ liệu ${table} không hợp lệ. Dữ liệu gốc được giữ nguyên.`)
    Object.assign(db, { [table]: data })
  }
  return db
}
export function saveTable<K extends keyof Database>(storage: Storage, key: K, data: Database[K]) {
  storage.setItem(`vu_${key}`, JSON.stringify(data))
}
