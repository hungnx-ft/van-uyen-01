<script setup lang="ts">
import type { User } from '~/types'
defineProps<{ students: User[] }>()
defineEmits<{
  reset: [user: User]
  move: [user: User]
  toggle: [user: User]
  remove: [user: User]
  grade: [user: User]
}>()
</script>
<template>
  <div style="overflow-x: auto">
    <table class="leaderboard-table" style="font-size: 0.9rem">
      <thead>
        <tr>
          <th>Họ Tên</th>
          <th>Lớp</th>
          <th>Tài Khoản</th>
          <th>Mật Khẩu</th>
          <th>Hành Động</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="u in students" :key="u.id">
          <td>
            {{ u.fullName }}
            <span v-if="u.isActive === false" class="text-light">(đã khóa)</span>
          </td>
          <td>{{ u.className }}</td>
          <td>{{ u.username || u.id }}</td>
          <td>*****</td>
          <td>
            <div class="flex gap-2" style="flex-wrap: wrap">
              <button
                class="btn btn-sm btn-accent"
                title="Đặt lại mật khẩu"
                @click="$emit('reset', u)"
              >
                🔄
              </button>
              <button class="btn btn-sm btn-primary" @click="$emit('grade', u)">📝 Chấm</button>
              <button
                v-if="u.isClassStudent"
                class="btn btn-sm btn-secondary"
                title="Chuyển lớp"
                @click="$emit('move', u)"
              >
                ⏩
              </button>
              <button
                class="btn btn-sm btn-secondary"
                title="Khóa/mở tài khoản"
                @click="$emit('toggle', u)"
              >
                {{ u.isActive === false ? '🔓' : '🔒' }}
              </button>
              <button
                class="btn btn-sm btn-danger"
                title="Xóa tài khoản"
                @click="$emit('remove', u)"
              >
                🗑️
              </button>
            </div>
          </td>
        </tr>
        <tr v-if="!students.length">
          <td colspan="5" class="empty-state">Chưa có học sinh.</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
