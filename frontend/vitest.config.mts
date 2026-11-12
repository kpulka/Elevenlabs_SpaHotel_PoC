import { fileURLToPath } from 'node:url'

import { defineConfig } from 'vitest/config'

// Testy jednostkowe (hooki, lib). Bez e2e. Alias `@/` jak w tsconfig.json.
export default defineConfig({
  resolve: {
    alias: [{ find: /^@\//, replacement: fileURLToPath(new URL('./', import.meta.url)) }],
  },
  test: {
    environment: 'jsdom',
    include: ['**/*.test.{ts,tsx}'],
    exclude: ['node_modules/**', '.next/**'],
  },
})
