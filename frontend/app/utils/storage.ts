import type { Database } from '../types'
import { normalizeTable } from './validation'

export const schemaVersion = 1
export const versionKey = 'vu_schema_version'
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
  const version = storage.getItem(versionKey)
  if (version !== null && version !== String(schemaVersion)) {
    throw new Error('Phiên bản dữ liệu chưa được hỗ trợ. Dữ liệu gốc được giữ nguyên.')
  }
  const db = emptyDatabase()
  for (const table of tables) {
    const raw = storage.getItem(`vu_${table}`)
    if (raw === null) continue
    let value: unknown
    try {
      value = JSON.parse(raw)
    } catch {
      throw new Error(`Dữ liệu ${table} không phải JSON hợp lệ. Dữ liệu gốc được giữ nguyên.`)
    }
    Object.assign(db, { [table]: normalizeTable(table, value) })
  }
  // The HTML app omitted attempt numbers. Derive them deterministically without rewriting storage.
  const attempts = new Map<string, number>()
  for (const result of [...db.results].sort((a, b) => a.submittedAt - b.submittedAt)) {
    const key = JSON.stringify([result.studentId, result.examType, result.examId])
    const attempt = result.attempt ?? (attempts.get(key) ?? 0) + 1
    result.attempt = attempt
    attempts.set(key, Math.max(attempts.get(key) ?? 0, attempt))
  }
  return db
}

export function saveTable<K extends keyof Database>(
  storage: Storage,
  key: K,
  data: Database[K],
): Database[K] {
  const normalized = normalizeTable(key, data)
  try {
    storage.setItem(`vu_${key}`, JSON.stringify(normalized))
  } catch {
    throw new Error('Không thể lưu dữ liệu. Bộ nhớ trình duyệt có thể đã đầy hoặc bị chặn.')
  }
  return normalized
}

/** Seed only absent tables. Validate everything before writing; rollback an incomplete startup. */
export function initializeDatabase(
  storage: Storage,
  seeds: Pick<Database, 'users' | 'theory_articles'>,
): Database {
  const db = readDatabase(storage)
  const writes: [string, string][] = []
  for (const table of ['users', 'theory_articles'] as const) {
    if (storage.getItem(`vu_${table}`) !== null) continue
    const rows = normalizeTable(table, seeds[table])
    Object.assign(db, { [table]: rows })
    writes.push([`vu_${table}`, JSON.stringify(rows)])
  }
  if (storage.getItem(versionKey) === null) writes.push([versionKey, String(schemaVersion)])
  const written: string[] = []
  try {
    for (const [key, value] of writes) {
      storage.setItem(key, value)
      written.push(key)
    }
  } catch {
    let restored = true
    for (const key of written.reverse()) {
      try {
        storage.removeItem(key)
      } catch {
        restored = false
      }
    }
    throw new Error(
      restored
        ? 'Không thể khởi tạo dữ liệu. Bộ nhớ trình duyệt có thể đã đầy hoặc bị chặn. Hãy thử lại.'
        : 'Khởi tạo dữ liệu bị gián đoạn. Hãy tải bản sao dữ liệu trước khi thử lại.',
    )
  }
  return db
}

/** Export the original strings, including malformed JSON, so diagnostics never destroy evidence. */
export function exportRawDatabase(storage: Storage): string {
  return JSON.stringify(
    {
      exportedAt: new Date().toISOString(),
      entries: Object.fromEntries(
        [...tables.map((table) => `vu_${table}`), versionKey].map((key) => [
          key,
          storage.getItem(key),
        ]),
      ),
    },
    null,
    2,
  )
}
