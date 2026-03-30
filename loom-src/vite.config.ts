import { defineConfig } from 'vite'

export default defineConfig({
  base: '/loom/',
  build: {
    outDir: '../loom',
    emptyOutDir: true,
  },
})
