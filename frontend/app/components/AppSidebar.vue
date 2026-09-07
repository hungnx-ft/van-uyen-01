<script setup lang="ts">
defineProps<{ open: boolean }>()
const { user, isTeacher } = useAuth()
const links = computed(() => [
  { to: '/', label: '🏡 Trang chủ' },
  { to: '/theory', label: '🌿 Góc kiến thức' },
  { to: '/practice', label: '🌸 Góc luyện tập' },
  { to: '/exams', label: '🍁 Góc thi thử' },
  ...(isTeacher.value
    ? [
        { to: '/manage', label: '🍀 Góc quản lý' },
        { to: '/analytics', label: '📈 Góc phân tích' },
      ]
    : [{ to: '/study', label: '📊 Góc học tập' }]),
])
</script>
<template>
  <nav class="sidebar" :class="{ open }" aria-label="Điều hướng chính">
    <div class="sidebar-header">
      <div class="sidebar-logo">🌸 VĂN UYỂN</div>
      <div class="sidebar-slogan">Nơi chữ nghĩa nở hoa 🌿</div>
    </div>
    <div class="sidebar-user">
      <div class="sidebar-user-avatar">{{ isTeacher ? '👩‍🏫' : '🎒' }}</div>
      <div class="sidebar-user-info">
        <div class="sidebar-user-name">{{ user?.fullName }}</div>
        <div class="sidebar-user-role">
          {{
            isTeacher ? 'Giáo viên' : `${user?.className || 'Tự do'} - ${user?.schoolName || ''}`
          }}
        </div>
      </div>
    </div>
    <div class="sidebar-nav">
      <NuxtLink
        v-for="link in links"
        :key="link.to"
        :to="link.to"
        class="nav-item"
        exact-active-class="active"
      >
        {{ link.label }}
      </NuxtLink>
    </div>
    <div class="sidebar-footer">
      👩‍🏫
      <b>Hà Thanh Hằng</b>
      <br />
      GV Ngữ văn THCS Yên Phong
      <br />
      <i class="fa-solid fa-phone" />
      <a href="tel:0977099420">0977 099 420</a>
    </div>
  </nav>
</template>
