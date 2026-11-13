import { defineConfig, globalIgnores } from 'eslint/config'
import nextVitals from 'eslint-config-next/core-web-vitals'
import nextTs from 'eslint-config-next/typescript'

// Skrypt `lint` uruchamia ESLint z `--quiet`: raportowane są tylko błędy (severity "error"),
// ostrzeżenia i reguły stylu z konfiguracji Next są ignorowane.
const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  // Domyślne ignorowane ścieżki eslint-config-next, plus pliki generowane.
  // public/widget/ to zbundlowany, zminifikowany skrypt widgetu ElevenLabs (vendor), nie nasz kod.
  globalIgnores(['.next/**', 'out/**', 'build/**', 'next-env.d.ts', 'public/widget/**']),
])

export default eslintConfig
