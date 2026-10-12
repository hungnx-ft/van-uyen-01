<script setup lang="ts">
import type { TheoryArticle } from '~/types'
import { mainCategories, subCategories } from '~/utils/exams'
const props = defineProps<{ category: string; subcategory: string; article?: TheoryArticle }>(),
  emit = defineEmits<{ save: [article: TheoryArticle]; close: [] }>()
const { show } = useToast()
const article = reactive<TheoryArticle>(
  props.article
    ? JSON.parse(JSON.stringify(props.article))
    : {
        id: crypto.randomUUID(),
        title: '',
        mainCat: props.category,
        subCat: props.subcategory,
        type: 'reference',
        format: 'text',
        icon: '📚',
        desc: '',
        content: '',
        fileData: '',
      },
)
const loading = ref(false)
watch(
  () => article.mainCat,
  (value) => (article.subCat = subCategories[value]?.[0]?.id || ''),
)
watch(
  () => article.format,
  () => (article.fileData = ''),
)
async function readFile(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  if (file.size > 5 * 1024 * 1024) {
    show('File quá lớn! Vui lòng chọn file dưới 5MB.')
    return
  }
  loading.value = true
  try {
    article.fileData = await new Promise<string>((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => resolve(String(reader.result))
      reader.onerror = reject
      reader.readAsDataURL(file)
    })
  } catch {
    show('Không thể đọc file.')
  } finally {
    loading.value = false
  }
}
function submit() {
  if (article.format === 'text' && !article.content.trim()) {
    show('Chưa nhập nội dung!')
    return
  }
  if (article.format !== 'text' && !article.fileData) {
    show('Chưa chọn tài liệu!')
    return
  }
  if (article.format === 'link' && !/^https?:\/\//i.test(article.fileData || '')) {
    show('Liên kết cần bắt đầu bằng https:// hoặc http://')
    return
  }
  emit('save', { ...article, content: article.content.replace(/\n/g, '<br>') })
}
</script>
<template>
  <BaseModal
    :title="article.title ? 'Sửa Bài Viết Kiến Thức' : 'Đăng Bài Viết Kiến Thức'"
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
          Định dạng
          <select v-model="article.format" class="input-control">
            <option value="text">Bài viết (Text)</option>
            <option value="link">Đường dẫn (Link)</option>
            <option value="image">Tải lên Ảnh</option>
            <option value="pdf">Tải lên PDF</option>
          </select>
        </label>
      </div>
      <div v-if="['image', 'pdf'].includes(article.format)" class="input-group">
        <label>
          Chọn File (Tối đa 5MB)
          <input
            type="file"
            class="input-control"
            :accept="
              article.format === 'pdf'
                ? 'application/pdf'
                : 'image/png,image/jpeg,image/gif,image/webp,image/avif'
            "
            @change="readFile"
          />
        </label>
      </div>
      <div v-if="article.format === 'link'" class="input-group">
        <label>
          Nhập đường dẫn (URL)
          <input v-model="article.fileData" type="url" class="input-control" required />
        </label>
      </div>
      <div class="input-group">
        <label>
          Mô tả ngắn
          <input v-model="article.desc" class="input-control" />
        </label>
      </div>
      <div v-if="article.format === 'text'" class="input-group">
        <label>
          Nội dung (Hỗ trợ HTML)
          <textarea v-model="article.content" class="input-control" style="height: 300px" />
        </label>
      </div>
      <button class="btn btn-primary" :disabled="loading">
        {{ loading ? 'Đang đọc file...' : 'Lưu Đăng' }}
      </button>
    </form>
  </BaseModal>
</template>
