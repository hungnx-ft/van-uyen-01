import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { computed, ref } from 'vue'
import { useDatabase } from '../../app/composables/useDatabase'
import { useAuth } from '../../app/composables/useAuth'
import { memoryStorage } from './memoryStorage'

describe('database and authentication state', () => {
  beforeEach(() => {
    const states = new Map<string, ReturnType<typeof ref>>()
    vi.stubGlobal('useState', (key: string, init: () => unknown) => {
      if (!states.has(key)) states.set(key, ref(init()))
      return states.get(key)
    })
    vi.stubGlobal('computed', computed)
    vi.stubGlobal('localStorage', memoryStorage())
    vi.stubGlobal('sessionStorage', memoryStorage())
    vi.stubGlobal('useDatabase', useDatabase)
    vi.stubGlobal('useToast', () => ({ show: vi.fn() }))
    vi.stubGlobal('navigateTo', vi.fn())
  })
  afterEach(() => vi.unstubAllGlobals())
  it('does not publish unsaved state on storage failure', () => {
    const db = useDatabase()
    db.initialize()
    const before = JSON.stringify(db.data.value.classes)
    localStorage.setItem = () => {
      throw new DOMException('Quota', 'QuotaExceededError')
    }
    expect(() => db.upsert('classes', { id: 'c', name: '9A', year: '2026' })).toThrow(
      /Không thể lưu/,
    )
    expect(JSON.stringify(db.data.value.classes)).toBe(before)
    expect(db.ready.value).toBe(true)
  })
  it('clears startup errors after retry and restores auth only after data is ready', () => {
    localStorage.setItem('vu_results', 'invalid')
    const db = useDatabase(),
      auth = useAuth()
    db.initialize()
    auth.restore()
    expect(db.ready.value).toBe(false)
    expect(auth.authReady.value).toBe(false)
    expect(db.data.value.users).toHaveLength(0)
    localStorage.removeItem('vu_results')
    db.initialize()
    auth.restore()
    expect(db.ready.value).toBe(true)
    expect(db.error.value).toBe('')
    expect(auth.authReady.value).toBe(true)
  })
  it('derives the signed-in user from shared data after class, role and password updates', () => {
    const db = useDatabase()
    db.initialize()
    const auth = useAuth()
    auth.restore()
    auth.register('student', 'password', 'Học sinh')
    db.upsert('users', {
      ...auth.user.value!,
      classId: 'new-class',
      className: '9B',
      password: 'reset',
    })
    expect(auth.user.value!.className).toBe('9B')
    expect(() => auth.changePassword('password', 'new')).toThrow(/cũ/)
    auth.changePassword('reset', 'new')
    expect(auth.user.value!.password).toBe('new')
    db.upsert('users', { ...auth.user.value!, role: 'teacher' })
    expect(auth.isTeacher.value).toBe(true)
    db.remove('users', 'student')
    expect(auth.user.value).toBeNull()
    expect(auth.isTeacher.value).toBe(false)
  })
  it('does not log in when session storage fails', () => {
    const db = useDatabase()
    db.initialize()
    const auth = useAuth(),
      teacher = db.data.value.users[0]!
    sessionStorage.setItem = () => {
      throw new Error('blocked')
    }
    expect(() => auth.login(teacher.id, teacher.password)).toThrow(/phiên/)
    expect(auth.user.value).toBeNull()
  })
})
