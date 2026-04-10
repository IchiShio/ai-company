import { defineConfig } from 'vite'
import path from 'path'
import fs from 'fs'

export default defineConfig({
  base: '/sync/',
  build: {
    outDir: '../sync',
    emptyOutDir: false,  // audio/ を消さない
  },
  plugins: [{
    name: 'serve-audio-dev',
    configureServer(server) {
      // dev: /sync/audio/* → ../sync/audio/* を直接配信
      server.middlewares.use('/sync/audio', (req, res, next) => {
        const filePath = path.resolve(__dirname, '../sync/audio', (req.url ?? '/').slice(1))
        if (fs.existsSync(filePath)) {
          const ext = path.extname(filePath)
          res.setHeader('Content-Type', ext === '.mp3' ? 'audio/mpeg' : 'application/json')
          fs.createReadStream(filePath).pipe(res as unknown as NodeJS.WritableStream)
        } else {
          next()
        }
      })
    },
  }],
})
