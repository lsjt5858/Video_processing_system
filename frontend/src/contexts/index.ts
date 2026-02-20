/**
 * Context providers and hooks export
 * 
 * 使用方式：
 * 
 * 1. 在 App.tsx 中包裹 Provider：
 *    <WebSocketProvider>
 *      <VideoProvider>
 *        <TaskProvider>
 *          <App />
 *        </TaskProvider>
 *      </VideoProvider>
 *    </WebSocketProvider>
 * 
 * 2. 在组件中使用 Hook：
 *    const { videos, loadVideos } = useVideoContext()
 *    const { tasks, updateTaskProgress } = useTaskContext()
 *    const { isConnected, subscribe } = useWebSocketContext()
 */

export { VideoProvider, useVideoContext } from './VideoContext'
export { TaskProvider, useTaskContext } from './TaskContext'
export { WebSocketProvider, useWebSocketContext } from './WebSocketContext'
