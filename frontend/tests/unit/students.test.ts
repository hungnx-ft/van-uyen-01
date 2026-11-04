import { describe, expect, it } from 'vitest'
import {
  DEFAULT_STUDENT_PASSWORD,
  newPasswordError,
  studentUsername,
  studentUsernameBase,
} from '../../app/utils/students'

describe('student usernames follow hs_hovaten_id like the backend', () => {
  it.each([
    ['Nguyễn Văn An', 'nguyenvanan'],
    ['Đặng Thị Đào', 'dangthidao'],
    ['  TRẦN   Ngọc-Ánh  ', 'tranngocanh'],
    ['Lê Văn Bảy 2', 'levanbay2'],
    ['李小龙', 'hocsinh'],
    ['😀', 'hocsinh'],
    ['A'.repeat(80), 'a'.repeat(40)],
  ])('%s -> %s', (name, base) => {
    expect(studentUsernameBase(name)).toBe(base)
  })
  it('appends the id', () => {
    expect(studentUsername('Nguyễn Văn An', 57)).toBe('hs_nguyenvanan_57')
  })
})

describe('new password rules', () => {
  it('uses the agreed default', () => {
    expect(DEFAULT_STUDENT_PASSWORD).toBe('123456')
  })
  it('rejects short, default, unchanged and mismatched passwords', () => {
    expect(newPasswordError('123456', 'short', 'short')).toMatch(/ít nhất 8/)
    expect(newPasswordError('old-password', '123456', '123456')).toMatch(/ít nhất 8/)
    expect(newPasswordError('same-password', 'same-password', 'same-password')).toMatch(/khác/)
    expect(newPasswordError('123456', 'new-password', 'other-password')).toMatch(/không khớp/)
  })
  it('accepts a valid new password', () => {
    expect(newPasswordError('123456', 'new-password', 'new-password')).toBe('')
  })
})
