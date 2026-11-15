import { defineConfig, globalIgnores } from 'eslint/config'
import nextVitals from 'eslint-config-next/core-web-vitals'
import nextTs from 'eslint-config-next/typescript'

// The `lint` script runs ESLint with `--quiet`: only errors (severity "error") are reported,
// warnings and style rules from the Next config are ignored.
const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  // Default eslint-config-next ignores, plus generated files.
  // public/widget/ is the bundled, minified ElevenLabs widget script (vendored), not our code.
  globalIgnores(['.next/**', 'out/**', 'build/**', 'next-env.d.ts', 'public/widget/**']),
])

export default eslintConfig
