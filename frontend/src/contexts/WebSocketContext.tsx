import React, { createContext, useContext, useEffect, useRef, useState, useCallback, ReactNode } from 'react'
import { message } from 'antd'

interface WebSocketMessage {
  type: string
  data: any
  timestamp: string
}

interface WebSocketContextType {
  // 连接状态
  isConnected: boolean
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error'
  
  // 最后收到的消息
  lastMessage: WebSocketMessage | null
  
  // 消息队列（用于离线时缓存消息）
  messageQueue: WebSocketMessage[]
  
  // 操作方法
  sendMessage: (type: string, data: any) => void
  subscribe: (type: string, callback: (data: any) => void) => () => void
  connect: () => void
  disconnect: () => void
  clearMessageQueue: () => void
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined)

interface WebSocketProviderProps {
  children: ReactNode
  url?: string
  autoConnect?: boolean
  reconnectInterval?: number
  maxReconnectAttempts?: number
}

/**
 * WebSocket 状态管理 Context Provider
 * 管理 WebSocket 连接、消息队列和事件订阅
 */
export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({ 
  children,
  url = 'ws://localhost:8000/ws/client',
  autoConnect = true,
  reconnectInterval = 3000,
  maxReconnectAttempts = 10,
}) => {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>()
  const reconnectAttemptsRef = useRef(0)
  const subscribersRef = useRef<Map<string, Set<(data: any) => void>>>(new Map())
  
  const [isConnected, setIsConnected] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected')
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const [messageQueue, setMessageQueue] = useState<WebSocketMessage[]>([])

  /**
   * 生成客户端ID
   */
  const getClientId = useCallback(() => {
    let clientId = localStorage.getItem('ws_client_id')
    if (!clientId) {
      clientId = `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
      localStorage.setItem('ws_client_id', clientId)
    }
    return clientId
  }, [])

  /**
   * 连接 WebSocket
   */
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected')
      return
    }

    try {
      setConnectionStatus('connecting')
      const clientId = getClientId()
      const wsUrl = `${url}/${clientId}`
      
      console.log('Connecting to WebSocket:', wsUrl)
      const ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        console.log('WebSocket connected')
        setIsConnected(true)
        setConnectionStatus('connected')
        reconnectAttemptsRef.current = 0
        
        // 发送队列中的消息
        if (messageQueue.length > 0) {
          messageQueue.forEach(msg => {
            ws.send(JSON.stringify(msg))
          })
          setMessageQueue([])
        }
      }

      ws.onmessage = (event) => {
        try {
          const raw = JSON.parse(event.data)
          console.log('WebSocket message received:', raw)
          
          const message: WebSocketMessage = raw.type
            ? raw
            : { type: raw.type || 'unknown', data: raw, timestamp: new Date().toISOString() }
          
          setLastMessage(message)
          
          const subscribers = subscribersRef.current.get(message.type)
          if (subscribers) {
            subscribers.forEach(callback => {
              try {
                callback(message.data)
              } catch (error) {
                console.error('Error in WebSocket subscriber callback:', error)
              }
            })
          }
          
          const allSubscribers = subscribersRef.current.get('*')
          if (allSubscribers) {
            allSubscribers.forEach(callback => {
              try {
                callback(message)
              } catch (error) {
                console.error('Error in WebSocket wildcard subscriber callback:', error)
              }
            })
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        setConnectionStatus('error')
        message.error('WebSocket 连接错误')
      }

      ws.onclose = () => {
        console.log('WebSocket disconnected')
        setIsConnected(false)
        setConnectionStatus('disconnected')
        wsRef.current = null

        // 自动重连
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++
          console.log(`Reconnecting WebSocket (attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts})...`)
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, reconnectInterval)
        } else {
          console.error('Max reconnection attempts reached')
          message.error('WebSocket 连接失败，已达到最大重连次数')
        }
      }

      wsRef.current = ws
    } catch (error) {
      console.error('Failed to create WebSocket:', error)
      setConnectionStatus('error')
    }
  }, [url, messageQueue, reconnectInterval, maxReconnectAttempts, getClientId])

  /**
   * 断开 WebSocket
   */
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    
    if (wsRef.current) {
      // 设置最大重连次数，防止自动重连
      reconnectAttemptsRef.current = maxReconnectAttempts
      wsRef.current.close()
      wsRef.current = null
    }
    
    setIsConnected(false)
    setConnectionStatus('disconnected')
  }, [maxReconnectAttempts])

  /**
   * 发送消息
   */
  const sendMessage = useCallback((type: string, data: any) => {
    const message: WebSocketMessage = {
      type,
      data,
      timestamp: new Date().toISOString(),
    }

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket is not connected, message queued')
      // 将消息加入队列
      setMessageQueue(prev => [...prev, message])
    }
  }, [])

  /**
   * 订阅特定类型的消息
   * 返回取消订阅的函数
   */
  const subscribe = useCallback((type: string, callback: (data: any) => void) => {
    if (!subscribersRef.current.has(type)) {
      subscribersRef.current.set(type, new Set())
    }
    
    const subscribers = subscribersRef.current.get(type)!
    subscribers.add(callback)
    
    // 返回取消订阅函数
    return () => {
      subscribers.delete(callback)
      if (subscribers.size === 0) {
        subscribersRef.current.delete(type)
      }
    }
  }, [])

  /**
   * 清除消息队列
   */
  const clearMessageQueue = useCallback(() => {
    setMessageQueue([])
  }, [])

  // 自动连接
  useEffect(() => {
    if (autoConnect) {
      connect()
    }

    return () => {
      disconnect()
    }
  }, [autoConnect])

  const value: WebSocketContextType = {
    isConnected,
    connectionStatus,
    lastMessage,
    messageQueue,
    sendMessage,
    subscribe,
    connect,
    disconnect,
    clearMessageQueue,
  }

  return <WebSocketContext.Provider value={value}>{children}</WebSocketContext.Provider>
}

/**
 * 使用 WebSocket Context 的 Hook
 */
export const useWebSocketContext = (): WebSocketContextType => {
  const context = useContext(WebSocketContext)
  if (context === undefined) {
    throw new Error('useWebSocketContext must be used within a WebSocketProvider')
  }
  return context
}
