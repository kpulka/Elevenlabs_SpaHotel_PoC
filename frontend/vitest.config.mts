import { fileURLToPath } from 'node:url'

import { defineConfig } from 'vitest/config'

// Unit tests (hooks, lib, route handlers). End-to-end tests live in e2e/ (Playwright) and are excluded here.
// The `@/` alias mirrors tsconfig.json.
export default defineConfig({
  resolve: {
    alias: [{ find: /^@\//, replacement: fileURLToPath(new URL('./', import.meta.url)) }],
  },
  test: {
    environment: 'jsdom',
    include: ['**/*.test.{ts,tsx}'],
    exclude: ['node_modules/**', '.next/**', 'e2e/**'],
  },
})
