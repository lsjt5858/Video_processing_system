import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, act } from '@testing-library/react'
import { renderHook } from '@testing-library/react'
import { WebSocketProvider, useWebSocketContext } from '@/contexts/WebSocketContext'
import { useWebSocket } from '@/hooks/useWebSocket'

// Mock WebSocket
class MockWebSocket {
  static CONNECTING = 0
  static OPEN = 1
  static CLOSING = 2
  static CLOSED = 3

  url: string
  readyState: number = MockWebSocket.CONNECTING
  onopen: ((event: Event) => void) | null = null
  onclose: ((event: CloseEvent) => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null

  constructor(url: string) {
    this.url = url
    // 模拟异步连接
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN
      if (this.onopen) {
        this.onopen(new Event('open'))
      }
    }, 10)
  }

  send(data: string) {
    // Mock send
  }

  close() {
    this.readyState = MockWebSocket.CLOSED
    if (this.onclose) {
      this.onclose(new CloseEvent('close'))
    }
  }

  // 模拟接收消息
  simulateMessage(data: any) {
    if (this.onmessage) {
      const event = new MessageEvent('message', {
        data: JSON.stringify(data),
      })
      this.onmessage(event)
    }
  }

  // 模拟错误
  simulateError() {
    if (this.onerror) {
      this.onerror(new Event('error'))
    }
  }
}

describe('WebSocket实时更新测试 - WebSocket Real-time Updates', () => {
  let mockWs: MockWebSocket

  beforeEach(() => {
    // 替换全局 WebSocket
    global.WebSocket = MockWebSocket as any
    // Don't use fake timers for WebSocket tests - they interfere with async connection
  })

  afterEach(() => {
    // Cleanup
  })

  describe('WebSocketContext', () => {
    it('应该初始化为未连接状态', () => {
      const { result } = renderHook(() => useWebSocketContext(), {
        wrapper: ({ children }) => (
          <WebSocketProvider url="ws://localhost:8000/ws" autoConnect={false}>
            {children}
          </WebSocketProvider>
        ),
      })

      expect(result.current.isConnected).toBe(false)
      expect(result.current.connectionStatus).toBe('disconnected')
    })

    it('应该在autoConnect为true时自动连接', async () => {
      const { result } = renderHook(() => useWebSocketContext(), {
        wrapper: ({ children }) => (
          <WebSocketProvider url="ws://localhost:8000/ws" autoConnect={true}>
            {children}
          </WebSocketProvider>
        ),
      })

      // 等待连接建立
      await waitFor(() => {
        expect(result.current.isConnected).toBe(true)
        expect(result.current.connectionStatus).toBe('connected')
      }, { timeout: 1000 })
    })

    it('应该能够手动连接WebSocket', async () => {
      const { result } = renderHook(() => useWebSocketContext(), {
        wrapper: ({ children }) => (
          <WebSocketProvider url="ws://localhost:8000/ws" autoConnect={false}>
            {children}
          </WebSocketProvider>
        ),
      })

      expect(result.current.isConnected).toBe(false)

      // 手动连接
      act(() => {
        result.current.connect()
      })

      // 等待连接建立
      await waitFor(() => {
        expect(result.current.isConnected).toBe(true)
      }, { timeout: 1000 })
    })

    it('应该能够断开WebSocket连接', async () => {
      const { result } = renderHook(() => useWebSocketContext(), {
        wrapper: ({ children }) => (
          <WebSocketProvider url="ws://localhost:8000/ws" autoConnect={true}>
            {children}
          </WebSocketProvider>
        ),
      })

      // 等待连接建立
      await waitFor(() => {
        expect(result.current.isConnected).toBe(true)
      }, { timeout: 1000 })

      // 断开连接
      act(() => {
        result.current.disconnect()
      })

      await waitFor(() => {
        expect(result.current.isConnected).toBe(false)
        expect(result.current.connectionStatus).toBe('disconnected')
      })
    })

    it('应该能够接收WebSocket消息', async () => {
      let wsInstance: MockWebSocket | null = null
      
      // 拦截 WebSocket 构造函数
      const OriginalWebSocket = global.WebSocket
      global.WebSocket = class extends MockWebSocket {
        constructor(url: string) {
          super(url)
          wsInstance = this
        }
      } as any

      const { result } = renderHook(() => useWebSocketContext(), {
        wrapper: ({ children }) => (
          <WebSocketProvider url="ws://localhost:8000/ws" autoConnect={true}>
            {children}
          </WebSocketProvider>
        ),
      })

      // 等待连接建立
      await waitFor(() => {
        expect(result.current.isConnected).toBe(true)
      }, { timeout: 1000 })

      // 模拟接收消息
      const testMessage = {
        type: 'upload_progress',
        data: { filename: 'test.mp4', progress: 50 },
        timestamp: new Date().toISOString(),
      }

      act(() => {
        wsInstance?.simulateMessage(testMessage)
      })

      await waitFor(() => {
        expect(result.current.lastMessage).toEqual(testMessage)
      })

      global.WebSocket = OriginalWebSocket
    })

    it('应该能够订阅特定类型的消息', async () => {
      let wsInstance: MockWebSocket | null = null
      
      const OriginalWebSocket = global.WebSocket
      global.WebSocket = class extends MockWebSocket {
        constructor(url: string) {
          super(url)
          wsInstance = this
        }
      } as any

      const onMessage = vi.fn()

      const { result } = renderHook(() => useWebSocketContext(), {
        wrapper: ({ children }) => (
          <WebSocketProvider url="ws://localhost:8000/ws" autoConnect={true}>
            {children}
          </WebSocketProvider>
        ),
      })

      // 等待连接建立
      await waitFor(() => {
        expect(result.current.isConnected).toBe(true)
      }, { timeout: 1000 })

      // 订阅消息
      let unsubscribe: (() => void) | undefined
      act(() => {
        unsubscribe = result.current.subscribe('upload_progress', onMessage)
      })

      // 模拟接收消息
      const testMessage = {
        type: 'upload_progress',
        data: { filename: 'test.mp4', progress: 50 },
        timestamp: new Date().toISOString(),
      }

      act(() => {
        wsInstance?.simulateMessage(testMessage)
      })

      await waitFor(() => {
        expect(onMessage).toHaveBeenCalledWith(testMessage.data)
      })

      // 取消订阅
      act(() => {
        unsubscribe?.()
      })

      // 再次发送消息，不应该触发回调
      onMessage.mockClear()
      act(() => {
        wsInstance?.simulateMessage(testMessage)
      })

      // 等待一段时间确保不会被调用
      await new Promise(resolve => setTimeout(resolve, 100))

      expect(onMessage).not.toHaveBeenCalled()

      global.WebSocket = OriginalWebSocket
    })

    it('应该能够发送消息', async () => {
      let wsInstance: MockWebSocket | null = null
      
      const OriginalWebSocket = global.WebSocket
      global.WebSocket = class extends MockWebSocket {
        constructor(url: string) {
          super(url)
          wsInstance = this
        }
      } as any

      const sendSpy = vi.spyOn(MockWebSocket.prototype, 'send')

      const { result } = renderHook(() => useWebSocketContext(), {
        wrapper: ({ children }) => (
          <WebSocketProvider url="ws://localhost:8000/ws" autoConnect={true}>
            {children}
          </WebSocketProvider>
        ),
      })

      // 等待连接建立
      await waitFor(() => {
        expect(result.current.isConnected).toBe(true)
      }, { timeout: 1000 })

      // 发送消息
      act(() => {
        result.current.sendMessage('test_message', { data: 'test' })
      })

      expect(sendSpy).toHaveBeenCalled()

      global.WebSocket = OriginalWebSocket
    })

    it('应该在未连接时将消息加入队列', async () => {
      const { result } = renderHook(() => useWebSocketContext(), {
        wrapper: ({ children }) => (
          <WebSocketProvider url="ws://localhost:8000/ws" autoConnect={false}>
            {children}
          </WebSocketProvider>
        ),
      })

      expect(result.current.isConnected).toBe(false)

      // 发送消息（未连接状态）
      act(() => {
        result.current.sendMessage('test_message', { data: 'test' })
      })

      // 消息应该被加入队列
      await waitFor(() => {
        expect(result.current.messageQueue.length).toBe(1)
      })
    })

    it('应该能够清除消息队列', async () => {
      const { result } = renderHook(() => useWebSocketContext(), {
        wrapper: ({ children }) => (
          <WebSocketProvider url="ws://localhost:8000/ws" autoConnect={false}>
            {children}
          </WebSocketProvider>
        ),
      })

      // 发送消息（未连接状态）
      act(() => {
        result.current.sendMessage('test_message', { data: 'test' })
      })

      await waitFor(() => {
        expect(result.current.messageQueue.length).toBe(1)
      })

      // 清除队列
      act(() => {
        result.current.clearMessageQueue()
      })

      await waitFor(() => {
        expect(result.current.messageQueue.length).toBe(0)
      })
    })
  })

  describe('useWebSocket Hook', () => {
    it('应该初始化为未连接状态', () => {
      const { result } = renderHook(() => 
        useWebSocket('ws://localhost:8000/ws', { reconnect: false })
      )

      expect(result.current.isConnected).toBe(false)
    })

    it('应该在连接建立后更新状态', async () => {
      const onOpen = vi.fn()
      
      const { result } = renderHook(() => 
        useWebSocket('ws://localhost:8000/ws', { onOpen, reconnect: false })
      )

      // 等待连接建立
      await waitFor(() => {
        expect(result.current.isConnected).toBe(true)
        expect(onOpen).toHaveBeenCalled()
      }, { timeout: 1000 })
    })

    it('应该能够接收消息并触发回调', async () => {
      let wsInstance: MockWebSocket | null = null
      
      const OriginalWebSocket = global.WebSocket
      global.WebSocket = class extends MockWebSocket {
        constructor(url: string) {
          super(url)
          wsInstance = this
        }
      } as any

      const onMessage = vi.fn()
      
      const { result } = renderHook(() => 
        useWebSocket('ws://localhost:8000/ws', { onMessage, reconnect: false })
      )

      // 等待连接建立
      await waitFor(() => {
        expect(result.current.isConnected).toBe(true)
      }, { timeout: 1000 })

      // 模拟接收消息
      const testMessage = {
        type: 'upload_progress',
        data: { filename: 'test.mp4', progress: 50 },
      }

      act(() => {
        wsInstance?.simulateMessage(testMessage)
      })

      await waitFor(() => {
        expect(onMessage).toHaveBeenCalledWith(testMessage)
        expect(result.current.lastMessage).toEqual(testMessage)
      })

      global.WebSocket = OriginalWebSocket
    })

    it('应该能够发送消息', async () => {
      let wsInstance: MockWebSocket | null = null
      
      const OriginalWebSocket = global.WebSocket
      global.WebSocket = class extends MockWebSocket {
        constructor(url: string) {
          super(url)
          wsInstance = this
        }
      } as any

      const sendSpy = vi.spyOn(MockWebSocket.prototype, 'send')

      const { result } = renderHook(() => 
        useWebSocket('ws://localhost:8000/ws', { reconnect: false })
      )

      // 等待连接建立
      await waitFor(() => {
        expect(result.current.isConnected).toBe(true)
      }, { timeout: 1000 })

      // 发送消息
      act(() => {
        result.current.sendMessage({ type: 'test', data: 'hello' })
      })

      expect(sendSpy).toHaveBeenCalled()

      global.WebSocket = OriginalWebSocket
    })

    it('应该在连接关闭时触发回调', async () => {
      let wsInstance: MockWebSocket | null = null
      
      const OriginalWebSocket = global.WebSocket
      global.WebSocket = class extends MockWebSocket {
        constructor(url: string) {
          super(url)
          wsInstance = this
        }
      } as any

      const onClose = vi.fn()
      
      const { result } = renderHook(() => 
        useWebSocket('ws://localhost:8000/ws', { onClose, reconnect: false })
      )

      // 等待连接建立
      await waitFor(() => {
        expect(result.current.isConnected).toBe(true)
      }, { timeout: 1000 })

      // 断开连接
      act(() => {
        result.current.disconnect()
      })

      await waitFor(() => {
        expect(result.current.isConnected).toBe(false)
        expect(onClose).toHaveBeenCalled()
      })

      global.WebSocket = OriginalWebSocket
    })

    it('应该在连接错误时触发回调', async () => {
      let wsInstance: MockWebSocket | null = null
      
      const OriginalWebSocket = global.WebSocket
      global.WebSocket = class extends MockWebSocket {
        constructor(url: string) {
          super(url)
          wsInstance = this
        }
      } as any

      const onError = vi.fn()
      
      const { result } = renderHook(() => 
        useWebSocket('ws://localhost:8000/ws', { onError, reconnect: false })
      )

      // 等待连接建立
      await waitFor(() => {
        expect(result.current.isConnected).toBe(true)
      }, { timeout: 1000 })

      // 模拟错误
      act(() => {
        wsInstance?.simulateError()
      })

      await waitFor(() => {
        expect(onError).toHaveBeenCalled()
      })

      global.WebSocket = OriginalWebSocket
    })
  })
})
