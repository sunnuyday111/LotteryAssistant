import { defineConfig, type Plugin } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'node:path'

/** 去掉 Vite 在 <script> / <link> 上加的 crossorigin 属性。
 *  tauri:// 协议下 WebView2 会对 crossorigin 资源做 CORS 检查，
 *  但本地应用协议没有 CORS 头，导致新窗口白屏。 */
function stripCrossorigin(): Plugin {
  return {
    name: 'strip-crossorigin',
    transformIndexHtml: {
      order: 'post',
      handler(html) {
        return html.replace(/\s+crossorigin(="")?/g, '')
      },
    },
  }
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), stripCrossorigin()],
  // 绝对根路径：保证无论页面 URL 是什么（/checkin/<token>、/events/<id>），
  // 资源都能从根加载；Tauri tauri:// 协议同样适用
  base: '/',
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
})
