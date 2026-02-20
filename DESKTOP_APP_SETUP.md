# 桌面应用设置完成 ✅

你的项目已经成功配置为 Electron 桌面应用！现在应用名称是"一键美"。

## 🎉 已完成的工作

1. ✅ 安装了 Electron 和相关依赖
2. ✅ 创建了 Electron 主进程 (`frontend/electron/main.js`)
3. ✅ 配置了打包工具 (electron-builder)
4. ✅ 更新了 Vite 配置以支持 Electron
5. ✅ 添加了开发和打包脚本
6. ✅ 创建了详细的使用文档

## 🚀 快速开始

### 开发模式（推荐）

```bash
# 1. 启动后端服务（新终端）
cd backend
bash run.sh

# 2. 启动 Electron 桌面应用（新终端）
cd frontend
npm run electron:dev
```

这会打开一个桌面应用窗口，支持热重载。

### 或者使用快速启动脚本

```bash
cd frontend
bash start-electron.sh
```

## 📦 打包应用

### 打包当前平台

```bash
cd frontend
npm run electron:build
```

### 打包特定平台

```bash
# macOS
npm run electron:build:mac

# Windows
npm run electron:build:win

# Linux
npm run electron:build:linux
```

打包后的文件在 `frontend/release/` 目录。

## 📁 项目结构

```
yijianmei/
├── backend/                    # Python 后端
│   └── run.sh                 # 后端启动脚本
│
├── frontend/                   # Electron 桌面应用
│   ├── electron/              # Electron 主进程
│   │   ├── main.js           # 主进程入口
│   │   └── preload.js        # 预加载脚本
│   ├── src/                   # React 前端代码
│   ├── dist/                  # 构建输出
│   ├── release/               # 打包输出（安装包）
│   ├── package.json           # 项目配置
│   ├── start-electron.sh      # 快速启动脚本
│   ├── ELECTRON_README.md     # Electron 使用指南
│   └── BUILD_GUIDE.md         # 打包详细指南
│
└── DESKTOP_APP_SETUP.md       # 本文件
```

## 🎯 下一步

### 1. 测试应用

运行 `npm run electron:dev` 测试桌面应用是否正常工作。

### 2. 自定义应用图标

将你的应用图标（512x512 PNG）放在 `frontend/public/icon.png`。

### 3. 更新应用信息

编辑 `frontend/package.json`：
- `author`: 你的名字
- `description`: 应用描述
- `version`: 版本号

### 4. 打包分发

```bash
cd frontend
npm run electron:build
```

生成的安装包可以直接分发给用户。

## 📚 文档

- **Electron 使用指南**: `frontend/ELECTRON_README.md`
- **打包详细指南**: `frontend/BUILD_GUIDE.md`

## 🔧 可用命令

| 命令 | 说明 |
|------|------|
| `npm run electron:dev` | 启动开发模式（Vite + Electron） |
| `npm run electron` | 仅启动 Electron（需要 Vite 已运行） |
| `npm run dev` | 仅启动 Vite（浏览器模式） |
| `npm run build` | 构建前端代码 |
| `npm run electron:build` | 打包桌面应用 |
| `npm run electron:build:mac` | 打包 macOS 应用 |
| `npm run electron:build:win` | 打包 Windows 应用 |
| `npm run electron:build:linux` | 打包 Linux 应用 |

## ⚠️ 注意事项

### 1. 后端服务必须运行

桌面应用仍然需要后端服务。确保在使用应用前启动后端：

```bash
cd backend
bash run.sh
```

### 2. 端口配置

- 后端: `http://localhost:8000`
- 前端开发服务器: `http://localhost:3000`

如果需要修改端口，请同时更新：
- `frontend/vite.config.ts` (proxy 配置)
- `frontend/src/services/api.ts` (API 地址)

### 3. 生产环境

如果要部署给最终用户，建议：
1. 将 Python 后端也打包进应用（使用 PyInstaller）
2. 在 Electron 主进程中自动启动后端
3. 购买代码签名证书（避免安全警告）

## 🐛 常见问题

### Q: Electron 窗口打不开？
A: 检查终端输出的错误信息，确保 Vite 开发服务器已启动。

### Q: 应用连接不到后端？
A: 确保后端服务在 `http://localhost:8000` 运行。

### Q: 打包后应用很大？
A: 正常现象，Electron 应用包含完整的 Chromium，通常 100-200MB。

### Q: macOS 提示"应用已损坏"？
A: 运行：`xattr -cr /Applications/一键美.app`

## 🎊 完成！

你现在有了一个完整的桌面应用！

- ✅ 可以像普通软件一样安装和使用
- ✅ 支持 Windows、macOS、Linux
- ✅ 可以打包成安装包分发
- ✅ 保留了所有原有功能

如有问题，请查看详细文档或提交 Issue。
