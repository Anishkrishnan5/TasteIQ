import { expect, test } from '@playwright/test'

test('searches with nutrition filters and renders grounded API results', async ({ page }) => {
  await page.goto('/')

  await page.getByLabel('Describe your meal').fill('chiken')
  await page.getByLabel('Maximum calories').fill('650')
  await page.getByLabel('Minimum protein').fill('20')

  const [response] = await Promise.all([
    page.waitForResponse(
      (candidate) =>
        candidate.url().endsWith('/api/recommendations') && candidate.request().method() === 'POST',
    ),
    page.getByRole('button', { name: 'Find my meal →' }).click(),
  ])

  expect(response.ok()).toBeTruthy()
  const payload = await response.json()
  expect(payload.meta.query_corrections).toEqual(['chiken->chicken'])
  expect(payload.meta.filters).toMatchObject({ max_calories: 650, min_protein: 20 })
  expect(payload.results.length).toBeGreaterThan(0)
  expect(
    payload.results.every(
      (item) => item.calories != null && item.calories <= 650 && item.protein_g >= 20,
    ),
  ).toBeTruthy()

  await expect(page.getByRole('heading', { name: 'Matches for you' })).toBeVisible()
  await expect(page.locator('.grid article')).toHaveCount(payload.results.length)
  await expect(page.locator('.grid article').first().getByRole('heading')).toHaveText(
    payload.results[0].name,
  )
})
