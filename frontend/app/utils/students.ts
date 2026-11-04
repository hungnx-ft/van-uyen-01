/** Teacher-created and teacher-reset accounts start with this password (see backend). */
export const DEFAULT_STUDENT_PASSWORD = '123456'
export const MIN_PASSWORD_LENGTH = 8

/** The ASCII "hovaten" part of hs_<hovaten>_<id>, matching the backend rule. */
export function studentUsernameBase(fullName: string) {
  const ascii = fullName
    .replace(/đ/g, 'd')
    .replace(/Đ/g, 'D')
    .normalize('NFKD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]/g, '')
    .slice(0, 40)
  return ascii || 'hocsinh'
}

export function studentUsername(fullName: string, id: string | number) {
  return `hs_${studentUsernameBase(fullName)}_${id}`
}

/** Returns a Vietnamese message, or '' when the new password is acceptable. */
export function newPasswordError(current: string, next: string, confirm: string) {
  if (next.length < MIN_PASSWORD_LENGTH)
    return `Mật khẩu mới cần ít nhất ${MIN_PASSWORD_LENGTH} ký tự.`
  if (next === DEFAULT_STUDENT_PASSWORD || next === current)
    return 'Mật khẩu mới phải khác mật khẩu hiện tại.'
  if (next !== confirm) return 'Mật khẩu nhập lại không khớp.'
  return ''
}
