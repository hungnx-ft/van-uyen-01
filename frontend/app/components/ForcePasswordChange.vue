<script setup lang="ts">
import { MIN_PASSWORD_LENGTH, newPasswordError } from '~/utils/students'
const { user, changePassword, logout } = useAuth(),
  { show } = useToast()
const current = ref(''),
  password = ref(''),
  confirm = ref(''),
  busy = ref(false),
  error = ref('')
async function save() {
  error.value = newPasswordError(current.value, password.value, confirm.value)
  if (error.value || busy.value) return
  busy.value = true
  try {
    await changePassword(current.value, password.value)
    show('Đổi mật khẩu thành công! Hãy đăng nhập lại bằng mật khẩu mới.')
  } catch (e) {
    const message = (e as Error).message
    error.value = /current password is incorrect/i.test(message)
      ? 'Mật khẩu hiện tại không đúng.'
      : message
  } finally {
    busy.value = false
  }
}
</script>
<template>
  <div class="auth-page">
    <form class="card force-password" @submit.prevent="save">
      <h2 class="font-heading text-primary mb-2">🔐 Đổi mật khẩu</h2>
      <p class="text-light mb-3">
        Chào {{ user?.fullName }}! Tài khoản
        <strong>{{ user?.username }}</strong>
        đang dùng mật khẩu mặc định. Hãy đặt mật khẩu mới trước khi bắt đầu học.
      </p>
      <div class="input-group">
        <label>
          Mật khẩu hiện tại
          <input
            v-model="current"
            type="password"
            class="input-control"
            autocomplete="current-password"
            required
          />
        </label>
      </div>
      <div class="input-group">
        <label>
          Mật khẩu mới (ít nhất {{ MIN_PASSWORD_LENGTH }} ký tự)
          <input
            v-model="password"
            type="password"
            class="input-control"
            autocomplete="new-password"
            :minlength="MIN_PASSWORD_LENGTH"
            required
          />
        </label>
      </div>
      <div class="input-group">
        <label>
          Nhập lại mật khẩu mới
          <input
            v-model="confirm"
            type="password"
            class="input-control"
            autocomplete="new-password"
            required
          />
        </label>
      </div>
      <p v-if="error" class="force-password-error" role="alert">{{ error }}</p>
      <button class="btn btn-primary w-full mb-2" :disabled="busy">
        {{ busy ? 'Đang lưu...' : 'Đổi mật khẩu' }}
      </button>
      <button type="button" class="btn btn-outline w-full" @click="logout">Đăng xuất</button>
    </form>
  </div>
</template>

<style scoped>
.auth-page {
  display: flex;
  justify-content: center;
  padding: 48px 16px;
}
.force-password {
  width: 100%;
  max-width: 440px;
}
.force-password-error {
  color: #b4232a;
  margin-bottom: 12px;
}
</style>
