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
  console.log(`Starting smoke & screenshot suite against ${BASE_URL}...`)
  const browser = await chromium.launch({ headless: true })

  const viewports = [
    { name: '1440x900', width: 1440, height: 900 },
    { name: '390x844', width: 390, height: 844 },
  ]

  const results = []
  let fatalError = false

  for (const vp of viewports) {
    const context = await browser.newContext({ viewport: { width: vp.width, height: vp.height } })

    async function capture(pageName, urlPath, filename, customActions = null) {
      const page = await context.newPage()
      const consoleErrors = []
      const failedRequests = []

      page.on('console', (msg) => {
        if (msg.type() === 'error') consoleErrors.push(msg.text())
      })
      page.on('pageerror', (err) => consoleErrors.push(err.message))
      page.on('response', (res) => {
        if (res.status() >= 400) failedRequests.push(`${res.status()} ${res.url()}`)
      })

      try {
        console.log(`[${vp.name}] Testing ${pageName} (${urlPath})...`)
        await page.goto(`${BASE_URL}${urlPath}`, { waitUntil: 'networkidle', timeout: 30000 })
        await page.waitForTimeout(1000)

        if (customActions) {
          await customActions(page)
          await page.waitForTimeout(1000)
        }

        const bodyText = await page.innerText('body')
        const matchedForbidden = []
        for (const forbidden of FORBIDDEN_STRINGS) {
          if (bodyText.includes(forbidden)) matchedForbidden.push(forbidden)
        }

        const screenshotPath = path.join(SCREENSHOTS_DIR, `${filename}-${vp.name}.png`)
        await page.screenshot({ path: screenshotPath, fullPage: false })

        const status =
          consoleErrors.length === 0 && failedRequests.length === 0 && matchedForbidden.length === 0
            ? 'PASS'
            : 'WARN/FAIL'

        results.push({
          page: `${pageName} (${vp.name})`,
          url: urlPath,
          status,
          screenshot: screenshotPath,
          consoleErrors,
          failedRequests,
          matchedForbidden,
        })
        console.log(`  ✓ ${pageName} (${vp.name}): ${status}`)
      } catch (err) {
        console.error(`  ✗ ${pageName} (${vp.name}) failed:`, err.message)
        results.push({
          page: `${pageName} (${vp.name})`,
          url: urlPath,
          status: 'FAIL',
          error: err.message,
        })
        fatalError = true
      } finally {
        await page.close()
      }
    }

    // 1. Home
    await capture('Home', '/', 'home')

    // 2. Missions
    await capture('Missions', '/missions', 'missions')

    // 3. Mission Profile
    await capture('Mission Profile', '/missions/mars-2020', 'mission-profile')

    // 4. Gallery
    await capture('Gallery', '/explorers/perseverance/gallery', 'gallery')

    // 5. Lunar Navigator (analysed)
    await capture('Lunar Navigator', '/lunar', 'lunar-navigator', async (page) => {
      // Click Analyse / Run analysis button
      const btn = page.locator('button:has-text("Run analysis"), button:has-text("Analyse")').first()
      if ((await btn.count()) > 0 && (await btn.isEnabled())) {
        await btn.click()
        await page.waitForTimeout(3000)
      }
    })

    // 6. Ask AI Drawer
    await capture('Ask AI', '/', 'ask-ai', async (page) => {
      const askAiBtn = page.locator('button[aria-label="Ask AI Assistant"], button:has-text("Ask AI")').first()
      if ((await askAiBtn.count()) > 0) {
        await askAiBtn.click()
      }
      const drawer = page.locator('aside[aria-label="AI Research Assistant"]')
      await drawer.waitFor({ state: 'visible', timeout: 5000 })
      await page.waitForTimeout(1000)
    })

    // 7. Time Machine redirect check (only needed once, runs on desktop context)
    if (vp.name === '1440x900') {
      await capture('Time Machine Redirect', '/time-machine', 'time-machine-redirect', async (page) => {
        const url = page.url()
        if (!url.endsWith('/') && !url.endsWith('/#')) {
          throw new Error(`/time-machine should redirect to / but got: ${url}`)
        }
      })
    }

    await context.close()
  }

  await browser.close()

  console.log('\n--- SMOKE & VISUAL VERIFICATION SUMMARY ---')
  console.table(
    results.map((r) => ({
      Page: r.page,
      Status: r.status,
      Errors: r.consoleErrors?.length || 0,
      FailedReqs: r.failedRequests?.length || 0,
      Forbidden: r.matchedForbidden?.join(', ') || 'None',
    }))
  )

  fs.writeFileSync(path.join(SCREENSHOTS_DIR, 'smoke_report.json'), JSON.stringify(results, null, 2))
  console.log(`Report written to ${path.join(SCREENSHOTS_DIR, 'smoke_report.json')}`)

  if (fatalError) process.exit(1)
}

run().catch((err) => {
  console.error('Smoke runner crashed:', err)
  process.exit(1)
})
