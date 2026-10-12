<script setup lang="ts">
import DOMPurify from 'dompurify'
import type { TheoryArticle } from '~/types'
const props = defineProps<{ article: TheoryArticle }>()
defineEmits<{ close: [] }>()
const content = computed(() => DOMPurify.sanitize(props.article.content))
const file = computed(() => {
  const value = props.article.fileData || ''
  if (/^https?:\/\//i.test(value)) return value
  if (
    props.article.format === 'image' &&
    /^data:image\/(png|jpe?g|gif|webp|avif);base64,/i.test(value)
  )
    return value
  if (props.article.format === 'pdf' && /^data:application\/pdf;base64,/i.test(value)) return value
  return ''
})
</script>
<template>
  <BaseModal :title="article.title" @close="$emit('close')">
    <div class="modal-content" style="font-size: 1.1rem; line-height: 1.8">
      <img
        v-if="article.format === 'image' && file"
        :src="file"
        :alt="article.title"
        style="max-width: 100%; border-radius: 8px"
      />
      <iframe
        v-else-if="article.format === 'pdf' && file"
        :src="file"
        :title="article.title"
        style="width: 100%; height: 65vh; border: 0"
      />
      <div v-else-if="article.format === 'link'" class="text-center">
        <p class="mb-3">Bài học này là một liên kết ngoài.</p>
        <a
          v-if="file"
          :href="file"
          target="_blank"
          rel="noopener noreferrer"
          class="btn btn-primary"
        >
          🔗 Mở liên kết ngay
        </a>
      </div>
      <div v-else-if="article.format === 'text'" v-html="content" />
      <p v-else>Không thể mở định dạng tài liệu này.</p>
    </div>
  </BaseModal>
</template>
