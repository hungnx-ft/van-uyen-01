<script setup lang="ts">
import type { User, Result } from '~/types'
import { isApiEnabled } from '~/utils/api'
const { data, remove, set, deleteRemoteStudent, setRemoteStudentStatus } = useDatabase(),
  { isTeacher, requireTeacher, logout } = useAuth(),
  { show } = useToast(),
  { openResult } = useWorkspace()
const filter = ref('all'),
  search = ref(''),
  activeMenu = ref('students'),
  editing = ref<{ student: User; mode: 'reset' | 'move' } | null>(null),
  deleting = ref<User | null>(null),
  viewing = ref<User | null>(null)
const students = computed(() =>
  data.value.users.filter(
    (u) =>
      u.role === 'student' &&
      (filter.value === 'all' ||
        (filter.value === 'free_class' ? !u.classId : u.classId === filter.value)) &&
      (() => {
        const q = search.value.trim().toLowerCase()
        if (!q) return true
        const code = u.studentCode || `hs-${String(u.id).replace(/\D/g, '').padStart(5, '0')}`
        return [code, u.fullName, u.username, u.id].some((value) =>
          String(value || '').toLowerCase().includes(q),
        )
      })(),
  ),
)
const results = computed(() =>
  data.value.results
    .filter((r) => r.studentId === viewing.value?.id)
    .sort((a, b) => b.submittedAt - a.submittedAt),
)
const studentStats = computed(() => {
  const items = results.value
  const graded = items.filter((r) => r.status === 'graded')
  const average = graded.length
    ? graded.reduce((sum, r) => sum + (r.teacherScore ?? r.selfScore ?? 0), 0) / graded.length
    : 0
  return { total: items.length, graded: graded.length, pending: items.length - graded.length, average }
})
const viewingClassYear = computed(() =>
  data.value.classes.find((c) => c.id === viewing.value?.classId)?.year || '—',
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
        <div class="flex gap-2" style="flex-wrap: wrap">
          <input v-model="search" class="input-control" style="width: 240px" placeholder="Tìm theo mã HS, tên hoặc tài khoản" aria-label="Tìm học sinh" />
          <select v-model="filter" class="input-control" style="width: 200px" aria-label="Lọc lớp">
          <option value="all">-- Tất cả Học sinh --</option>
          <option value="free_class">Lớp Tự do</option>
          <option v-for="c in data.classes" :key="c.id" :value="c.id">
            {{ c.name }} ({{ c.year }})
          </option>
          </select>
        </div>
      </div>
      <StudentTable
        :students="students"
        @reset="editing = { student: $event, mode: 'reset' }"
        @move="editing = { student: $event, mode: 'move' }"
        @remove="deleting = $event"
        @toggle="toggleStatus"
        @detail="viewing = $event"
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
    <BaseModal v-if="viewing" :title="`Hồ sơ học sinh: ${viewing.fullName}`" wide @close="viewing = null">
      <div class="modal-content">
        <div class="student-profile-head">
          <div>
            <h3 class="font-heading text-primary">{{ viewing.fullName }}</h3>
            <p class="text-light mb-0">Tài khoản: {{ viewing.username || viewing.id }}</p>
          </div>
          <span class="status-pill" :class="viewing.isActive === false ? 'status-locked' : 'status-active'">
            {{ viewing.isActive === false ? 'Đã khóa' : 'Đang hoạt động' }}
          </span>
        </div>
        <div class="student-info-grid mt-3">
          <div><small>Lớp</small><strong>{{ viewing.className || 'Tự do' }}</strong></div>
          <div><small>Niên khóa</small><strong>{{ viewingClassYear }}</strong></div>
          <div><small>Trường</small><strong>{{ viewing.schoolName || '—' }}</strong></div>
          <div><small>Bài đã nộp</small><strong>{{ studentStats.total }}</strong></div>
          <div><small>Đã chấm</small><strong>{{ studentStats.graded }}</strong></div>
          <div><small>Điểm trung bình</small><strong>{{ studentStats.graded ? studentStats.average.toFixed(2) : '—' }}</strong></div>
        </div>
        <h4 class="font-heading text-primary mt-4 mb-2">Quá trình học tập</h4>
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

<style scoped>
.student-profile-head { display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
.student-info-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }
.student-info-grid > div { padding: 12px; border: 1px solid var(--border-color); border-radius: var(--radius-md); background: #fffafe; }
.student-info-grid small, .student-info-grid strong { display: block; }
.student-info-grid small { color: var(--text-light); margin-bottom: 4px; }
.status-pill { padding: 6px 12px; border-radius: 999px; font-size: .85rem; font-weight: 600; }
.status-active { background: #dcfce7; color: #166534; }
.status-locked { background: #fee2e2; color: #991b1b; }
@media (max-width: 700px) { .student-info-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
</style>
