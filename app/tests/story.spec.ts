import { expect, test } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

test('story renders, exposes keyboard tooltips, and expands methods', async ({ page }) => {
  const errors: string[] = []
  page.on('console', (message) => message.type() === 'error' && errors.push(message.text()))
  await page.goto('/')
  await expect(page).toHaveTitle(/Municipal overtime/)
  await expect(page.getByRole('heading', { level: 1 })).toContainText('Overtime’s share of pay fell')
  await expect(page.locator('.trend-chart svg')).toBeVisible({ timeout: 7_000 })

  const trendPoint = page.locator('.trend-point[aria-label^="Chicago, 2025"]')
  await trendPoint.focus()
  await expect(page.getByRole('tooltip')).toContainText('Total reported pay')
  await expect(page.getByRole('tooltip')).toContainText('Change vs 2024')
  await expect(page.getByRole('tooltip')).toContainText('Analyst-classified pay elements')

  const overtimeSegment = page.getByRole('button', { name: /Chicago, Overtime/ })
  await overtimeSegment.focus()
  await expect(page.getByRole('tooltip')).toContainText('Amount')
  await expect(page.getByRole('tooltip')).toContainText('$469.9M')

  const departmentMark = page.locator('.ranking').filter({ hasText: 'Chicago' }).getByRole('button', { name: /Chicago Police Department/ })
  await departmentMark.focus()
  await expect(page.getByRole('tooltip')).toContainText('Share of city overtime')
  await expect(page.getByRole('tooltip')).toContainText('Of department pay')

  await page.getByText('Methods, definitions, and sources').click()
  await expect(page.getByRole('heading', { name: 'How the comparison was built' })).toBeVisible()
  expect(errors).toEqual([])
  const accessibility = await new AxeBuilder({ page }).analyze()
  expect(accessibility.violations).toEqual([])
})

test('layout has no horizontal overflow', async ({ page }) => {
  await page.goto('/')
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)
  expect(overflow).toBeLessThanOrEqual(1)
})
