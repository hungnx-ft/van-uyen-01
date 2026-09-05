import { describe, expect, it } from 'vitest'
import { createLocalDatabase } from '../../app/repositories/localDatabase'
import {
  exportRawDatabase,
  initializeDatabase,
  readDatabase,
  saveTable,
  versionKey,
} from '../../app/utils/storage'
import { restoreSession, saveSession, sessionKey } from '../../app/utils/session'
import type { Database, Result, User } from '../../app/types'

import { memoryStorage } from './memoryStorage'

const teacher: User = {
  id: 'teacher',
  password: 'changed-password',
  role: 'teacher',
  fullName: 'Giáo viên',
}
const seeds: Pick<Database, 'users' | 'theory_articles'> = { users: [teacher], theory_articles: [] }
function result(id: string, submittedAt: number): Result {
  return {
    id,
    studentId: 'student',
    studentName: 'Học sinh',
    examId: 'exam',
    examTitle: 'Đề',
    examType: 'practice',
    maxScore: 4,
    status: 'pending',
    answers: { q0: { ans: 'Bài làm', selfScore: 0, teacherScore: 0 } },
    submittedAt,
    timeSpent: 30,
  }
}

describe('runtime validation and legacy compatibility', () => {
  it('normalizes optional legacy fields without rewriting the original or changing IDs', () => {
    const storage = memoryStorage()
    const original = JSON.stringify([
      { id: 'student', role: 'student', password: 'test', classId: 'class-1' },
    ])
    storage.setItem('vu_users', original)
    storage.setItem('vu_classes', JSON.stringify([{ id: 'class-1', name: '9A' }]))
    const db = readDatabase(storage)
    expect(db.users[0]!.fullName).toBe('student')
    expect(db.users[0]!.classId).toBe(db.classes[0]!.id)
    expect(db.classes[0]!.year).toBe('')
    expect(storage.getItem('vu_users')).toBe(original)
  })
  it.each([
    ['users', [{ ...teacher, role: 'admin' }]],
    ['users', [teacher, teacher]],
    ['classes', [{ id: 'c', name: 123 }]],
    ['practice_exams', [{ id: 'e', title: 'Đề', targetGroup: 'doc-hieu', questions: 'broken' }]],
    [
      'mock_exams',
      [
        {
          id: 'e',
          title: 'Đề',
          targetGroup: 'vao-10',
          questions: [{ q: 'Câu', a: 'Đáp án', score: -1 }],
        },
      ],
    ],
    [
      'theory_articles',
      [{ id: 't', title: 'Bài', mainCat: 'doc-hieu', subCat: 'tho', format: 'javascript' }],
    ],
    ['results', [{ ...result('r', 1), answers: [] }]],
    [
      'assignments',
      [{ id: 'a', examType: 'other', examId: 'e', classId: 'c', createdAt: 1, examTitle: 'Đề' }],
    ],
  ])('rejects malformed %s with a useful error and leaves storage intact', (table, rows) => {
    const storage = memoryStorage(),
      raw = JSON.stringify(rows)
    storage.setItem(`vu_${table}`, raw)
    expect(() => readDatabase(storage)).toThrow(new RegExp(String(table)))
    expect(storage.getItem(`vu_${table}`)).toBe(raw)
  })
  it('derives missing attempt numbers chronologically, without conflating student or exam type', () => {
    const storage = memoryStorage()
    storage.setItem(
      'vu_results',
      JSON.stringify([
        result('second', 20),
        result('first', 10),
        { ...result('other', 15), examType: 'mock' },
      ]),
    )
    expect(readDatabase(storage).results.map((r) => r.attempt)).toEqual([2, 1, 1])
    expect(JSON.parse(storage.getItem('vu_results')!)[0].attempt).toBeUndefined()
  })
  it('rejects non-finite score writes instead of serializing NaN as null', () => {
    const storage = memoryStorage()
    const invalid = result('r', 1)
    invalid.answers.q0!.teacherScore = NaN
    expect(() => saveTable(storage, 'results', [invalid])).toThrow(/teacherScore/)
    expect(storage.length).toBe(0)
  })
  it('detaches nested result data from mutable forms', () => {
    const storage = memoryStorage(),
      form = result('r', 1)
    const saved = saveTable(storage, 'results', [form])
    form.answers.q0!.ans = 'Unsaved edit'
    expect(saved[0]!.answers.q0!.ans).toBe('Bài làm')
    expect(readDatabase(storage).results[0]!.answers.q0!.ans).toBe('Bài làm')
  })
  it('preserves unsupported future versions', () => {
    const storage = memoryStorage()
    storage.setItem(versionKey, '99')
    expect(() => initializeDatabase(storage, seeds)).toThrow(/Phiên bản/)
    expect(storage.getItem(versionKey)).toBe('99')
    expect(storage.getItem('vu_users')).toBeNull()
  })
  it('can export original malformed strings for recovery', () => {
    const storage = memoryStorage()
    storage.setItem('vu_results', '{broken')
    expect(JSON.parse(exportRawDatabase(storage)).entries.vu_results).toBe('{broken')
  })
})

describe('one-time initialization', () => {
  it('seeds unique IDs once and preserves changed passwords on subsequent startup', () => {
    const storage = memoryStorage(),
      repository = createLocalDatabase(storage)
    const first = repository.initialize()
    expect(new Set(first.theory_articles.map((article) => article.id)).size).toBe(
      first.theory_articles.length,
    )
    repository.save('users', [{ ...first.users[0]!, password: 'new-password' }])
    const second = repository.initialize()
    expect(second.users[0]!.password).toBe('new-password')
    expect(second.theory_articles.map((article) => article.id)).toEqual(
      first.theory_articles.map((article) => article.id),
    )
    expect(storage.getItem(versionKey)).toBe('1')
  })
  it('respects explicitly empty tables and never recreates a deleted teacher', () => {
    const storage = memoryStorage()
    storage.setItem('vu_users', '[]')
    storage.setItem('vu_theory_articles', '[]')
    const db = initializeDatabase(storage, seeds)
    expect(db.users).toEqual([])
    expect(db.theory_articles).toEqual([])
  })
  it('validates all existing tables before writing any seeds', () => {
    const storage = memoryStorage()
    storage.setItem('vu_results', 'bad JSON')
    expect(() => initializeDatabase(storage, seeds)).toThrow(/results/)
    expect(storage.getItem('vu_users')).toBeNull()
    expect(storage.getItem(versionKey)).toBeNull()
  })
  it('rolls back partial startup on quota errors and can retry successfully', () => {
    const storage = memoryStorage(),
      original = storage.setItem
    storage.setItem = (key, value) => {
      if (key === 'vu_theory_articles') throw new DOMException('Quota', 'QuotaExceededError')
      original(key, value)
    }
    expect(() => initializeDatabase(storage, seeds)).toThrow(/khởi tạo/)
    expect(storage.length).toBe(0)
    storage.setItem = original
    expect(initializeDatabase(storage, seeds).users).toEqual([teacher])
  })
})

describe('session restoration', () => {
  it('reduces legacy sessions to ID and takes account details from database', () => {
    const storage = memoryStorage()
    storage.setItem(
      sessionKey,
      JSON.stringify({ ...teacher, password: 'old-password', role: 'student' }),
    )
    expect(restoreSession(storage, [teacher])).toBe(teacher.id)
    expect(storage.getItem(sessionKey)).toBe(JSON.stringify({ id: teacher.id }))
  })
  it.each(['{broken', 'null', '[]', '{"id":"deleted-user"}', '{"id":123}'])(
    'clears invalid or deleted-user session %s',
    (raw) => {
      const storage = memoryStorage()
      storage.setItem(sessionKey, raw)
      expect(restoreSession(storage, [teacher])).toBeNull()
      expect(storage.getItem(sessionKey)).toBeNull()
    },
  )
  it('reports blocked session writes', () => {
    const storage = memoryStorage()
    storage.setItem = () => {
      throw new DOMException('Blocked', 'SecurityError')
    }
    expect(() => saveSession(storage, teacher.id)).toThrow(/phiên đăng nhập/)
  })
})
