import type { User } from '~/types'
export function useExcel() {
  async function readNames(file: File) {
    const XLSX = await import('xlsx')
    const workbook = XLSX.read(await file.arrayBuffer(), { type: 'array' })
    const sheet = workbook.Sheets[workbook.SheetNames[0] || '']
    if (!sheet) throw new Error('File Excel không có trang tính.')
    return XLSX.utils
      .sheet_to_json<unknown[]>(sheet, { header: 1 })
      .map((row) => String(row[0] ?? '').trim())
      .filter(
        (name) => name && !['họ tên', 'họ và tên', 'tên', 'full name'].includes(name.toLowerCase()),
      )
  }
  async function exportAccounts(users: User[]) {
    const XLSX = await import('xlsx')
    const sheet = XLSX.utils.json_to_sheet(
      users.map((u, i) => ({
        STT: i + 1,
        'Họ Tên': u.fullName,
        Lớp: u.className,
        'Tài Khoản': u.id,
        'Mật Khẩu': u.password,
      })),
    )
    const book = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(book, sheet, 'Tài khoản')
    XLSX.writeFile(book, 'tai-khoan-van-uyen.xlsx')
  }
  return { readNames, exportAccounts }
}
