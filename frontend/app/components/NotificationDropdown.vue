<script setup lang="ts">
const { user, isTeacher } = useAuth(),
  { data } = useDatabase(),
  { start } = useWorkspace(),
  { show } = useToast()
const open = ref(false)
const pending = computed(() =>
  data.value.assignments
    .filter(
      (a) =>
        a.classId === user.value?.classId &&
        !data.value.results.some(
          (r) =>
            r.studentId === user.value?.id && r.examId === a.examId && r.examType === a.examType,
        ),
    )
    .sort((a, b) => b.createdAt - a.createdAt),
)
async function choose(a: (typeof pending.value)[number]) {
  const exam = data.value[a.examType === 'practice' ? 'practice_exams' : 'mock_exams'].find(
    (e) => e.id === a.examId,
  )
  if (!exam) {
    show('Đề này đã bị xóa.')
    return
  }
  open.value = false
  await navigateTo(a.examType === 'practice' ? '/practice' : '/exams')
  start(a.examType, exam)
}
</script>
<template>
  <div v-if="!isTeacher" style="position: relative">
    <button
      class="btn btn-outline"
      aria-label="Thông báo"
      :aria-expanded="open"
      @click="open = !open"
    >
      🔔
      <span v-if="pending.length">{{ pending.length }}</span>
    </button>
    <div v-if="open" class="card dropdown" style="width: 320px; max-height: 400px; overflow: auto">
      <h4 class="font-heading mb-2">Thông báo mới</h4>
      <p v-if="!pending.length" class="text-light">Không có đề nào mới được giao.</p>
      <button
        v-for="a in pending"
        :key="a.id"
        class="btn btn-outline w-full mb-2"
        style="text-align: left; display: block"
        @click="choose(a)"
      >
        Cô Hằng vừa giao đề mới:
        <br />
        <b>{{ a.examTitle }}</b>
        <br />
        <small>{{ new Date(a.createdAt).toLocaleDateString('vi-VN') }}</small>
      </button>
    </div>
  </div>
</template>
