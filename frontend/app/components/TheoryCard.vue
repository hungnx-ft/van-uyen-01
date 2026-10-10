<script setup lang="ts">
import type { TheoryArticle } from '~/types'
defineProps<{ article: TheoryArticle; teacher: boolean }>()
defineEmits<{ open: []; edit: []; remove: [] }>()
</script>
<template>
  <div
    class="card floating-doc"
    style="position: relative; cursor: pointer"
    role="button"
    tabindex="0"
    @click="$emit('open')"
    @keydown.enter.self="$emit('open')"
  >
    <div class="card-badge">
      {{
        article.type === 'core'
          ? 'Kiến thức cốt lõi'
          : article.type === 'reference'
            ? 'Bài tham khảo'
            : 'Chia sẻ kinh nghiệm'
      }}
      | {{ article.format }}
    </div>
    <span class="card-icon">{{ article.icon }}</span>
    <h3 class="card-title mt-2">{{ article.title }}</h3>
    <p class="card-desc">{{ article.desc }}</p>
    <template v-if="teacher && article.type !== 'core'">
      <div class="theory-actions">
        <button class="btn btn-outline btn-sm" @click.stop="$emit('edit')">Sửa bài</button>
        <button class="btn btn-danger btn-sm" @click.stop="$emit('remove')">Xóa bài</button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.theory-actions { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 8px; }
</style>
