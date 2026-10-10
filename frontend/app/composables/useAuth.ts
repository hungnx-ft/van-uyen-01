import type { User } from '~/types'
import { restoreSession, saveSession } from '~/utils/session'
import { apiRequest, clearApiSession, isApiEnabled, loginApi, registerApi } from '~/utils/api'

export function useAuth() {
  const { data, set, ready, syncRemote } = useDatabase()
  const { show } = useToast()
  const userId = useState<string | null>('current-user-id', () => null)
  const authReady = useState('auth-ready', () => false)
  const remoteUser = useState<User | null>('remote-user', () => null)
  const user = computed(() =>
    isApiEnabled()
      ? remoteUser.value
      : ready.value
        ? (data.value.users.find((account) => account.id === userId.value) ?? null)
        : null,
  )
  const isTeacher = computed(() => user.value?.role === 'teacher')
  function restore() {
    if (isApiEnabled()) {
      return apiRequest<ApiUser>('/auth/me')
        .then(async (account) => {
          remoteUser.value = mapApiUser(account)
          await syncRemote()
        })
        .catch(() => {
          clearApiSession()
          remoteUser.value = null
        })
        .finally(() => {
          authReady.value = true
        })
    }
    if (!ready.value) return
    try {
      userId.value = restoreSession(sessionStorage, data.value.users)
    } catch {
      userId.value = null
      show('Không thể khôi phục phiên. Vui lòng đăng nhập lại.')
    } finally {
      authReady.value = true
    }
  }
  function establish(account: User) {
    saveSession(sessionStorage, account.id)
    userId.value = account.id
  }
  function login(id: string, password: string) {
    if (isApiEnabled()) {
      return loginApi<ApiUser>(id.trim(), password).then(async (account) => {
        remoteUser.value = mapApiUser(account)
        await syncRemote()
      })
    }
    if (!ready.value) throw new Error('Kho dữ liệu chưa sẵn sàng.')
    const found = data.value.users.find(
      (account) => account.id === id.trim() && account.password === password,
    )
    if (!found) throw new Error('Tài khoản hoặc mật khẩu không đúng!')
    establish(found)
  }
  function register(id: string, password: string, fullName: string) {
    if (isApiEnabled()) {
      return registerApi<ApiUser>(id.trim(), password, fullName.trim()).then(async (account) => {
        remoteUser.value = mapApiUser(account)
        await syncRemote()
      })
    }
    id = id.trim()
    fullName = fullName.trim()
    if (!id || !password || !fullName) throw new Error('Vui lòng điền đầy đủ thông tin.')
    if (data.value.users.some((account) => account.id === id))
      throw new Error('Tên đăng nhập đã tồn tại.')
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
    try {
      establish(account)
    } catch {
      throw new Error(
        'Tài khoản đã được tạo nhưng chưa lưu được phiên. Hãy cho phép bộ nhớ phiên rồi đăng nhập lại.',
      )
    }
  }
  function changePassword(oldPassword: string, password: string) {
    if (isApiEnabled()) {
      return apiRequest('/auth/password', {
        method: 'PUT',
        body: JSON.stringify({ current_password: oldPassword, new_password: password }),
      }).then(async () => {
        clearApiSession()
        remoteUser.value = null
        await navigateTo('/login')
      })
    }
    if (!user.value || user.value.password !== oldPassword)
      throw new Error('Mật khẩu cũ không đúng!')
    if (!password.trim()) throw new Error('Nhập mật khẩu mới.')
    const updated = { ...user.value, password }
    set(
      'users',
      data.value.users.map((account) => (account.id === updated.id ? updated : account)),
    )
  }
  async function logout() {
    if (isApiEnabled()) {
      try {
        await apiRequest('/auth/logout', { method: 'POST' })
      } catch {
        // The local session is still cleared if the server session already expired.
      }
      clearApiSession()
      remoteUser.value = null
    }
    userId.value = null
    try {
      saveSession(sessionStorage, null)
    } catch (e) {
      show((e as Error).message)
    }
    await navigateTo('/login')
  }
  function requireTeacher() {
    if (!isTeacher.value) throw new Error('Chức năng dành cho giáo viên.')
  }
  return {
    user,
    isTeacher,
    authReady,
    restore,
    login,
    register,
    changePassword,
    logout,
    requireTeacher,
  }
}

interface ApiUser {
  id: number
  username: string
  full_name: string
  school_name: string | null
  role: 'Teacher' | 'Student'
  class_id: number | null
  is_active: boolean
}

function mapApiUser(account: ApiUser): User {
  return {
    id: String(account.id),
    username: account.username,
    password: '',
    role: account.role === 'Teacher' ? 'teacher' : 'student',
    fullName: account.full_name,
    classId: account.class_id === null ? undefined : String(account.class_id),
    schoolName: account.school_name || undefined,
    isClassStudent: account.class_id !== null,
  }
}
