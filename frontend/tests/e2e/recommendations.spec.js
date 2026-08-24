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

test('creates a profile, personalizes results, and saves a meal', async ({ page }) => {
  await page.goto('/')

  await page.getByLabel('Profile name').fill('Browser Demo')
  await page.getByLabel('Diet preferences').fill('high_protein')
  await page.getByRole('button', { name: 'Create profile' }).click()
  await expect(page.getByText('Personalization active')).toBeVisible()

  await page.getByLabel('Describe your meal').fill('chicken')
  await page.getByRole('button', { name: 'Find my meal →' }).click()

  await expect(page.locator('.match-reason').first()).toContainText('high_protein')
  const firstCard = page.locator('.grid article').first()
  await firstCard.getByRole('button', { name: 'Save', exact: true }).click()
  await expect(firstCard.getByRole('button', { name: 'Saved', exact: true })).toBeVisible()
})

test('answers conversationally with grounded menu citations', async ({ page }) => {
  await page.goto('/')

  await page.getByRole('textbox', { name: 'Ask TasteIQ' }).fill('What is a high protein chicken option?')
  await page.getByRole('button', { name: 'Send', exact: true }).click()

  await expect(page.locator('.chat-turn.assistant')).toBeVisible()
  await expect(page.getByLabel('Menu citations').first()).toBeVisible()
  await expect(page.getByText('Local grounded fallback').first()).toBeVisible()
})
