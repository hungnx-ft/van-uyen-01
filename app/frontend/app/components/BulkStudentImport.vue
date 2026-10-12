<script setup lang="ts">
import * as XLSX from 'xlsx'
import { isApiEnabled } from '~/utils/api'

interface ImportRow {
  row: number
  fullName: string
  username: string
  password: string
  schoolName: string
  className: string
  classYear: string
  error?: string
}

const { data, set, createRemoteClass, createRemoteStudentsBulk } = useDatabase()
const { requireTeacher } = useAuth()
const { show } = useToast()
const defaultYear = ref('2025-2026')
const rows = ref<ImportRow[]>([])
const fileName = ref('')
const busy = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)
const createdCredentials = ref<Array<{ fullName: string; username: string; password: string }>>([])

function clean(value: unknown) {
  return String(value ?? '').trim()
}

function headerKey(value: unknown) {
  return clean(value)
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[ _-]+/g, '')
}

function pick(row: Record<string, unknown>, names: string[]) {
  const entries = Object.entries(row)
  const found = entries.find(([key]) => names.includes(headerKey(key)))
  return found ? clean(found[1]) : ''
}

function makeUsername(fullName: string, index: number, used: Set<string>) {
  const base =
    fullName
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '_')
      .replace(/^_+|_+$/g, '') || 'hoc_sinh'
  let candidate = `hs_${base}_${index}`
  let suffix = 1
  while (used.has(candidate)) candidate = `hs_${base}_${index}_${suffix++}`
  return candidate
}

function makePassword(index: number) {
  const bytes = new Uint8Array(9)
  crypto.getRandomValues(bytes)
  return `VuYen${index}${Array.from(bytes, (byte) => byte.toString(36))
    .join('')
    .slice(0, 8)}`
}

async function readFile(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  fileName.value = file.name
  try {
    const workbook = XLSX.read(await file.arrayBuffer(), { type: 'array' })
    const sheet = workbook.Sheets[workbook.SheetNames[0] || '']
    if (!sheet) throw new Error('File Excel không có sheet dữ liệu.')
    const source = XLSX.utils.sheet_to_json<Record<string, unknown>>(sheet, { defval: '' })
    const used = new Set(data.value.users.map((user) => user.username || user.id))
    rows.value = source.map((item, index) => {
      const fullName = pick(item, ['hoten', 'hovaten', 'fullname', 'name'])
      const suppliedUsername = pick(item, ['username', 'taikhoan', 'tendangnhap'])
      const username = suppliedUsername || makeUsername(fullName, index + 1, used)
      used.add(username)
      const password = pick(item, ['password', 'matkhau']) || makePassword(index + 1)
      const className = pick(item, ['class', 'lop', 'tenlop', 'classname'])
      const classYear =
        pick(item, ['khoa', 'nienkhoa', 'year', 'namhoc', 'schoolyear']) || defaultYear.value
      return {
        row: index + 2,
        fullName,
        username,
        password,
        schoolName: pick(item, ['school', 'truong', 'schoolname']),
        className,
        classYear,
        error: !fullName ? 'Thiếu họ và tên' : !className ? 'Thiếu lớp' : undefined,
      }
    })
    if (!rows.value.length) throw new Error('Sheet không có dòng học sinh.')
  } catch (error) {
    rows.value = []
    show((error as Error).message)
  } finally {
    if (fileInput.value) fileInput.value.value = ''
  }
}

function downloadTemplate() {
  const sheet = XLSX.utils.aoa_to_sheet([
    ['Họ và tên', 'Tên đăng nhập', 'Mật khẩu', 'Trường', 'Lớp', 'Khóa'],
    ['Nguyễn Văn A', '', '', 'THCS ...', '6A1', '2025-2026'],
  ])
  const workbook = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(workbook, sheet, 'HocSinh')
  XLSX.writeFile(workbook, 'mau-tao-tai-khoan-hoc-sinh.xlsx')
}

async function submit() {
  if (busy.value) return
  const valid = rows.value.filter((row) => !row.error)
  if (!valid.length) return show('Chưa có học sinh hợp lệ để tạo.')
  busy.value = true
  try {
    requireTeacher()
    const classMap = new Map<string, { id: string; name: string; year: string }>()
    const groups = new Map<string, ImportRow[]>()
    for (const row of valid) {
      if (!/^\d{4}-\d{4}$/.test(row.classYear)) {
        row.error = 'Niên khóa phải có dạng YYYY-YYYY'
        continue
      }
      const key = `${row.className.toLowerCase()}|${row.classYear}`
      groups.set(key, [...(groups.get(key) || []), row])
    }
    for (const [key, group] of groups) {
      const sample = group[0]!
      const existing = data.value.classes.find(
        (item) =>
          item.name.toLowerCase() === sample.className.toLowerCase() &&
          item.year === sample.classYear,
      )
      if (existing) classMap.set(key, existing)
      else if (isApiEnabled())
        classMap.set(key, await createRemoteClass(sample.className, sample.classYear))
      else {
        const created = { id: crypto.randomUUID(), name: sample.className, year: sample.classYear }
        set('classes', [...data.value.classes, created])
        classMap.set(key, created)
      }
    }
    if (isApiEnabled()) {
      const created: Array<{ fullName: string; username: string; password: string }> = []
      const failed: ImportRow[] = []
      for (const [key, classRows] of groups) {
        const classroom = classMap.get(key)!
        const result = await createRemoteStudentsBulk(
          classroom.id,
          classRows.map((row) => ({
            username: row.username,
            password: row.password,
            fullName: row.fullName,
            schoolName: row.schoolName,
          })),
        )
        created.push(
          ...result.created.map((student) => ({
            fullName: student.fullName,
            username: student.username || student.id,
            password: student.password,
          })),
        )
        failed.push(
          ...result.failed.map((failure) => {
            const original = classRows.find((row) => row.username === failure.username)
            return {
              row: original?.row || failure.row,
              fullName: original?.fullName || '',
              username: failure.username || '',
              password: '',
              schoolName: original?.schoolName || '',
              className: original?.className || '',
              classYear: original?.classYear || '',
              error: failure.detail,
            }
          }),
        )
      }
      show(`Đã tạo ${created.length} tài khoản; lỗi ${failed.length} dòng.`)
      createdCredentials.value = created
      rows.value = failed
    } else {
      const existing = new Set(data.value.users.map((user) => user.username || user.id))
      const duplicate = valid.find((row) => existing.has(row.username))
      if (duplicate) throw new Error(`Tên đăng nhập đã tồn tại: ${duplicate.username}`)
      set('users', [
        ...data.value.users,
        ...valid.map((row) => ({
          ...(() => {
            const classroom = classMap.get(`${row.className.toLowerCase()}|${row.classYear}`)!
            return { classId: classroom.id, className: classroom.name }
          })(),
          id: row.username,
          username: row.username,
          password: row.password,
          role: 'student' as const,
          fullName: row.fullName,
          schoolName: row.schoolName || undefined,
          isClassStudent: true,
        })),
      ])
      createdCredentials.value = valid.map((row) => ({
        fullName: row.fullName,
        username: row.username,
        password: row.password,
      }))
      show(`Đã tạo ${valid.length} tài khoản.`)
      rows.value = []
    }
  } catch (error) {
    show((error as Error).message)
  } finally {
    busy.value = false
  }
}

function downloadCredentials() {
  const content = [
    'Họ tên\tTài khoản\tMật khẩu',
    ...createdCredentials.value.map(
      (item) => `${item.fullName}\t${item.username}\t${item.password}`,
    ),
  ].join('\n')
  const url = URL.createObjectURL(new Blob([content], { type: 'text/plain;charset=utf-8' }))
  const link = document.createElement('a')
  link.href = url
  link.download = 'tai-khoan-hoc-sinh.txt'
  link.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <div class="bulk-student-import">
    <h3 class="font-heading mb-3 text-primary">📊 Tạo tài khoản từ Excel</h3>
    <p class="text-light mb-3">
      Cột bắt buộc: Họ và tên, Lớp. Tài khoản và mật khẩu sẽ tự tạo nếu để trống.
    </p>
    <div class="input-group">
      <label>
        Niên khóa mặc định (khi cột Khóa để trống)
        <input v-model="defaultYear" class="input-control" pattern="\\d{4}-\\d{4}" required />
      </label>
    </div>
    <div class="flex gap-2 mb-3" style="flex-wrap: wrap">
      <button type="button" class="btn btn-secondary" @click="downloadTemplate">
        Tải file mẫu
      </button>
      <button type="button" class="btn btn-outline" @click="fileInput?.click()">
        Chọn file Excel
      </button>
      <input ref="fileInput" type="file" accept=".xlsx,.xls,.csv" hidden @change="readFile" />
    </div>
    <p v-if="fileName" class="text-light">{{ fileName }} · {{ rows.length }} dòng</p>
    <div v-if="rows.length" style="overflow-x: auto; max-height: 280px" class="mb-3">
      <table class="leaderboard-table" style="font-size: 0.85rem">
        <thead>
          <tr>
            <th>Dòng</th>
            <th>Họ tên</th>
            <th>Tài khoản</th>
            <th>Mật khẩu</th>
            <th>Lớp</th>
            <th>Niên khóa</th>
            <th>Trạng thái</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in rows" :key="row.row">
            <td>{{ row.row }}</td>
            <td>{{ row.fullName || '—' }}</td>
            <td>{{ row.username || '—' }}</td>
            <td>{{ row.password || '—' }}</td>
            <td>{{ row.className || '—' }}</td>
            <td>{{ row.classYear || '—' }}</td>
            <td>{{ row.error || 'Sẵn sàng' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <button
      v-if="rows.length"
      type="button"
      class="btn btn-primary w-full"
      :disabled="busy"
      @click="submit"
    >
      Tạo {{ rows.filter((row) => !row.error).length }} tài khoản
    </button>
    <button
      v-if="createdCredentials.length"
      type="button"
      class="btn btn-secondary w-full mt-2"
      @click="downloadCredentials"
    >
      Tải danh sách tài khoản đã tạo
    </button>
  </div>
</template>
