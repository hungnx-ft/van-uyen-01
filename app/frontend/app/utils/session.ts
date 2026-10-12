import type { User } from '../types'
export const sessionKey = 'vu_current_user'

export function saveSession(storage: Storage, id: string | null) {
  try {
    if (id === null) storage.removeItem(sessionKey)
    else storage.setItem(sessionKey, JSON.stringify({ id }))
  } catch {
    throw new Error('Không thể lưu phiên đăng nhập. Hãy cho phép trình duyệt sử dụng bộ nhớ phiên.')
  }
}

export function restoreSession(storage: Storage, users: User[]): string | null {
  const raw = storage.getItem(sessionKey)
  if (raw === null) return null
  let saved: unknown
  try {
    saved = JSON.parse(raw)
  } catch {
    saveSession(storage, null)
    return null
  }
  const id = saved && typeof saved === 'object' && 'id' in saved ? saved.id : null
  if (typeof id !== 'string' || !users.some((user) => user.id === id)) {
    saveSession(storage, null)
    return null
  }
  // Old HTML sessions included passwords and roles. Keep only a reference to the stored user.
  if (raw !== JSON.stringify({ id })) saveSession(storage, id)
  return id
}
