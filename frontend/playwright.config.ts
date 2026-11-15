import { existsSync } from 'node:fs'
import { resolve } from 'node:path'

import { defineConfig, devices } from '@playwright/test'

/**
 * End-to-end smoke tests (Chromium only). They run against the production build: `next start`.
 *
 * - No build yet? The webServer command builds first (slow, minutes). Run `pnpm build` beforehand to
 *   skip it locally.
 * - Port: E2E_PORT, default 3100 (a free port, not the dev server's 3000).
 * - Nothing in the tests calls ElevenLabs: the signed-url endpoint is mocked with page.route.
 */

const PORT = Number(process.env.E2E_PORT ?? 3100)
const baseURL = `http://127.0.0.1:${PORT}`
// Run from the frontend directory (pnpm does this). The package is CommonJS, so no import.meta here.
const hasBuild = existsSync(resolve(process.cwd(), '.next', 'BUILD_ID'))
const startCommand = `pnpm exec next start -p ${PORT} -H 127.0.0.1`

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [['list'], ['html', { open: 'never' }]] : 'list',
  use: {
    baseURL,
    trace: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: hasBuild ? startCommand : `pnpm build && ${startCommand}`,
    url: baseURL,
    reuseExistingServer: !process.env.CI,
    timeout: 600_000,
    // Public agent id is inlined at build time. This placeholder is not a real agent and is never used
    // for a live call: the signed-url request is mocked in the tests.
    // ELEVENLABS_API_KEY is overridden on purpose: process env wins over frontend/.env.local, so a real
    // developer key can never be used by the e2e server, whatever is on disk.
    env: {
      ...process.env,
      ELEVENLABS_API_KEY: 'e2e-fake-key-not-a-real-credential',
      NEXT_PUBLIC_ELEVENLABS_AGENT_ID: process.env.NEXT_PUBLIC_ELEVENLABS_AGENT_ID ?? 'agent_e2eplaceholder01',
    },
  },
})
