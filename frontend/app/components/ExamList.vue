<script setup lang="ts">
import type { Exam, ExamType } from '~/types'
import { practiceGroups, mockGroups } from '~/utils/exams'
import { isApiEnabled } from '~/utils/api'
const props = defineProps<{ type: ExamType }>()
const { data, upsert, remove, set, createRemoteExam, updateRemoteExam, deleteRemoteExam } =
    useDatabase(),
  { user, isTeacher, requireTeacher } = useAuth(),
  { show } = useToast(),
  { start, openResult } = useWorkspace()
const group = ref(props.type === 'practice' ? 'doc-hieu' : 'vao-10'),
  editing = ref(false),
  edit = ref<Exam>(),
  deleting = ref<Exam | null>(null),
  assigning = ref<Exam | null>(null),
  rubricExam = ref<Exam | null>(null)
const table = computed(() => (props.type === 'practice' ? 'practice_exams' : 'mock_exams'))
const exams = computed(() => data.value[table.value].filter((e) => e.targetGroup === group.value))
async function save(exam: Exam) {
  try {
    requireTeacher()
    if (isApiEnabled()) {
      if (edit.value) await updateRemoteExam(exam, props.type)
      else await createRemoteExam(exam, props.type)
    } else upsert(table.value, exam)
    group.value = exam.targetGroup
    editing.value = false
    show('Đã lưu đề thành công! 🌻')
  } catch (e) {
    show((e as Error).message)
  }
}
async function destroy() {
  try {
    requireTeacher()
    if (deleting.value) {
      if (isApiEnabled()) await deleteRemoteExam(deleting.value.id, props.type)
      else {
        remove(table.value, deleting.value.id)
        set(
          'assignments',
          data.value.assignments.filter(
            (a) => !(a.examId === deleting.value!.id && a.examType === props.type),
          ),
        )
      }
    }
    deleting.value = null
  } catch (e) {
    show((e as Error).message)
  }
}
function openEditor(exam?: Exam) {
  edit.value = exam
  editing.value = true
}
</script>
<template>
  <section class="panel">
    <div class="flex justify-between items-center mb-3">
      <h2 class="section-title" style="margin: 0">
        {{ type === 'practice' ? '🌸 Góc Luyện Tập' : '🍁 Góc Thi Thử' }}
      </h2>
      <button v-if="isTeacher" class="btn btn-primary" @click="openEditor()">＋ Thêm đề mới</button>
    </div>
    <CategoryTabs v-model="group" :items="type === 'practice' ? practiceGroups : mockGroups" />
    <div class="grid">
      <ExamCard
        v-for="exam in exams"
        :key="exam.id"
        :exam="exam"
        :type="type"
        :teacher="isTeacher"
        :results="
          data.results.filter(
            (r) =>
              r.examId === exam.id &&
              r.examType === type &&
              (isTeacher || r.studentId === user?.id),
          )
        "
        @start="start(type, exam)"
        @edit="openEditor(exam)"
        @remove="deleting = exam"
        @assign="assigning = exam"
        @review="openResult($event)"
        @grade="openResult($event, true)"
        @rubric="rubricExam = exam"
      />
      <p v-if="!exams.length" class="empty-state">Chưa có đề nào trong mục này.</p>
    </div>
    <ExamEditor
      v-if="editing && isTeacher"
      :type="type"
      :exam="edit"
      :group="group"
      @save="save"
      @close="editing = false"
    />
    <ConfirmDialog
      v-if="deleting"
      message="Xóa đề này và thông báo giao đề liên quan?"
      @close="deleting = null"
      @confirm="destroy"
    />
    <AssignExamModal
      v-if="assigning && isTeacher"
      :exam="assigning"
      :type="type"
      @close="assigning = null"
    />
    <ExamRubricPanel
      v-if="rubricExam && isTeacher"
      :exam="rubricExam"
      :type="type"
      @close="rubricExam = null"
    />
  </section>
</template>
