import { chromium } from 'playwright'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const ROOT = path.resolve(__dirname, '..')
const SCREENSHOTS_DIR = path.join(ROOT, 'qa-screenshots')

if (!fs.existsSync(SCREENSHOTS_DIR)) {
  fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true })
}

const BASE_URL = process.env.BASE_URL || 'http://localhost:5173'

const FORBIDDEN_STRINGS = [
  'Something went wrong',
  'No data returned',
  'Cannot read',
  'undefined',
  'NaN',
  'Mock data',
]

async function run() {
  console.log(`Starting smoke tests against ${BASE_URL}...`)
  const browser = await chromium.launch({ headless: true })
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
  })

  const results = []
  let fatalError = false

  async function testPage(name, urlPath, customActions = null) {
    const page = await context.newPage()
    const consoleErrors = []
    const failedRequests = []

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        const text = msg.text()
        // Ignore favicon or non-critical 404s if any
        consoleErrors.push(text)
      }
    })

    page.on('pageerror', (err) => {
      consoleErrors.push(err.message)
    })

    page.on('response', (res) => {
      if (res.status() >= 400) {
        failedRequests.push(`${res.status()} ${res.url()}`)
      }
    })

    try {
      console.log(`Testing ${name} (${urlPath})...`)
      await page.goto(`${BASE_URL}${urlPath}`, { waitUntil: 'networkidle', timeout: 30000 })
      await page.waitForTimeout(1000)

      if (customActions) {
        await customActions(page)
        await page.waitForTimeout(1000)
      }

      // Check forbidden text
      const bodyText = await page.innerText('body')
      const matchedForbidden = []
      for (const forbidden of FORBIDDEN_STRINGS) {
        if (bodyText.includes(forbidden)) {
          matchedForbidden.push(forbidden)
        }
      }

      const screenshotPath = path.join(SCREENSHOTS_DIR, `${name.toLowerCase().replace(/[^a-z0-9]/g, '-')}.png`)
      await page.screenshot({ path: screenshotPath, fullPage: true })

      const status = consoleErrors.length === 0 && failedRequests.length === 0 && matchedForbidden.length === 0 ? 'PASS' : 'WARN/FAIL'
      results.push({
        page: name,
        url: urlPath,
        status,
        screenshot: screenshotPath,
        consoleErrors,
        failedRequests,
        matchedForbidden,
      })
      console.log(`  ✓ ${name}: ${status}`)
    } catch (err) {
      console.error(`  ✗ ${name} failed:`, err.message)
      results.push({
        page: name,
        url: urlPath,
        status: 'FAIL',
        error: err.message,
      })
      fatalError = true
    } finally {
      await page.close()
    }
  }

  // 1. Home Page
  await testPage('Home', '/')

  // 2. Missions List
  await testPage('Missions', '/missions')

  // 3. Mission Profile
  await testPage('Mission Profile (Mars 2020)', '/missions/mars-2020')

  // 4. Time Machine
  await testPage('Time Machine', '/time-machine?explorer=perseverance', async (page) => {
    const slider = page.locator('input[type="range"]')
    if (await slider.count() > 0) {
      await slider.fill('50')
      await page.waitForTimeout(500)
    }
  })

  // 5. Gallery
  await testPage('Gallery', '/explorers/perseverance/gallery', async (page) => {
    // Select camera if available
    const camSelect = page.locator('#gc')
    if (await camSelect.count() > 0) {
      const options = await camSelect.locator('option').allInnerTexts()
      if (options.length > 1) {
        await camSelect.selectOption({ index: 1 })
        await page.waitForTimeout(500)
      }
    }
  })

  // 6. Map
  await testPage('Map', '/explorers/perseverance/map', async (page) => {
    const point = page.locator('circle.cursor-pointer').first()
    if (await point.count() > 0) {
      await point.click({ force: true })
      await page.waitForTimeout(800)
    }
  })

  // 7. Lunar Navigator - Site 1, Date 1
  await testPage('Lunar Navigator (Shackleton, 2026-12-25)', '/lunar', async (page) => {
    const btn = page.locator('button:has-text("Run analysis"), button:has-text("Analyse")').first()
    if (await btn.count() > 0 && await btn.isEnabled()) {
      await btn.click()
      await page.waitForTimeout(4000)
    }
  })

  // 8. Lunar Compare
  await testPage('Lunar Compare', '/lunar/compare')

  // 9. Assistant
  await testPage('Assistant', '/assistant', async (page) => {
    const input = page.locator('input[aria-label="Your question"]')
    const send = page.locator('button[type="submit"]')
    if (await input.count() > 0) {
      await input.fill('Where is the latest published position of Perseverance?')
      await send.click()
      await page.waitForSelector('text=Coordinates', { timeout: 15000 }).catch(() => {})
      await page.waitForTimeout(1000)
    }
  })

  await browser.close()

  console.log('\n--- SMOKE TEST SUMMARY ---')
  console.table(results.map(r => ({
    Page: r.page,
    Status: r.status,
    Errors: r.consoleErrors?.length || 0,
    FailedReqs: r.failedRequests?.length || 0,
    Forbidden: r.matchedForbidden?.join(', ') || 'None'
  })))

  fs.writeFileSync(path.join(SCREENSHOTS_DIR, 'smoke_report.json'), JSON.stringify(results, null, 2))
  console.log(`Report written to ${path.join(SCREENSHOTS_DIR, 'smoke_report.json')}`)

  if (fatalError) {
    process.exit(1)
  }
}

run().catch((err) => {
  console.error('Smoke runner crashed:', err)
  process.exit(1)
})
