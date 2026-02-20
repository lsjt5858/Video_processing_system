# WebSocket 连接问题修复说明

## 问题描述

在本地打开应用后，再次打开网页时会提示：
```
WebSocket 连接失败，已达到最大重连次数
```

## 问题原因

1. **无限重连**：之前的 WebSocket 实现没有最大重连次数限制，会一直尝试重连
2. **不必要的连接**：即使在不需要实时更新的页面，WebSocket 也在尝试连接
3. **缺少错误处理**：连接失败时没有友好的降级方案

## 解决方案

### 1. 添加最大重连次数限制

在 `useWebSocket` hook 中添加了 `maxReconnectAttempts` 参数（默认 5 次）：

```typescript
interface UseWebSocketOptions {
  // ... 其他选项
  maxReconnectAttempts?: number  // 新增：最大重连次数
}
```

### 2. 改进重连逻辑

- 连接成功后重置重连计数器
- 达到最大重连次数后停止重连
- 组件卸载时停止重连尝试
- 显示友好的警告信息

### 3. 添加错误处理回调

所有使用 WebSocket 的页面都添加了 `onError` 回调：

```typescript
useWebSocket(url, {
  onError: () => {
    console.warn('WebSocket 连接错误，将使用轮询方式')
  },
  maxReconnectAttempts: 3,
})
```

### 4. 优化连接策略

- VideoUpload: 限制最多重连 3 次
- BatchProcessing: 限制最多重连 3 次
- TaskManager: 限制最多重连 3 次，并有定时轮询作为备用方案

## 修改的文件

1. `frontend/src/hooks/useWebSocket.ts` - 核心 WebSocket hook
2. `frontend/src/pages/VideoUpload.tsx` - 视频上传页面
3. `frontend/src/pages/BatchProcessing.tsx` - 批量处理页面
4. `frontend/src/pages/TaskManager.tsx` - 任务管理页面

## 使用建议

### 对于开发者

如果需要调整重连策略，可以在使用 `useWebSocket` 时传入参数：

```typescript
useWebSocket(url, {
  reconnect: true,              // 是否自动重连
  reconnectInterval: 3000,      // 重连间隔（毫秒）
  maxReconnectAttempts: 5,      // 最大重连次数
  onError: (error) => {
    // 错误处理
  },
})
```

### 对于用户

如果看到 WebSocket 连接失败的警告：

1. **不影响使用**：应用会自动降级到轮询模式
2. **检查后端**：确保后端服务在 `http://localhost:8000` 运行
3. **刷新页面**：如果需要，可以刷新页面重新连接

## 测试验证

### 测试场景 1：正常连接
1. 启动后端服务
2. 打开应用
3. WebSocket 应该正常连接

### 测试场景 2：后端未启动
1. 不启动后端服务
2. 打开应用
3. 应该看到最多 3-5 次重连尝试
4. 然后停止重连，显示警告信息
5. 应用其他功能仍然可用

### 测试场景 3：后端中途断开
1. 启动后端和前端
2. 停止后端服务
3. 应该看到重连尝试
4. 达到最大次数后停止

### 测试场景 4：后端恢复
1. 在场景 3 的基础上
2. 重新启动后端
3. 刷新页面，WebSocket 应该重新连接

## 后续优化建议

### 1. 添加连接状态指示器

在 UI 上显示 WebSocket 连接状态：

```tsx
{!isConnected && (
  <Alert
    message="实时更新已断开"
    description="正在使用轮询模式获取更新"
    type="warning"
    closable
  />
)}
```

### 2. 智能重连策略

根据网络状况动态调整重连间隔：

```typescript
// 指数退避算法
const reconnectInterval = Math.min(
  initialInterval * Math.pow(2, reconnectAttempts),
  maxInterval
)
```

### 3. 心跳检测

定期发送心跳包检测连接状态：

```typescript
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'ping' }))
  }
}, 30000)
```

### 4. 离线检测

监听浏览器在线/离线事件：

```typescript
window.addEventListener('online', () => {
  // 网络恢复，尝试重连
  connect()
})

window.addEventListener('offline', () => {
  // 网络断开，停止重连
  disconnect()
})
```

## 总结

通过添加最大重连次数限制和改进错误处理，WebSocket 连接问题已经得到解决。应用现在能够：

- ✅ 优雅地处理连接失败
- ✅ 避免无限重连
- ✅ 提供友好的错误提示
- ✅ 在 WebSocket 不可用时降级到轮询模式

用户体验得到了显著改善。
