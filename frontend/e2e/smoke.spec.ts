import { expect, test, type Page } from '@playwright/test'

const SIGNED_URL_PATH = '/api/anna/signed-url'
const FAB_NAME = /Porozmawiaj z Ann/
// Fake value: the widget never reaches a real ElevenLabs session in these tests.
const FAKE_SIGNED_URL = 'wss://signed-url.e2e.invalid/conversation?token=e2e-fake'

/** Records securitypolicyviolation events from the first moment of the document. */
async function recordCspViolations(page: Page) {
  await page.addInitScript(() => {
    const w = window as unknown as { __cspViolations: string[] }
    w.__cspViolations = []
    document.addEventListener('securitypolicyviolation', (event) => {
      w.__cspViolations.push(`${event.violatedDirective} -> ${event.blockedURI || 'inline'}`)
    })
  })
}

async function cspViolations(page: Page): Promise<string[]> {
  return page.evaluate(() => (window as unknown as { __cspViolations: string[] }).__cspViolations)
}

test.describe('smoke', () => {
  // Hermetic by default: no test may reach ElevenLabs, even if a hover or focus triggers the lazy fetch.
  // Tests that assert on the request register their own (later, therefore winning) route.
  test.beforeEach(async ({ page }) => {
    await page.route(`**${SIGNED_URL_PATH}*`, (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ signed_url: FAKE_SIGNED_URL, language: 'pl' }),
      }),
    )
  })

  test('home page loads in Polish with the Anna button', async ({ page }) => {
    await page.goto('/')

    await expect(page.locator('html')).toHaveAttribute('lang', 'pl')
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
    await expect(page.locator('#anna-floating-trigger')).toBeVisible()
    await expect(page.locator('#anna-floating-trigger')).toHaveAccessibleName(FAB_NAME)
  })

  test('clicking the Anna button requests a signed URL, and only then', async ({ page }) => {
    const signedUrlRequests: string[] = []
    page.on('request', (request) => {
      if (request.url().includes(SIGNED_URL_PATH)) signedUrlRequests.push(request.url())
    })
    await page.route(`**${SIGNED_URL_PATH}*`, (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ signed_url: FAKE_SIGNED_URL, language: 'pl' }),
      }),
    )

    await page.goto('/')
    // Lazy loading: nothing is requested on page load.
    await page.waitForLoadState('networkidle')
    expect(signedUrlRequests).toHaveLength(0)

    const request = page.waitForRequest((req) => req.url().includes(SIGNED_URL_PATH))
    await page.locator('#anna-floating-trigger').click()

    expect((await request).url()).toContain('lang=pl')
  })

  test('no Content-Security-Policy violations on the home page', async ({ page }) => {
    await recordCspViolations(page)

    await page.goto('/')
    await page.waitForLoadState('networkidle')

    expect(await cspViolations(page)).toEqual([])
  })

  test('the privacy policy is reachable from the footer, without CSP violations', async ({ page }) => {
    await recordCspViolations(page)
    await page.goto('/')

    await page.getByRole('contentinfo').getByRole('link', { name: 'Polityka prywatności' }).click()

    await expect(page).toHaveURL(/\/polityka$/)
    await expect(page.getByRole('heading', { level: 1 })).toHaveText('Polityka prywatności')
    await page.waitForLoadState('networkidle')
    expect(await cspViolations(page)).toEqual([])
  })
})
