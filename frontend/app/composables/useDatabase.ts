import type { Database } from '~/types'
import { emptyDatabase, readDatabase, saveTable } from '~/utils/storage'
import { initialTheory } from '~/data/theory'
export function useDatabase() {
  const data = useState<Database>('database', emptyDatabase)
  const ready = useState('database-ready', () => false)
  const error = useState('database-error', () => '')
  function initialize() {
    if (ready.value) return
    try {
      data.value = readDatabase(localStorage)
      if (!data.value.users.some((u) => u.role === 'teacher')) {
        data.value.users.push({
          id: 'hathanhhangc2yenphong@bacninh.edu.vn',
          password: 'Thanhhang97@',
          role: 'teacher',
          fullName: 'Hà Thanh Hằng',
          schoolName: 'THCS Yên Phong',
        })
        saveTable(localStorage, 'users', data.value.users)
      }
      if (!localStorage.getItem('vu_theory_articles')) {
        data.value.theory_articles = initialTheory.map((t) => ({ ...t, id: crypto.randomUUID() }))
        saveTable(localStorage, 'theory_articles', data.value.theory_articles)
      }
      ready.value = true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Không thể đọc dữ liệu trình duyệt.'
    }
  }
  function set<K extends keyof Database>(table: K, rows: Database[K]) {
    if (!ready.value) throw new Error('Kho dữ liệu chưa sẵn sàng.')
    try {
      saveTable(localStorage, table, rows)
      Object.assign(data.value, { [table]: rows })
    } catch {
      throw new Error('Không thể lưu dữ liệu. Bộ nhớ trình duyệt có thể đã đầy hoặc bị chặn.')
    }
  }
  function upsert<K extends keyof Database>(table: K, row: Database[K][number]) {
    const rows = [...data.value[table]] as Database[K][number][]
    const index = rows.findIndex((item) => item.id === row.id)
    if (index < 0) rows.push(row)
    else rows[index] = row
    set(table, rows as Database[K])
  }
  function remove<K extends keyof Database>(table: K, id: string) {
    set(table, data.value[table].filter((row) => row.id !== id) as Database[K])
  }
  return { data, ready, error, initialize, set, upsert, remove }
}
