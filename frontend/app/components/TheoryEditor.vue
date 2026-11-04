<script setup lang="ts">
import type { TheoryArticle, TheoryAttachment } from '~/types'
import { mainCategories, subCategories } from '~/utils/exams'
import { isApiEnabled } from '~/utils/api'
import {
  ACCEPTED_FILE_TYPES,
  MAX_ATTACHMENTS,
  MAX_FILE_BYTES,
  fileSizeText,
  isHttpUrl,
  uploadErrorText,
} from '~/utils/theory'

interface PendingFile {
  key: string
  file: File
  error?: string
}
interface PendingLink {
  key: string
  url: string
  title: string
}

const props = defineProps<{ category: string; subcategory: string; article?: TheoryArticle }>(),
  emit = defineEmits<{ saved: [article: TheoryArticle]; close: [] }>()
const {
  upsert,
  createRemoteTheory,
  updateRemoteTheory,
  reloadRemoteTheory,
  uploadRemoteTheoryFile,
  addRemoteTheoryLink,
  deleteRemoteTheoryAttachment,
} = useDatabase()
const { show } = useToast()
const api = isApiEnabled()

const article = reactive<TheoryArticle>(
  props.article
    ? JSON.parse(JSON.stringify(props.article))
    : {
        id: crypto.randomUUID(),
        title: '',
        mainCat: props.category,
        subCat: props.subcategory,
        type: 'reference',
        format: 'mixed',
        icon: '📚',
        desc: '',
        content: '',
        attachments: [],
      },
)
// Editing shows the stored HTML with <br> turned back into line breaks.
article.content = (article.content || '').replace(/<br\s*\/?>/gi, '\n')
// Set once the post exists on the server, so a retry updates instead of duplicating it.
const savedId = ref(api && props.article ? props.article.id : '')
const existing = ref<TheoryAttachment[]>([...(article.attachments || [])])
const removed = ref<TheoryAttachment[]>([])
const files = ref<PendingFile[]>([])
const links = ref<PendingLink[]>([])
const newLinkUrl = ref('')
const newLinkTitle = ref('')
const busy = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)

const legacyFile = computed(() =>
  ['image', 'pdf', 'link'].includes(article.format) ? article.fileData || '' : '',
)
const attachmentCount = computed(
  () =>
    existing.value.length + files.value.length + links.value.length + (legacyFile.value ? 1 : 0),
)
watch(
  () => article.mainCat,
  (value, old) => {
    if (old !== undefined && value !== old) article.subCat = subCategories[value]?.[0]?.id || ''
  },
)

function key() {
  return crypto.randomUUID()
}
function chooseFiles(event: Event) {
  const input = event.target as HTMLInputElement
  for (const file of Array.from(input.files || [])) {
    if (attachmentCount.value >= MAX_ATTACHMENTS) {
      show(`Mỗi bài tối đa ${MAX_ATTACHMENTS} tệp/liên kết.`)
      break
    }
    if (file.size > MAX_FILE_BYTES) {
      show(`${file.name} quá lớn (tối đa ${fileSizeText(MAX_FILE_BYTES)}).`)
      continue
    }
    files.value.push({ key: key(), file })
  }
  input.value = ''
}
function addLink() {
  const url = newLinkUrl.value.trim()
  if (!isHttpUrl(url)) {
    show('Liên kết cần bắt đầu bằng https:// hoặc http://')
    return
  }
  if (attachmentCount.value >= MAX_ATTACHMENTS) {
    show(`Mỗi bài tối đa ${MAX_ATTACHMENTS} tệp/liên kết.`)
    return
  }
  links.value.push({ key: key(), url, title: newLinkTitle.value.trim() })
  newLinkUrl.value = ''
  newLinkTitle.value = ''
}
function removeExisting(item: TheoryAttachment) {
  existing.value = existing.value.filter((a) => a.id !== item.id)
  if (api) removed.value.push(item)
}
// Old single-format posts become ordinary attachments when they are saved again.
async function convertLegacy() {
  const value = legacyFile.value
  if (!value) return
  if (article.format === 'link' && isHttpUrl(value))
    links.value.push({ key: key(), url: value, title: '' })
  else if (value.startsWith('data:')) {
    const blob = await (await fetch(value)).blob()
    const extension = article.format === 'pdf' ? 'pdf' : blob.type.split('/')[1] || 'png'
    files.value.push({
      key: key(),
      file: new File([blob], `${article.title || 'tai-lieu'}.${extension}`, { type: blob.type }),
    })
  }
  article.fileData = ''
  article.format = 'mixed'
}
function html() {
  return article.content.trim().replace(/\n/g, '<br>')
}

async function saveLocal() {
  // Offline mode keeps the browser storage format: text and links only.
  const saved: TheoryArticle = {
    ...article,
    content: html(),
    format: 'mixed',
    fileData: '',
    attachments: [
      ...existing.value,
      ...links.value.map((link) => ({
        id: link.key,
        kind: 'link' as const,
        url: link.url,
        name: link.title || link.url,
      })),
    ],
  }
  upsert('theory_articles', saved)
  emit('saved', saved)
}

async function saveRemote() {
  await convertLegacy()
  const body = { ...article, id: savedId.value || article.id, content: html() }
  const post = savedId.value ? await updateRemoteTheory(body) : await createRemoteTheory(body)
  savedId.value = post.id
  for (const item of [...removed.value]) {
    await deleteRemoteTheoryAttachment(post.id, item.id)
    removed.value = removed.value.filter((a) => a.id !== item.id)
  }
  for (const link of [...links.value]) {
    await addRemoteTheoryLink(post.id, link.url, link.title)
    links.value = links.value.filter((l) => l.key !== link.key)
  }
  // Upload one file at a time and keep failures listed so the teacher can retry.
  for (const item of files.value) {
    try {
      await uploadRemoteTheoryFile(post.id, item.file)
      item.error = undefined
      files.value = files.value.filter((f) => f.key !== item.key)
    } catch (error) {
      item.error = uploadErrorText(error)
    }
  }
  const fresh = await reloadRemoteTheory(post.id)
  existing.value = [...(fresh.attachments || [])]
  if (files.value.length) {
    show(`Đã lưu bài, nhưng ${files.value.length} tệp chưa tải lên được. Hãy bấm Lưu để thử lại.`)
    return
  }
  emit('saved', fresh)
}

async function submit() {
  if (busy.value) return
  if (!article.title.trim()) return show('Chưa nhập tiêu đề!')
  if (!article.content.trim() && !attachmentCount.value)
    return show('Hãy nhập nội dung hoặc thêm ảnh, liên kết, tệp đính kèm.')
  busy.value = true
  try {
    if (api) await saveRemote()
    else await saveLocal()
  } catch (error) {
    show((error as Error).message)
  } finally {
    busy.value = false
  }
}
</script>
<template>
  <BaseModal
    :title="props.article ? 'Sửa Bài Viết Kiến Thức' : 'Đăng Bài Viết Kiến Thức'"
    @close="emit('close')"
  >
    <form class="modal-content" @submit.prevent="submit">
      <div class="input-group">
        <label>
          Tiêu đề bài viết
          <input v-model="article.title" class="input-control" required />
        </label>
      </div>
      <div class="form-row">
        <div class="input-group">
          <label>
            Mục chính
            <select v-model="article.mainCat" class="input-control">
              <option v-for="c in mainCategories" :key="c.id" :value="c.id">{{ c.label }}</option>
            </select>
          </label>
        </div>
        <div class="input-group">
          <label>
            Mục nhỏ
            <select v-model="article.subCat" class="input-control">
              <option v-for="c in subCategories[article.mainCat]" :key="c.id" :value="c.id">
                {{ c.label }}
              </option>
            </select>
          </label>
        </div>
        <div class="input-group">
          <label>
            Loại bài
            <select v-model="article.type" class="input-control">
              <option value="reference">Bài tham khảo</option>
              <option value="sharing">Chia sẻ kinh nghiệm</option>
            </select>
          </label>
        </div>
        <div class="input-group">
          <label>
            Icon
            <input v-model="article.icon" class="input-control" />
          </label>
        </div>
      </div>
      <div class="input-group">
        <label>
          Mô tả ngắn
          <input v-model="article.desc" class="input-control" />
        </label>
      </div>
      <div class="input-group">
        <label>
          Nội dung (hỗ trợ HTML, không giới hạn độ dài)
          <textarea v-model="article.content" class="input-control" style="height: 260px" />
        </label>
      </div>

      <h4 class="font-heading mb-2 text-primary">
        Ảnh, tệp và liên kết ({{ attachmentCount }}/{{ MAX_ATTACHMENTS }})
      </h4>
      <ul v-if="attachmentCount" class="attachment-list mb-3">
        <li v-if="legacyFile">
          <span>📌 Tệp cũ ({{ article.format }}) — sẽ được chuyển thành tệp đính kèm khi lưu</span>
        </li>
        <li v-for="item in existing" :key="item.id">
          <span>
            {{ item.kind === 'image' ? '🖼️' : item.kind === 'link' ? '🔗' : '📎' }}
            {{ item.name }}
            <small v-if="item.size" class="text-light">· {{ fileSizeText(item.size) }}</small>
          </span>
          <button type="button" class="btn btn-sm btn-danger" @click="removeExisting(item)">
            Xóa
          </button>
        </li>
        <li v-for="link in links" :key="link.key">
          <span>
            🔗 {{ link.title || link.url }}
            <small class="text-light">· chưa lưu</small>
          </span>
          <button
            type="button"
            class="btn btn-sm btn-danger"
            @click="links = links.filter((l) => l.key !== link.key)"
          >
            Xóa
          </button>
        </li>
        <li v-for="item in files" :key="item.key">
          <span>
            {{ item.file.type.startsWith('image/') ? '🖼️' : '📎' }} {{ item.file.name }}
            <small class="text-light">· {{ fileSizeText(item.file.size) }} · chưa lưu</small>
            <small v-if="item.error" class="attachment-error">· Lỗi: {{ item.error }}</small>
          </span>
          <button
            type="button"
            class="btn btn-sm btn-danger"
            @click="files = files.filter((f) => f.key !== item.key)"
          >
            Xóa
          </button>
        </li>
      </ul>
      <div v-if="api" class="input-group">
        <button type="button" class="btn btn-outline" @click="fileInput?.click()">
          ＋ Thêm ảnh / tệp (PDF, Word)
        </button>
        <input
          ref="fileInput"
          type="file"
          multiple
          hidden
          :accept="ACCEPTED_FILE_TYPES"
          @change="chooseFiles"
        />
        <small class="text-light">
          Ảnh PNG, JPG, GIF, WebP, AVIF; tài liệu PDF, DOCX. Tối đa
          {{ fileSizeText(MAX_FILE_BYTES) }} mỗi tệp.
        </small>
      </div>
      <p v-else class="text-light">Chế độ ngoại tuyến chỉ lưu nội dung và liên kết.</p>
      <div class="form-row">
        <div class="input-group">
          <label>
            Liên kết (URL)
            <input
              v-model="newLinkUrl"
              type="url"
              class="input-control"
              placeholder="https://..."
              @keydown.enter.prevent="addLink"
            />
          </label>
        </div>
        <div class="input-group">
          <label>
            Tên liên kết (tuỳ chọn)
            <input v-model="newLinkTitle" class="input-control" @keydown.enter.prevent="addLink" />
          </label>
        </div>
      </div>
      <button type="button" class="btn btn-secondary mb-3" @click="addLink">
        ＋ Thêm liên kết
      </button>
      <button class="btn btn-primary w-full" :disabled="busy">
        {{ busy ? 'Đang lưu...' : 'Lưu Đăng' }}
      </button>
    </form>
  </BaseModal>
</template>

<style scoped>
.attachment-list {
  list-style: none;
  padding: 0;
  display: grid;
  gap: 6px;
}
.attachment-list li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.03);
  word-break: break-word;
}
.attachment-error {
  color: #b4232a;
}
</style>
