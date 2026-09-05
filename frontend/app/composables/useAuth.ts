import type { User } from '~/types'
export function useAuth() {
  const { data, set } = useDatabase()
  const user = useState<User | null>('current-user', () => null)
  const isTeacher = computed(() => user.value?.role === 'teacher')
  function restore() {
    try {
      const saved = JSON.parse(sessionStorage.getItem('vu_current_user') || 'null')
      user.value = data.value.users.find((u) => u.id === saved?.id) || null
    } catch {
      sessionStorage.removeItem('vu_current_user')
    }
  }
  function establish(account: User) {
    sessionStorage.setItem('vu_current_user', JSON.stringify({ id: account.id }))
    user.value = { ...account }
  }
  function login(id: string, password: string) {
    const found = data.value.users.find((u) => u.id === id.trim() && u.password === password)
    if (!found) throw new Error('Tài khoản hoặc mật khẩu không đúng!')
    establish(found)
  }
  function register(id: string, password: string, fullName: string) {
    id = id.trim()
    fullName = fullName.trim()
    if (!id || !password || !fullName) throw new Error('Vui lòng điền đầy đủ thông tin.')
    if (data.value.users.some((u) => u.id === id)) throw new Error('Tên đăng nhập đã tồn tại.')
    const account: User = {
      id,
      password,
      fullName,
      role: 'student',
      classId: 'free_class',
      className: 'Lớp Tự do',
      schoolName: 'Học sinh Tự do',
      isClassStudent: false,
    }
    set('users', [...data.value.users, account])
    establish(account)
  }
  function changePassword(oldPassword: string, password: string) {
    if (!user.value || user.value.password !== oldPassword)
      throw new Error('Mật khẩu cũ không đúng!')
    if (!password.trim()) throw new Error('Nhập mật khẩu mới.')
    const updated = { ...user.value, password }
    set(
      'users',
      data.value.users.map((u) => (u.id === updated.id ? updated : u)),
    )
    establish(updated)
  }
  async function logout() {
    sessionStorage.removeItem('vu_current_user')
    user.value = null
    await navigateTo('/login')
  }
  function requireTeacher() {
    if (!isTeacher.value) throw new Error('Chức năng dành cho giáo viên.')
  }
  return { user, isTeacher, restore, login, register, changePassword, logout, requireTeacher }
}
