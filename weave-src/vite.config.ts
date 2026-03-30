import { defineConfig } from 'vite'

export default defineConfig({
  base: '/weave/',
  build: {
    outDir: '../weave',
    emptyOutDir: true,
  },
})
