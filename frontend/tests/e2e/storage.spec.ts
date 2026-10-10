import { test, expect } from '@playwright/test'
import { readFile } from 'node:fs/promises'

test('storage error preserves raw data, offers a backup and recovers after retry', async ({
  page,
}) => {
  await page.addInitScript(() => localStorage.setItem('vu_results', '{invalid JSON'))
  await page.goto('/')
  await expect(page.getByRole('alert')).toContainText('results')
  await expect(page.getByRole('heading', { name: 'Chưa thể mở dữ liệu' })).toBeVisible()
  const downloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Tải bản sao dữ liệu gốc' }).click()
  const download = await downloadPromise
  const backup = JSON.parse(await readFile((await download.path())!, 'utf8'))
  expect(backup.entries.vu_results).toBe('{invalid JSON')
  expect(backup.entries.vu_users).toBeNull()
  await page.evaluate(() => localStorage.setItem('vu_results', '[]'))
  await page.getByRole('button', { name: 'Thử lại' }).click()
  await expect(page.getByRole('button', { name: 'Đăng nhập hệ thống' })).toBeVisible()
  await expect(page.getByRole('alert')).toHaveCount(0)
})

test('legacy sessions resolve current roles and class changes sync across tabs', async ({
  page,
  context,
}) => {
  const errors: string[] = []
  page.on('pageerror', (error) => errors.push(error.message))
  await page.addInitScript(() => {
    if (sessionStorage.getItem('fixture-loaded')) return
    const student = {
      id: 'student',
      password: 'old',
      role: 'student',
      fullName: 'Học sinh cũ',
      classId: 'a',
      className: '9A',
      isClassStudent: true,
    }
    localStorage.setItem(
      'vu_users',
      JSON.stringify([
        student,
        { id: 'teacher', password: 'teacher-password', role: 'teacher', fullName: 'Giáo viên' },
      ]),
    )
    localStorage.setItem(
      'vu_classes',
      JSON.stringify([
        { id: 'a', name: '9A', year: '2026' },
        { id: 'b', name: '9B', year: '2026' },
      ]),
    )
    sessionStorage.setItem('vu_current_user', JSON.stringify({ ...student, role: 'teacher' }))
    sessionStorage.setItem('fixture-loaded', '1')
  })
  await page.goto('/study')
  await expect(page.getByRole('link', { name: 'Góc học tập' })).toBeVisible()
  await expect(page.getByRole('link', { name: 'Góc quản lý' })).toHaveCount(0)
  expect(await page.evaluate(() => JSON.parse(sessionStorage.getItem('vu_current_user')!))).toEqual(
    { id: 'student' },
  )

  const teacherPage = await context.newPage()
  await teacherPage.goto('/login')
  await teacherPage.getByLabel('👤 Tên đăng nhập').fill('teacher')
  await teacherPage.getByLabel('🔒 Mật khẩu').fill('teacher-password')
  await teacherPage.getByRole('button', { name: 'Đăng nhập hệ thống' }).click()
  await teacherPage.getByRole('link', { name: 'Góc quản lý' }).click()
  const row = teacherPage.getByRole('row').filter({ hasText: 'Học sinh cũ' })
  await row.getByTitle('Chuyển lớp').click()
  await teacherPage.getByRole('dialog').getByLabel('Lớp mới').selectOption('b')
  await teacherPage.getByRole('dialog').getByRole('button', { name: 'Lưu', exact: true }).click()
  await expect(page.locator('.sidebar-user-role')).toContainText('9B')
  await row.getByTitle('Đặt lại mật khẩu').click()
  await teacherPage.getByRole('dialog').getByLabel('Mật khẩu mới').fill('reset-password')
  await teacherPage.getByRole('dialog').getByRole('button', { name: 'Lưu', exact: true }).click()
  await page.getByRole('button', { name: 'Học sinh cũ', exact: false }).click()
  await page.getByLabel('Mật khẩu cũ').fill('reset-password')
  await page.getByLabel('Mật khẩu mới').fill('changed-password')
  await page.getByRole('button', { name: 'Đổi Mật Khẩu', exact: true }).click()
  await expect(row).toContainText('changed-password')
  await page.reload()
  await expect(page.locator('.sidebar-user-role')).toContainText('9B')

  await row.getByTitle('Xóa tài khoản').click()
  await teacherPage
    .getByRole('dialog')
    .getByRole('button', { name: 'Xác nhận', exact: true })
    .click()
  await expect(page.getByRole('button', { name: 'Đăng nhập hệ thống' })).toBeVisible()
  expect(await page.evaluate(() => sessionStorage.getItem('vu_current_user'))).toBeNull()
  expect(errors).toEqual([])
})
