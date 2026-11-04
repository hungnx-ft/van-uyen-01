<script setup lang="ts">
import DOMPurify from 'dompurify'
import type { TheoryArticle, TheoryAttachment } from '~/types'
import { isApiEnabled } from '~/utils/api'
import { fileSizeText, isHttpUrl } from '~/utils/theory'
const props = defineProps<{ article: TheoryArticle }>()
defineEmits<{ close: [] }>()
const { fetchRemoteTheoryAttachment } = useDatabase()
const content = computed(() => DOMPurify.sanitize(props.article.content || ''))
const attachments = computed(() => props.article.attachments || [])
const images = computed(() => attachments.value.filter((item) => item.kind === 'image'))
const links = computed(() => attachments.value.filter((item) => item.kind === 'link'))
const files = computed(() => attachments.value.filter((item) => item.kind === 'file'))
// Legacy single-format posts keep their image, PDF or link in fileData.
const legacy = computed(() => {
  const value = props.article.fileData || ''
  if (props.article.format === 'link' && isHttpUrl(value)) return { kind: 'link', value }
  if (
    props.article.format === 'image' &&
    /^data:image\/(png|jpe?g|gif|webp|avif);base64,/i.test(value)
  )
    return { kind: 'image', value }
  if (props.article.format === 'pdf' && /^data:application\/pdf;base64,/i.test(value))
    return { kind: 'pdf', value }
  return null
})
// Protected files need the bearer token, so they are fetched into object URLs.
const objectUrls = reactive<Record<string, string>>({})
const failed = reactive<Record<string, boolean>>({})
const openPdf = ref('')
async function load(item: TheoryAttachment) {
  if (objectUrls[item.id] || !isApiEnabled()) return objectUrls[item.id]
  try {
    const blob = await fetchRemoteTheoryAttachment(item.id)
    objectUrls[item.id] = URL.createObjectURL(blob)
  } catch {
    failed[item.id] = true
  }
  return objectUrls[item.id]
}
async function openFile(item: TheoryAttachment) {
  const url = await load(item)
  if (!url) return
  if (item.mimeType === 'application/pdf') {
    openPdf.value = openPdf.value === item.id ? '' : item.id
    return
  }
  const link = document.createElement('a')
  link.href = url
  link.download = item.name
  link.click()
}
onMounted(() => images.value.forEach(load))
onBeforeUnmount(() => Object.values(objectUrls).forEach((url) => URL.revokeObjectURL(url)))
</script>
<template>
  <BaseModal :title="article.title" @close="$emit('close')">
    <div class="modal-content reader" style="font-size: 1.1rem; line-height: 1.8">
      <div v-if="content" v-html="content" />

      <img
        v-if="legacy?.kind === 'image'"
        :src="legacy.value"
        :alt="article.title"
        class="reader-image"
      />
      <iframe
        v-else-if="legacy?.kind === 'pdf'"
        :src="legacy.value"
        :title="article.title"
        class="reader-pdf"
      />
      <p v-else-if="legacy?.kind === 'link'" class="text-center">
        <a :href="legacy.value" target="_blank" rel="noopener noreferrer" class="btn btn-primary">
          🔗 Mở liên kết ngay
        </a>
      </p>

      <figure v-for="item in images" :key="item.id" class="reader-figure">
        <img
          v-if="objectUrls[item.id]"
          :src="objectUrls[item.id]"
          :alt="item.name"
          class="reader-image"
        />
        <p v-else-if="failed[item.id]" class="text-light">Không tải được ảnh {{ item.name }}.</p>
        <p v-else class="text-light">Đang tải ảnh...</p>
      </figure>

      <div v-if="links.length" class="reader-section">
        <h4 class="font-heading text-primary">🔗 Liên kết</h4>
        <ul>
          <li v-for="item in links" :key="item.id">
            <a :href="item.url" target="_blank" rel="noopener noreferrer">{{ item.name }}</a>
          </li>
        </ul>
      </div>

      <div v-if="files.length" class="reader-section">
        <h4 class="font-heading text-primary">📎 Tệp đính kèm</h4>
        <div v-for="item in files" :key="item.id" class="reader-file">
          <button type="button" class="btn btn-outline btn-sm" @click="openFile(item)">
            {{ item.mimeType === 'application/pdf' ? '📄 Xem' : '⬇️ Tải về' }}
            {{ item.name }}
            <small v-if="item.size" class="text-light">({{ fileSizeText(item.size) }})</small>
          </button>
          <span v-if="failed[item.id]" class="text-light">Không tải được tệp.</span>
          <iframe
            v-if="openPdf === item.id && objectUrls[item.id]"
            :src="objectUrls[item.id]"
            :title="item.name"
            class="reader-pdf"
          />
        </div>
      </div>

      <p v-if="!content && !legacy && !attachments.length" class="text-light">
        Bài viết chưa có nội dung.
      </p>
    </div>
  </BaseModal>
</template>

<style scoped>
.reader-image {
  max-width: 100%;
  border-radius: 8px;
}
.reader-figure {
  margin: 16px 0;
}
.reader-pdf {
  width: 100%;
  height: 65vh;
  border: 0;
  margin-top: 8px;
}
.reader-section {
  margin-top: 20px;
}
.reader-file {
  margin: 8px 0;
}
</style>
