<script setup lang="ts">
import type { Answer, Question } from '~/types'
import { scoreOptions } from '~/utils/exams'
defineProps<{
  question: Question
  label: string
  practice: boolean
  mode: 'self' | 'grade' | 'review'
  graded: boolean
  aiAnswer?: { score: number; comment?: string | null }
}>()
const answer = defineModel<Answer>({ required: true })
</script>
<template>
  <div class="question-block">
    <div class="question-title">{{ label }}</div>
    <div class="grading-grid" :class="practice ? 'cols-4' : 'cols-3'">
      <div class="grading-col">
        <span class="grading-col-title">Bài làm của cậu</span>
        <div class="grading-text" style="white-space: pre-wrap">{{ answer.ans || 'Trống' }}</div>
      </div>
      <div class="grading-col">
        <span class="grading-col-title">Đáp án chuẩn / Hướng dẫn chấm</span>
        <div class="grading-text grading-ans" style="white-space: pre-wrap">{{ question.a }}</div>
      </div>
      <div v-if="practice" class="grading-col">
        <span class="grading-col-title">Tự chấm</span>
        <select
          v-if="mode === 'self'"
          v-model.number="answer.selfScore"
          class="score-select"
          :aria-label="`Tự chấm ${label}`"
        >
          <option v-for="score in scoreOptions(question.score)" :key="score" :value="score">
            {{ score }}đ
          </option>
        </select>
        <div v-else class="grading-text">{{ answer.selfScore }}đ</div>
      </div>
      <div class="grading-col" style="background: #fff3cd">
        <span class="grading-col-title">Cô chấm</span>
        <template v-if="mode === 'grade'">
          <select
            v-model.number="answer.teacherScore"
            class="score-select"
            :aria-label="`Cô chấm ${label}`"
          >
            <option v-for="score in scoreOptions(question.score)" :key="score" :value="score">
              {{ score }}đ
            </option>
          </select>
          <input
            v-model="answer.teacherComment"
            class="input-control mt-2"
            :aria-label="`Nhận xét ${label}`"
            placeholder="Nhận xét câu này..."
          />
        </template>
        <template v-else>
          <div class="grading-text">{{ graded ? `${answer.teacherScore}đ` : '⌛' }}</div>
          <p v-if="answer.teacherComment" class="mt-2 text-light">
            Lời phê: {{ answer.teacherComment }}
          </p>
        </template>
      </div>
      <div v-if="aiAnswer" class="grading-col" style="background: #eef4ff">
        <span class="grading-col-title">AI đề xuất</span>
        <div class="grading-text">{{ aiAnswer.score }}đ</div>
        <p v-if="aiAnswer.comment" class="mt-2 text-light">{{ aiAnswer.comment }}</p>
      </div>
    </div>
  </div>
</template>
