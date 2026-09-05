<script setup lang="ts">
const { user, changePassword, logout } = useAuth(),
  { show } = useToast()
const open = ref(false),
  old = ref(''),
  password = ref('')
async function save() {
  try {
    await changePassword(old.value, password.value)
    old.value = ''
    password.value = ''
    show('Đổi mật khẩu thành công!')
  } catch (e) {
    show((e as Error).message)
  }
}
</script>
<template>
  <div style="position: relative">
    <button class="btn btn-outline" :aria-expanded="open" @click="open = !open">
      {{ user?.fullName }} ▾
    </button>
    <div v-if="open" class="card dropdown">
      <form @submit.prevent="save">
        <h4 class="font-heading mb-2 text-primary">Cài đặt Tài khoản</h4>
        <div class="input-group">
          <input
            v-model="old"
            type="password"
            class="input-control"
            placeholder="Mật khẩu cũ"
            aria-label="Mật khẩu cũ"
            autocomplete="current-password"
            required
          />
        </div>
        <div class="input-group">
          <input
            v-model="password"
            type="password"
            class="input-control"
            placeholder="Mật khẩu mới"
            aria-label="Mật khẩu mới"
            autocomplete="new-password"
            required
          />
        </div>
        <button class="btn btn-secondary w-full mb-3">Đổi Mật Khẩu</button>
      </form>
      <button class="btn btn-danger w-full" @click="logout">Đăng xuất</button>
    </div>
  </div>
</template>
