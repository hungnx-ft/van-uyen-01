<script setup lang="ts">
import { apiRequest, isApiEnabled } from '~/utils/api'

interface AISettings {
  provider: string
  model: string
  base_url: string | null
  has_api_key: boolean
  is_enabled: boolean
}

const settings = ref<AISettings>({
  provider: 'openai-compatible',
  model: '',
  base_url: null,
  has_api_key: false,
  is_enabled: false,
})
const apiKey = ref('')
const busy = ref(false)
const { show } = useToast()

async function load() {
  if (!isApiEnabled()) return
  try {
    settings.value = await apiRequest<AISettings>('/ai/settings')
  } catch (error) {
    show((error as Error).message)
  }
}

async function save() {
  if (busy.value) return
  busy.value = true
  try {
    settings.value = await apiRequest<AISettings>('/ai/settings', {
      method: 'PUT',
      body: JSON.stringify({
        provider: settings.value.provider,
        model: settings.value.model,
        base_url: settings.value.base_url || null,
        api_key: apiKey.value || null,
        is_enabled: settings.value.is_enabled,
      }),
    })
    apiKey.value = ''
    show('Đã lưu cấu hình AI.')
  } catch (error) {
    show((error as Error).message)
  } finally {
    busy.value = false
  }
}

async function testConnection() {
  if (busy.value) return
  try {
    await save()
    busy.value = true
    const result = await apiRequest<{ ok: boolean; message: string }>('/ai/test-connection', {
      method: 'POST',
    })
    show(result.message)
  } catch (error) {
    show((error as Error).message)
  } finally {
    busy.value = false
  }
}

async function clearKey() {
  if (busy.value) return
  busy.value = true
  try {
    settings.value = await apiRequest<AISettings>('/ai/settings/key', { method: 'DELETE' })
    apiKey.value = ''
    show('Đã xóa API key AI.')
  } catch (error) {
    show((error as Error).message)
  } finally {
    busy.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="ai-settings-panel">
    <h3 class="font-heading mb-3 text-primary">🤖 Cài đặt AI</h3>
    <p v-if="!isApiEnabled()" class="text-light">Cần bật Backend API để sử dụng AI.</p>
    <form v-else @submit.prevent="save">
      <div class="input-group">
        <label>
          Provider
          <select v-model="settings.provider" class="input-control">
            <option value="openai-compatible">OpenAI-compatible</option>
            <option value="openai">OpenAI</option>
            <option value="anthropic">Anthropic</option>
            <option value="google">Google Gemini</option>
          </select>
        </label>
      </div>
      <div class="input-group">
        <label>
          Model
          <input v-model="settings.model" class="input-control" placeholder="Tên model" required />
        </label>
      </div>
      <div class="input-group">
        <label>
          Base URL <span class="text-light">(tùy chọn)</span>
          <input
            v-model="settings.base_url"
            class="input-control"
            placeholder="https://api.openai.com/v1"
          />
        </label>
      </div>
      <div class="input-group">
        <label>
          API key
          <input v-model="apiKey" class="input-control" type="password" :placeholder="settings.has_api_key ? 'Đã lưu — nhập lại nếu muốn thay' : 'Nhập API key'" />
        </label>
      </div>
      <label class="flex gap-2 items-center mb-3">
        <input v-model="settings.is_enabled" type="checkbox" /> Bật sử dụng AI
      </label>
      <div class="flex gap-2" style="flex-wrap: wrap">
        <button class="btn btn-primary" :disabled="busy">Lưu cấu hình</button>
        <button type="button" class="btn btn-secondary" :disabled="busy" @click="testConnection">
          Kiểm tra kết nối
        </button>
        <button v-if="settings.has_api_key" type="button" class="btn btn-danger" :disabled="busy" @click="clearKey">
          Xóa API key
        </button>
      </div>
    </form>
  </div>
</template>
