# 一键美 - 前端

基于 React 18 + Vite + TypeScript + Ant Design 的现代化前端应用。

## 技术栈

- **React 18**: 最新的 React 特性
- **TypeScript**: 类型安全
- **Vite**: 快速的开发服务器和构建工具
- **Ant Design**: 企业级 UI 组件库
- **React Router**: 路由管理
- **Axios**: HTTP 请求库

## 开发环境要求

- Node.js >= 16.0.0
- npm >= 8.0.0 或 yarn >= 1.22.0

## 安装依赖

```bash
npm install
# 或
yarn install
```

## 开发

启动开发服务器（默认端口 3000）：

```bash
npm run dev
# 或
yarn dev
```

开发服务器会自动代理以下请求到后端（http://localhost:8000）：
- `/api/*` - REST API 请求
- `/ws/*` - WebSocket 连接

## 构建

构建生产版本：

```bash
npm run build
# 或
yarn build
```

构建产物将输出到 `dist/` 目录。

## 预览

预览生产构建：

```bash
npm run preview
# 或
yarn preview
```

## 项目结构

```
frontend/
├── src/
│   ├── pages/          # 页面组件
│   ├── components/     # 通用组件
│   ├── services/       # API 服务
│   ├── hooks/          # 自定义 Hooks
│   ├── types/          # TypeScript 类型定义
│   ├── App.tsx         # 根组件
│   ├── main.tsx        # 入口文件
│   └── vite-env.d.ts   # Vite 类型声明
├── public/             # 静态资源
├── index.html          # HTML 模板
├── vite.config.ts      # Vite 配置
├── tsconfig.json       # TypeScript 配置
└── package.json        # 项目依赖
```

## 配置说明

### Vite 代理配置

在 `vite.config.ts` 中配置了代理，将前端请求转发到后端：

```typescript
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
}
```

### TypeScript 路径别名

配置了 `@` 别名指向 `src` 目录：

```typescript
import Component from '@/components/Component'
```

## 后续开发

接下来需要实现的功能：

1. 视频列表页面
2. 视频上传页面
3. 水印标记页面
4. 水印去除页面
5. 批量处理页面
6. 任务管理页面

详见项目任务列表。
