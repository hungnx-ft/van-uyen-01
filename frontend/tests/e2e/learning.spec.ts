import { test, expect } from '@playwright/test'
import * as XLSX from 'xlsx'

test('teacher creates and assigns an exam, student submits, teacher grades', async ({ page }) => {
  const errors: string[] = []
  page.on('pageerror', (e) => errors.push(e.message))
  await page.goto('/login')
  await page.getByLabel('👤 Tên đăng nhập').fill('hathanhhangc2yenphong@bacninh.edu.vn')
  await page.getByLabel('🔒 Mật khẩu').fill('Thanhhang97@')
  await page.getByRole('button', { name: 'Đăng nhập hệ thống' }).click()
  await page.getByRole('link', { name: 'Góc quản lý' }).click()
  await page.getByLabel('Tên lớp (VD: 9A1)').fill('9A1')
  await page.getByRole('button', { name: 'Tạo Lớp', exact: true }).click()
  const workbook = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(
    workbook,
    XLSX.utils.aoa_to_sheet([['Họ tên'], ['Học Sinh Kiểm Thử']]),
    'Lớp',
  )
  await page.getByLabel('Tải lên File Excel').setInputFiles({
    name: 'students.xlsx',
    mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    buffer: XLSX.write(workbook, { type: 'buffer', bookType: 'xlsx' }),
  })
  await page.getByRole('button', { name: 'Tạo Tài Khoản Nhanh' }).click()
  const row = page.getByRole('row').filter({ hasText: 'Học Sinh Kiểm Thử' })
  await expect(row).toBeVisible()
  const studentId = await row.getByRole('cell').nth(2).innerText()
  await page.getByRole('link', { name: 'Góc luyện tập' }).click()
  await page.getByRole('button', { name: 'Viết đoạn văn (35p)', exact: false }).click()
  await page.getByRole('button', { name: 'Thêm đề mới' }).click()
  const editor = page.getByRole('dialog')
  await editor.getByLabel('Tên đề', { exact: true }).fill('Lòng biết ơn')
  await editor.getByLabel('Đề bài (Yêu cầu viết)').fill('Viết một đoạn văn về lòng biết ơn.')
  await editor
    .getByLabel('Đáp án chuẩn / Hướng dẫn chấm')
    .fill('Nêu ý nghĩa, dẫn chứng và bài học.')
  await editor.getByRole('button', { name: 'Lưu Đề', exact: true }).click()
  const card = page.locator('.floating-doc').filter({ hasText: 'Lòng biết ơn' })
  await expect(card).toBeVisible()
  await card.getByRole('button', { name: 'Thao tác đề' }).click()
  await card.getByRole('button', { name: 'Giao đề', exact: true }).click()
  await page.getByRole('dialog').getByRole('button', { name: 'Giao Đề ✅' }).click()
  await page.getByRole('button', { name: 'Hà Thanh Hằng', exact: false }).click()
  await page.getByRole('button', { name: 'Đăng xuất', exact: true }).click()
  await page.getByLabel('👤 Tên đăng nhập').fill(studentId)
  await page.getByLabel('🔒 Mật khẩu').fill('demo@123')
  await page.getByRole('button', { name: 'Đăng nhập hệ thống' }).click()
  await page.getByRole('button', { name: 'Thông báo', exact: true }).click()
  await page.getByRole('button', { name: 'Cô Hằng vừa giao đề mới:' }).click()
  const workspace = page.getByRole('dialog')
  await workspace.getByRole('textbox').fill('Lòng biết ơn giúp ta trân trọng những điều tốt đẹp.')
  await workspace.getByRole('button', { name: 'Nộp bài', exact: true }).click()
  await page
    .getByRole('dialog', { name: 'Xác nhận', exact: true })
    .getByRole('button', { name: 'Xác nhận', exact: true })
    .click()
  await page.getByLabel('Tự chấm Yêu cầu:').selectOption('1.75')
  await page.getByRole('button', { name: 'Lưu Điểm', exact: true }).click()
  await page.getByRole('link', { name: 'Góc học tập' }).click()
  await expect(page.getByRole('row').filter({ hasText: 'Lòng biết ơn' })).toContainText('Chờ chấm')
  await page.getByRole('button', { name: 'Học Sinh Kiểm Thử', exact: false }).click()
  await page.getByRole('button', { name: 'Đăng xuất', exact: true }).click()
  await page.getByLabel('👤 Tên đăng nhập').fill('hathanhhangc2yenphong@bacninh.edu.vn')
  await page.getByLabel('🔒 Mật khẩu').fill('Thanhhang97@')
  await page.getByRole('button', { name: 'Đăng nhập hệ thống' }).click()
  await page.getByRole('link', { name: 'Góc luyện tập' }).click()
  await page.getByRole('button', { name: 'Viết đoạn văn (35p)', exact: false }).click()
  await page.getByRole('button', { name: 'Chấm ngay' }).click()
  await page.getByLabel('Cô chấm Yêu cầu:').selectOption('2')
  await page.getByLabel('Lời phê tổng hợp').fill('Bài viết tốt!')
  await page.getByRole('button', { name: 'Xác nhận Điểm', exact: true }).click()
  await expect(page.getByText('Không có bài chờ chấm')).toBeVisible()
  await page.reload()
  await expect(page.getByRole('link', { name: 'Góc quản lý' })).toBeVisible()
  await page.getByRole('button', { name: 'Viết đoạn văn (35p)', exact: false }).click()
  await expect(page.getByRole('heading', { name: 'Lòng biết ơn' })).toBeVisible()
  await page.screenshot({
    path: 'test-results/desktop.png',
    fullPage: true,
    animations: 'disabled',
  })
  expect(errors).toEqual([])
})

test('mobile registration, theory reader and route protection', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/register')
  await page.getByLabel('👤 Tên đăng nhập').fill('mobile-student')
  await page.getByLabel('🔒 Mật khẩu').fill('test-password')
  await page.getByLabel('Họ và tên đầy đủ').fill('Học sinh tự do')
  await page.getByRole('button', { name: 'Tạo tài khoản' }).click()
  await page.getByRole('button', { name: 'Mở menu' }).click()
  await page.getByRole('link', { name: 'Góc kiến thức' }).click()
  await page.getByRole('heading', { name: 'Tri thức Thơ', exact: true }).click()
  await expect(page.getByRole('dialog', { name: 'Tri thức Thơ' })).toContainText(
    'Thơ dùng ngôn ngữ cô đọng',
  )
  await page.getByRole('dialog').getByRole('button', { name: 'Đóng', exact: true }).click()
  await page.screenshot({ path: 'test-results/mobile.png', fullPage: true, animations: 'disabled' })
  await page.goto('/manage')
  await expect(page).toHaveURL(/\/$/)
  await expect(
    page.getByRole('heading', { name: 'Chào mừng tới Khu Vườn Văn Chương' }),
  ).toBeVisible()
})

test('mock exam submits once at the deadline and retains all seven answers', async ({ page }) => {
  await page.goto('/login')
  await page.getByLabel('👤 Tên đăng nhập').fill('hathanhhangc2yenphong@bacninh.edu.vn')
  await page.getByLabel('🔒 Mật khẩu').fill('Thanhhang97@')
  await page.getByRole('button', { name: 'Đăng nhập hệ thống' }).click()
  await page.getByRole('link', { name: 'Góc thi thử' }).click()
  await page.getByRole('button', { name: 'Thêm đề mới' }).click()
  const editor = page.getByRole('dialog')
  await editor.getByLabel('Tên đề', { exact: true }).fill('Thi thử tự nộp')
  await editor.getByLabel('Ngữ liệu đọc hiểu').fill('Một ngữ liệu đọc hiểu.')
  for (let i = 0; i < 7; i++) {
    await editor
      .getByLabel('Câu hỏi', { exact: true })
      .nth(i)
      .fill(`Câu hỏi ${i + 1}`)
    await editor
      .getByLabel('Đáp án chuẩn / Hướng dẫn chấm')
      .nth(i)
      .fill(`Đáp án ${i + 1}`)
  }
  await editor.getByRole('button', { name: 'Lưu Đề', exact: true }).click()
  await page.getByRole('button', { name: 'Hà Thanh Hằng', exact: false }).click()
  await page.getByRole('button', { name: 'Đăng xuất', exact: true }).click()
  await page.getByRole('link', { name: 'Đăng ký tài khoản tự do' }).click()
  await expect(page.getByRole('heading', { name: 'Đăng ký Tài khoản Tự do' })).toBeVisible()
  await page.getByLabel('👤 Tên đăng nhập').fill('mock-student')
  await page.getByLabel('🔒 Mật khẩu').fill('test-password')
  await page.getByLabel('Họ và tên đầy đủ').fill('Học sinh thi thử')
  await page.getByRole('button', { name: 'Tạo tài khoản' }).click()
  await page.getByRole('link', { name: 'Góc thi thử' }).click()
  await page.clock.install()
  await page.getByRole('button', { name: 'Thi Ngay' }).click()
  const workspace = page.getByRole('dialog')
  await expect(workspace.getByRole('textbox')).toHaveCount(7)
  for (let i = 0; i < 7; i++)
    await workspace
      .getByRole('textbox')
      .nth(i)
      .fill(`Bài làm ${i + 1}`)
  await page.clock.fastForward(120 * 60 * 1000 + 1000)
  await expect(page.getByRole('dialog')).toHaveCount(0)
  await page.getByRole('link', { name: 'Góc học tập' }).click()
  await expect(page.getByRole('row').filter({ hasText: 'Thi thử tự nộp' })).toHaveCount(1)
  await page.getByRole('button', { name: 'Xem bài' }).click()
  await expect(page.getByRole('dialog')).toContainText('Bài làm 7')
  await page.getByRole('dialog').getByRole('button', { name: 'Đóng', exact: true }).click()
  await page.reload()
  await expect(page.getByRole('row').filter({ hasText: 'Thi thử tự nộp' })).toHaveCount(1)
})
