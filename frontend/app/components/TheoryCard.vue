<script setup lang="ts">
import type { TheoryArticle } from '~/types'
defineProps<{ article: TheoryArticle; teacher: boolean }>()
defineEmits<{ open: []; remove: [] }>()
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
    <button
      v-if="teacher && article.type !== 'core'"
      class="btn btn-danger btn-sm mt-2"
      @click.stop="$emit('remove')"
    >
      Xóa bài
    </button>
  </div>
</template>
