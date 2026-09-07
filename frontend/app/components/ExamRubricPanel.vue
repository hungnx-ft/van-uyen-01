<script setup lang="ts">
import type { Exam, ExamType } from '~/types'
import { isApiEnabled } from '~/utils/api'

const props = defineProps<{ exam: Exam; type: ExamType }>()
const emit = defineEmits<{ close: [] }>()
const { getRemoteRubric, uploadRemoteRubric, updateRemoteRubric, deleteRemoteRubric } =
  useDatabase()
const { show } = useToast()
const rubric = ref<{
  id: number
  content_text: string
  original_filename?: string | null
  version: number
} | null>(null)
const content = ref('')
const loading = ref(true)
const saving = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)

async function load() {
  if (!isApiEnabled()) {
    loading.value = false
    return
  }
  try {
    rubric.value = await getRemoteRubric(props.exam.id, props.type)
    content.value = rubric.value.content_text
  } catch (error) {
    if (!String((error as Error).message).includes('404')) show((error as Error).message)
  } finally {
    loading.value = false
  }
}
async function upload(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  saving.value = true
  try {
    rubric.value = await uploadRemoteRubric(props.exam.id, props.type, file)
    content.value = rubric.value.content_text
    show('Đã tải barem thành công.')
  } catch (error) {
    show((error as Error).message)
  } finally {
    saving.value = false
    if (fileInput.value) fileInput.value.value = ''
  }
}
async function save() {
  if (!content.value.trim()) return show('Nội dung barem không được để trống.')
  saving.value = true
  try {
    rubric.value = await updateRemoteRubric(props.exam.id, props.type, content.value)
    content.value = rubric.value.content_text
    show('Đã lưu phiên bản barem mới.')
  } catch (error) {
    show((error as Error).message)
  } finally {
    saving.value = false
  }
}
async function remove() {
  if (!rubric.value || !window.confirm('Xóa barem của đề này?')) return
  saving.value = true
  try {
    await deleteRemoteRubric(props.exam.id, props.type)
    rubric.value = null
    content.value = ''
    show('Đã xóa barem.')
  } catch (error) {
    show((error as Error).message)
  } finally {
    saving.value = false
  }
}
onMounted(load)
</script>

<template>
  <BaseModal :title="`Barem: ${exam.title}`" wide @close="emit('close')">
    <div v-if="!isApiEnabled()" class="empty-state">
      Barem cần backend API và chưa hỗ trợ ở chế độ local.
    </div>
    <template v-else>
      <p v-if="loading" class="text-light">Đang tải barem...</p>
      <template v-else>
        <div class="flex justify-between items-center mb-3" style="flex-wrap: wrap; gap: 10px">
          <span class="text-light">
            {{
              rubric
                ? `Phiên bản ${rubric.version}${rubric.original_filename ? ` · ${rubric.original_filename}` : ''}`
                : 'Chưa có barem'
            }}
          </span>
          <div class="flex gap-2">
            <button class="btn btn-secondary btn-sm" :disabled="saving" @click="fileInput?.click()">
              Upload file
            </button>
            <button v-if="rubric" class="btn btn-danger btn-sm" :disabled="saving" @click="remove">
              Xóa
            </button>
          </div>
          <input
            ref="fileInput"
            type="file"
            accept=".pdf,.docx,.txt,.md,.markdown"
            hidden
            @change="upload"
          />
        </div>
        <textarea
          v-model="content"
          class="input-control"
          rows="18"
          placeholder="Dán hoặc chỉnh sửa barem tại đây..."
        />
        <button v-if="rubric" class="btn btn-primary mt-3" :disabled="saving" @click="save">
          Lưu phiên bản mới
        </button>
        <p v-else class="text-light mt-3">
          Upload PDF, DOCX, TXT hoặc Markdown để tạo barem cho đề.
        </p>
      </template>
    </template>
  </BaseModal>
</template>
