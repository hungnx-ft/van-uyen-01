<script setup lang="ts">
import type { Result } from '~/types'
defineProps<{ results: Result[]; teacher?: boolean }>()
defineEmits<{ review: [result: Result]; grade: [result: Result] }>()
</script>
<template>
  <div style="overflow-x: auto">
    <table class="leaderboard-table" style="font-size: 0.95rem; min-width: 600px">
      <thead>
        <tr>
          <th>Tên đề</th>
          <th>Phân loại</th>
          <th>Điểm số</th>
          <th>Trạng thái</th>
          <th>Hành động</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(r, i) in results" :key="r.id">
          <td>{{ r.examTitle }} (Lần {{ r.attempt || 1 }})</td>
          <td>{{ r.examType === 'practice' ? 'Luyện tập' : 'Thi thử' }}</td>
          <td>{{ r.status === 'graded' ? `${r.teacherScore}/${r.maxScore}` : 'Chờ chấm' }}</td>
          <td>{{ r.status === 'graded' ? 'Đã chấm' : 'Đã nộp' }}</td>
          <td>
            <div class="result-actions">
              <button class="btn btn-sm btn-outline" @click="$emit('review', r)">Xem bài</button>
              <button v-if="teacher" class="btn btn-sm btn-primary" @click="$emit('grade', r)">
                Chấm bài
              </button>
            </div>
          </td>
        </tr>
        <tr v-if="!results.length">
          <td colspan="5" class="empty-state">
            Chưa có lịch sử làm bài. Hãy bắt đầu luyện tập nhé!
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.result-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
</style>
