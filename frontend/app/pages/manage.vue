<script setup lang="ts">
import type { User, Result } from '~/types'
import { isApiEnabled } from '~/utils/api'
const { data, remove, set, deleteRemoteStudent, setRemoteStudentStatus } = useDatabase(),
  { isTeacher, requireTeacher, logout } = useAuth(),
  { show } = useToast(),
  { openResult } = useWorkspace()
const filter = ref('all'),
  activeMenu = ref('students'),
  editing = ref<{ student: User; mode: 'reset' | 'move' } | null>(null),
  deleting = ref<User | null>(null),
  viewing = ref<User | null>(null)
const students = computed(() =>
  data.value.users.filter(
    (u) =>
      u.role === 'student' &&
      (filter.value === 'all' ||
        (filter.value === 'free_class' ? !u.classId : u.classId === filter.value)),
  ),
)
const results = computed(() =>
  data.value.results
    .filter((r) => r.studentId === viewing.value?.id)
    .sort((a, b) => b.submittedAt - a.submittedAt),
)
async function destroy() {
  try {
    requireTeacher()
    if (deleting.value) {
      if (isApiEnabled()) await deleteRemoteStudent(deleting.value.id)
      else {
        remove('users', deleting.value.id)
        set(
          'results',
          data.value.results.filter((r) => r.studentId !== deleting.value!.id),
        )
      }
    }
    deleting.value = null
    show('Đã xóa tài khoản.')
  } catch (e) {
    show((e as Error).message)
  }
}
async function toggleStatus(student: User) {
  try {
    requireTeacher()
    const active = student.isActive === false
    if (isApiEnabled()) await setRemoteStudentStatus(student.id, active)
    else
      set(
        'users',
        data.value.users.map((item) =>
          item.id === student.id ? { ...item, isActive: active } : item,
        ),
      )
    show(active ? 'Đã mở khóa tài khoản.' : 'Đã khóa tài khoản.')
  } catch (error) {
    show((error as Error).message)
  }
}
function viewResult(result: Result, grade = false) {
  viewing.value = null
  openResult(result, grade)
}
const managementMenus = [
  { id: 'students', label: '👥 Học sinh' },
  { id: 'accounts', label: '➕ Tạo tài khoản' },
  { id: 'classes', label: '🏫 Lớp học' },
  { id: 'ai', label: '🤖 Cài đặt AI' },
]
</script>
<template>
  <section v-if="isTeacher" class="panel">
    <div class="flex justify-between items-center mb-3">
      <h2 class="section-title" style="margin: 0">🍀 Góc Quản Lý & Cài Đặt</h2>
      <button class="btn btn-danger" @click="logout">Đăng xuất</button>
    </div>
    <CategoryTabs v-model="activeMenu" :items="managementMenus" />

    <div v-if="activeMenu === 'students'" class="card mt-3">
      <div class="flex justify-between items-center mb-3" style="flex-wrap: wrap; gap: 12px">
        <h3 class="font-heading text-primary">Danh Sách Học Sinh</h3>
        <select v-model="filter" class="input-control" style="width: 200px" aria-label="Lọc lớp">
          <option value="all">-- Tất cả Học sinh --</option>
          <option value="free_class">Lớp Tự do</option>
          <option v-for="c in data.classes" :key="c.id" :value="c.id">
            {{ c.name }} ({{ c.year }})
          </option>
        </select>
      </div>
      <StudentTable
        :students="students"
        @reset="editing = { student: $event, mode: 'reset' }"
        @move="editing = { student: $event, mode: 'move' }"
        @remove="deleting = $event"
        @toggle="toggleStatus"
        @grade="viewing = $event"
      />
    </div>

    <div v-else-if="activeMenu === 'accounts'" class="card mt-3">
      <h3 class="font-heading text-primary mb-3">Tạo tài khoản học sinh</h3>
      <p class="text-light mb-3">Tạo từng tài khoản hoặc nhập nhiều học sinh từ file Excel.</p>
      <div class="flex gap-4" style="flex-wrap: wrap">
        <div style="flex: 1; min-width: min(300px, 100%)"><StudentCreateForm /></div>
        <div style="flex: 2; min-width: min(300px, 100%)"><BulkStudentImport /></div>
      </div>
    </div>

    <div v-else-if="activeMenu === 'classes'" class="card mt-3">
      <h3 class="font-heading text-primary mb-3">Quản lý lớp học</h3>
      <ClassCreateForm />
    </div>

    <div v-else class="card mt-3">
      <h3 class="font-heading text-primary mb-3">Cài đặt AI</h3>
      <AISettingsPanel />
    </div>
    <StudentEditModal
      v-if="editing"
      :student="editing.student"
      :mode="editing.mode"
      @close="editing = null"
    />
    <ConfirmDialog
      v-if="deleting"
      :message="`Xóa tài khoản ${deleting.fullName} và các bài làm của học sinh này?`"
      @close="deleting = null"
      @confirm="destroy"
    />
    <BaseModal v-if="viewing" :title="`Bài làm: ${viewing.fullName}`" @close="viewing = null">
      <div class="modal-content">
        <ResultHistory
          :results="results"
          teacher
          @review="viewResult($event)"
          @grade="viewResult($event, true)"
        />
      </div>
    </BaseModal>
  </section>
</template>
