<script setup lang="ts">
const props = defineProps<{ register?: boolean }>()
const { login, register: registerAccount, user, logout } = useAuth(),
  { show } = useToast()
const id = ref(''),
  password = ref(''),
  name = ref(''),
  activeTab = ref<'student' | 'teacher'>('student')
async function submit() {
  try {
    if (props.register) await registerAccount(id.value, password.value, name.value)
    else {
      await login(id.value, password.value)
      if (user.value?.role !== activeTab.value) {
        await logout()
        throw new Error(
          `Tài khoản này không thuộc nhóm ${activeTab.value === 'teacher' ? 'giáo viên' : 'học sinh'}.`,
        )
      }
    }
    await navigateTo('/')
  } catch (e) {
    show((e as Error).message)
  }
}
</script>
<template>
  <div class="workspace-overlay active" style="background: var(--bg-color); overflow: auto">
    <div class="onboarding-container">
      <div class="floral-decoration floral-tl">🌸</div>
      <div class="floral-decoration floral-br">🌿</div>
      <h1 class="font-heading text-primary mb-1" style="font-size: 2.2rem">🌸 VĂN UYỂN</h1>
      <p class="text-light mb-4" style="font-style: italic">Nơi chữ nghĩa nở hoa</p>
      <div
        v-if="!register"
        class="tabs mb-4"
        style="justify-content: center"
        aria-label="Loại tài khoản đăng nhập"
      >
        <button
          type="button"
          class="tab-btn"
          :class="{ active: activeTab === 'student' }"
          @click="activeTab = 'student'"
        >
          🎒 Học sinh
        </button>
        <button
          type="button"
          class="tab-btn"
          :class="{ active: activeTab === 'teacher' }"
          @click="activeTab = 'teacher'"
        >
          👩‍🏫 Giáo viên
        </button>
      </div>
      <form @submit.prevent="submit">
        <h2 v-if="!register" class="font-heading mb-2 text-primary">
          {{ activeTab === 'teacher' ? 'Đăng nhập giáo viên' : 'Đăng nhập học sinh' }}
        </h2>
        <p v-if="!register" class="mb-3 text-light">
          {{
            activeTab === 'teacher'
              ? 'Dành cho giáo viên quản lý lớp, đề và chấm bài.'
              : 'Dành cho học sinh học tập và làm bài.'
          }}
        </p>
        <h2 v-if="register" class="font-heading mb-2 text-primary">🌱 Đăng ký Tài khoản Tự do</h2>
        <p v-if="register" class="mb-3 text-light">
          Dành cho học sinh tự học không có tài khoản của trường
        </p>
        <div class="input-group">
          <label for="auth-id">👤 Tên đăng nhập</label>
          <input id="auth-id" v-model="id" class="input-control" autocomplete="username" required />
        </div>
        <div class="input-group">
          <label for="auth-password">🔒 Mật khẩu</label>
          <input
            id="auth-password"
            v-model="password"
            type="password"
            class="input-control"
            :autocomplete="register ? 'new-password' : 'current-password'"
            required
          />
        </div>
        <div v-if="register" class="input-group">
          <label for="auth-name">📛 Họ và tên đầy đủ</label>
          <input id="auth-name" v-model="name" class="input-control" autocomplete="name" required />
        </div>
        <button
          type="submit"
          class="btn btn-accent mt-2 w-full"
          style="font-size: 1.1rem; padding: 12px"
        >
          {{ register ? 'Tạo tài khoản 🚀' : 'Đăng nhập hệ thống 🔓' }}
        </button>
      </form>
      <NuxtLink
        v-if="register || activeTab === 'student'"
        class="toggle-login"
        :to="register ? '/login' : '/register'"
      >
        {{ register ? '🔑 Đã có tài khoản? Đăng nhập ngay' : '🌱 Đăng ký tài khoản tự do' }}
      </NuxtLink>
    </div>
  </div>
</template>
