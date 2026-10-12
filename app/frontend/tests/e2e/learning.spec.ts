import { test, expect } from '@playwright/test'

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
  await page.goto('/manage')
  await expect(page).toHaveURL(/\/$/)
})

test('mock exam submits once at the deadline and retains all seven answers', async ({ page }) => {
  const studentUsername = `mock-student-${Date.now()}`
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
  await expect(page).toHaveURL(/\/login$/)
  await page.goto('/register')
  await page.getByLabel('👤 Tên đăng nhập').fill(studentUsername)
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
})
