import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  base: './', // Electron 需要相对路径
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
        changeOrigin: true,
      },
    },
  },
  build: {
    // 输出目录
    outDir: 'dist',
    // 生成sourcemap用于生产环境调试
    sourcemap: false,
    // 代码分割策略
    rollupOptions: {
      output: {
        // 手动分割代码块
        manualChunks: {
          // React核心库
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          // Ant Design UI库
          'antd-vendor': ['antd'],
          // 工具库
          'utils-vendor': ['axios', 'dayjs'],
        },
        // 资源文件命名
        chunkFileNames: 'assets/js/[name]-[hash].js',
        entryFileNames: 'assets/js/[name]-[hash].js',
        assetFileNames: 'assets/[ext]/[name]-[hash].[ext]',
      },
    },
    // 压缩选项
    minify: 'terser',
    terserOptions: {
      compress: {
        // 移除console
        drop_console: true,
        // 移除debugger
        drop_debugger: true,
      },
    },
    // chunk大小警告限制（500kb）
    chunkSizeWarningLimit: 500,
    // 启用CSS代码分割
    cssCodeSplit: true,
  },
})
