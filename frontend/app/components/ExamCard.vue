<script setup lang="ts">
import type { Exam, ExamType, Result } from '~/types'
import { totalScore } from '~/utils/exams'
const props = defineProps<{ exam: Exam; type: ExamType; results: Result[]; teacher: boolean }>()
const emit = defineEmits<{
  start: []
  edit: []
  remove: []
  assign: []
  review: [result: Result]
  grade: [result: Result]
}>()
const menu = ref(false),
  pending = computed(() => props.results.filter((r) => r.status === 'pending'))
const icons: Record<string, string> = {
  tho: '🌸',
  truyen: '🍁',
  'thong-tin': '🌿',
  'nghi-luan': '🍀',
}
function choose(action: 'edit' | 'remove' | 'assign') {
  menu.value = false
  if (action === 'edit') emit('edit')
  else if (action === 'remove') emit('remove')
  else emit('assign')
}
</script>
<template>
  <div
    class="card text-center floating-doc"
    style="position: relative"
    :style="type === 'mock' ? { borderColor: 'var(--accent)' } : {}"
  >
    <span class="card-icon">{{ type === 'mock' ? '⏱️' : icons[exam.genre || ''] || '📝' }}</span>
    <h3 class="card-title mt-2">{{ exam.title }}</h3>
    <p class="text-light">
      {{ exam.questions.length }} {{ exam.questions.length === 1 ? 'bài viết' : 'câu hỏi' }} | Tổng
      {{ totalScore(exam) }} điểm
    </p>
    <template v-if="teacher">
      <div style="position: absolute; top: 10px; right: 10px">
        <button class="btn btn-sm btn-secondary" aria-label="Thao tác đề" @click="menu = !menu">
          ⋯
        </button>
        <div v-if="menu" class="card dropdown" style="min-width: 130px">
          <button class="btn btn-sm btn-outline w-full mb-1" @click="choose('edit')">Sửa đề</button>
          <button class="btn btn-sm btn-danger w-full mb-1" @click="choose('remove')">
            Xóa đề
          </button>
          <button class="btn btn-sm btn-primary w-full" @click="choose('assign')">Giao đề</button>
        </div>
      </div>
      <div
        v-if="pending.length"
        class="mt-3"
        style="background: #fff3cd; padding: 12px; border-radius: 8px"
      >
        <p>📥 Có {{ pending.length }} bài chờ chấm</p>
        <button class="btn btn-sm btn-primary mt-2" @click="$emit('grade', pending[0]!)">
          Chấm ngay
        </button>
      </div>
      <p v-else class="mt-3 text-light">✅ Không có bài chờ chấm</p>
    </template>
    <template v-else>
      <div v-if="results.length" class="mt-3">
        <h4 class="font-heading mb-2">📜 Lịch sử làm bài:</h4>
        <button
          v-for="(r, i) in results"
          :key="r.id"
          class="btn btn-sm btn-outline w-full mb-2"
          style="justify-content: space-between"
          @click="$emit('review', r)"
        >
          <span>Lần {{ r.attempt || i + 1 }}</span>
          <span>{{ r.status === 'graded' ? `${r.teacherScore}đ` : '⌛ Chờ chấm' }}</span>
        </button>
      </div>
      <button
        class="btn mt-3 w-full"
        :class="type === 'practice' ? 'btn-primary' : 'btn-accent'"
        @click="$emit('start')"
      >
        {{
          results.length
            ? `Làm lại đề (Lần ${results.length + 1})`
            : type === 'practice'
              ? 'Làm bài ngay →'
              : 'Thi Ngay ⚑'
        }}
      </button>
    </template>
  </div>
</template>
