# 打包桌面应用指南

## 准备工作

### 1. 创建应用图标

将你的应用图标放在 `public/icon.png`，建议使用 512x512 或 1024x1024 的 PNG 图片。

如果你有不同格式的图标：
- macOS: `public/icon.icns`
- Windows: `public/icon.ico`
- Linux: `public/icon.png`

### 2. 更新应用信息

编辑 `package.json`：

```json
{
  "name": "yijianmei",
  "productName": "一键美",
  "version": "1.0.0",
  "description": "智能视频美化工具",
  "author": "你的名字 <your.email@example.com>"
}
```

## 打包步骤

### macOS 应用

```bash
# 打包 DMG 和 ZIP
npm run electron:build:mac
```

生成的文件在 `release/` 目录：
- `一键美-1.0.0.dmg` - 安装包（推荐分发）
- `一键美-1.0.0-mac.zip` - 压缩包

**安装方式：**
1. 双击 DMG 文件
2. 拖动应用到 Applications 文件夹
3. 首次打开可能需要在"系统偏好设置 > 安全性与隐私"中允许

### Windows 应用

```bash
# 打包安装程序和便携版
npm run electron:build:win
```

生成的文件：
- `一键美 Setup 1.0.0.exe` - 安装程序（推荐）
- `一键美 1.0.0.exe` - 便携版（无需安装）

**安装程序特性：**
- 可选择安装目录
- 创建桌面快捷方式
- 创建开始菜单快捷方式
- 支持卸载

### Linux 应用

```bash
# 打包 AppImage 和 DEB
npm run electron:build:linux
```

生成的文件：
- `一键美-1.0.0.AppImage` - 通用格式（推荐）
- `一键美_1.0.0_amd64.deb` - Debian/Ubuntu 包

**AppImage 使用：**
```bash
chmod +x 一键美-1.0.0.AppImage
./一键美-1.0.0.AppImage
```

**DEB 安装：**
```bash
sudo dpkg -i 一键美_1.0.0_amd64.deb
```

## 打包所有平台

如果你在 macOS 上，可以同时打包 Mac、Windows 和 Linux 版本：

```bash
npm run electron:build
```

注意：跨平台打包可能需要额外配置。

## 高级配置

### 1. 代码签名（推荐用于生产）

**macOS:**
```json
"mac": {
  "identity": "Developer ID Application: Your Name (TEAM_ID)",
  "hardenedRuntime": true,
  "gatekeeperAssess": false,
  "entitlements": "build/entitlements.mac.plist",
  "entitlementsInherit": "build/entitlements.mac.plist"
}
```

**Windows:**
需要购买代码签名证书，然后配置：
```json
"win": {
  "certificateFile": "path/to/cert.pfx",
  "certificatePassword": "password"
}
```

### 2. 自动更新

安装 electron-updater：
```bash
npm install electron-updater
```

在 `electron/main.js` 中添加：
```javascript
const { autoUpdater } = require('electron-updater')

app.whenReady().then(() => {
  autoUpdater.checkForUpdatesAndNotify()
})
```

### 3. 减小应用体积

在 `package.json` 中配置：
```json
"build": {
  "asar": true,
  "compression": "maximum",
  "files": [
    "dist/**/*",
    "electron/**/*",
    "package.json"
  ]
}
```

### 4. 多语言支持

在 `electron/main.js` 中：
```javascript
const locale = app.getLocale() // 获取系统语言
```

## 分发应用

### 方式一：直接分发安装包
将生成的安装包上传到你的网站或云存储。

### 方式二：使用 GitHub Releases
1. 在 GitHub 创建 Release
2. 上传打包文件
3. 用户可以直接下载

### 方式三：应用商店
- macOS: Mac App Store
- Windows: Microsoft Store
- Linux: Snap Store, Flathub

## 测试清单

打包前请测试：

- [ ] 应用能正常启动
- [ ] 所有功能正常工作
- [ ] 后端连接正常
- [ ] 文件上传/下载正常
- [ ] WebSocket 连接正常
- [ ] 应用图标显示正确
- [ ] 菜单功能正常
- [ ] 快捷键工作正常
- [ ] 窗口大小和位置正常
- [ ] 应用能正常退出

## 常见问题

### Q: 打包后应用体积很大？
A: Electron 应用包含完整的 Chromium 和 Node.js，通常 100-200MB 是正常的。

### Q: 打包失败？
A: 检查：
1. Node.js 版本是否兼容
2. 是否有足够的磁盘空间
3. 网络连接是否正常（需要下载依赖）

### Q: macOS 提示"应用已损坏"？
A: 这是因为应用未签名。用户可以：
```bash
xattr -cr /Applications/一键美.app
```

### Q: Windows Defender 报毒？
A: 未签名的应用可能被误报。建议购买代码签名证书。

## 后端集成（可选）

如果想要真正的独立应用（不需要单独启动后端），可以：

1. 使用 PyInstaller 打包 Python 后端
2. 在 Electron 主进程中启动后端进程
3. 应用退出时关闭后端进程

示例代码：
```javascript
const { spawn } = require('child_process')
const path = require('path')

let backendProcess

function startBackend() {
  const backendPath = path.join(__dirname, '../backend/dist/main')
  backendProcess = spawn(backendPath)
}

app.on('quit', () => {
  if (backendProcess) {
    backendProcess.kill()
  }
})
```

## 更新日志

记得在每次发布新版本时更新：
1. `package.json` 中的 `version`
2. 创建 CHANGELOG.md 记录更新内容
3. 在 GitHub 创建对应的 Release Tag
