import type { Database } from '../types'
import { initialTheory } from '../data/theory'
import { initializeDatabase, readDatabase, saveTable } from '../utils/storage'

export interface DatabaseRepository {
  initialize(): Database
  read(): Database
  save<K extends keyof Database>(table: K, rows: Database[K]): Database[K]
}

export function createLocalDatabase(storage: Storage): DatabaseRepository {
  return {
    initialize: () =>
      initializeDatabase(storage, {
        users: [
          {
            id: 'hathanhhangc2yenphong@bacninh.edu.vn',
            password: 'Thanhhang97@',
            role: 'teacher',
            fullName: 'Hà Thanh Hằng',
            schoolName: 'THCS Yên Phong',
          },
        ],
        theory_articles: initialTheory.map((article) => ({ ...article, id: crypto.randomUUID() })),
      }),
    read: () => readDatabase(storage),
    save: (table, rows) => saveTable(storage, table, rows),
  }
}
