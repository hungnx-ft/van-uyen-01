import { expect, test } from '@playwright/test'

test('registering through the backend establishes an authenticated session', async ({ page }) => {
  await page.goto('/register')
  await page.getByLabel('👤 Tên đăng nhập').fill(`api-student-${Date.now()}`)
  await page.getByLabel('🔒 Mật khẩu').fill('test-password')
  await page.getByLabel('Họ và tên đầy đủ').fill('Học sinh API')
  await page.getByRole('button', { name: 'Tạo tài khoản' }).click()
  await expect(page).toHaveURL(/\/$/)
  await expect(page.getByRole('link', { name: 'Góc thi thử' })).toBeVisible()
  await expect(page.getByRole('button', { name: /Học sinh API/ })).toBeVisible()
  expect(await page.evaluate(() => Boolean(sessionStorage.getItem('vu_api_access_token')))).toBe(
    true,
  )
})
