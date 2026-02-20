# Electron 桌面应用使用指南

## 开发模式

### 启动开发环境
```bash
npm run electron:dev
```
这会同时启动 Vite 开发服务器和 Electron 窗口。

### 单独启动 Vite（用于浏览器调试）
```bash
npm run dev
```

## 打包应用

### 打包所有平台（根据当前系统）
```bash
npm run electron:build
```

### 打包 macOS 应用
```bash
npm run electron:build:mac
```
生成文件：
- `release/一键美-1.0.0.dmg` - DMG 安装包
- `release/一键美-1.0.0-mac.zip` - ZIP 压缩包

### 打包 Windows 应用
```bash
npm run electron:build:win
```
生成文件：
- `release/一键美 Setup 1.0.0.exe` - 安装程序
- `release/一键美 1.0.0.exe` - 便携版

### 打包 Linux 应用
```bash
npm run electron:build:linux
```
生成文件：
- `release/一键美-1.0.0.AppImage` - AppImage 格式
- `release/一键美_1.0.0_amd64.deb` - Debian 包

## 注意事项

### 1. 后端服务
桌面应用仍然需要后端服务运行。有两种方式：

**方式一：手动启动后端**
```bash
cd backend
bash run.sh
```

**方式二：集成后端到 Electron（推荐用于生产）**
可以将 Python 后端打包进 Electron，实现真正的独立应用。

### 2. 应用图标
请将应用图标放在 `public/icon.png`，建议尺寸：
- macOS: 512x512 或 1024x1024
- Windows: 256x256
- Linux: 512x512

支持的格式：PNG, ICNS (macOS), ICO (Windows)

### 3. 配置修改
在 `package.json` 的 `build` 字段中可以修改：
- `appId`: 应用唯一标识
- `productName`: 应用显示名称
- `directories.output`: 打包输出目录

### 4. 代码签名（可选）
生产环境建议对应用进行代码签名：

**macOS:**
```json
"mac": {
  "identity": "Developer ID Application: Your Name (TEAM_ID)"
}
```

**Windows:**
需要购买代码签名证书。

## 开发调试

### 打开开发者工具
- 开发模式：自动打开
- 快捷键：`F12` 或 `Cmd+Option+I` (Mac) / `Ctrl+Shift+I` (Windows/Linux)

### 查看日志
- 主进程日志：终端输出
- 渲染进程日志：开发者工具 Console

## 常见问题

### Q: 打包后应用无法启动？
A: 检查 `electron/main.js` 中的路径配置，确保使用相对路径。

### Q: 如何减小应用体积？
A: 
1. 在 `package.json` 的 `build.files` 中只包含必要文件
2. 使用 `asar` 打包（默认启用）
3. 移除不必要的依赖

### Q: 如何自动更新？
A: 可以集成 `electron-updater` 实现自动更新功能。

## 项目结构

```
frontend/
├── electron/           # Electron 主进程代码
│   ├── main.js        # 主进程入口
│   └── preload.js     # 预加载脚本
├── src/               # React 应用代码
├── dist/              # Vite 构建输出
├── release/           # Electron 打包输出
└── package.json       # 项目配置
```

## 下一步

1. 替换 `public/icon.png` 为你的应用图标
2. 修改 `package.json` 中的 `author` 和 `description`
3. 运行 `npm run electron:dev` 测试开发环境
4. 运行 `npm run electron:build` 打包应用
