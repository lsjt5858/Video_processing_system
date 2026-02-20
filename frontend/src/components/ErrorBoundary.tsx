/**
 * React错误边界组件
 * 
 * 捕获组件树中的JavaScript错误，记录错误并显示备用UI
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Result, Button } from 'antd';
import { logError } from '@/utils/errorHandler';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    // 更新state以便下次渲染显示备用UI
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // 记录错误到控制台
    logError(error, {
      componentStack: errorInfo.componentStack,
      errorBoundary: true,
    });

    // 更新state
    this.setState({
      errorInfo,
    });

    // 调用自定义错误处理器
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  handleReset = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  handleReload = (): void => {
    window.location.reload();
  };

  render(): ReactNode {
    if (this.state.hasError) {
      // 如果提供了自定义fallback，使用它
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // 默认错误UI
      return (
        <div style={{ padding: '50px', minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Result
            status="error"
            title="页面出错了"
            subTitle="抱歉，页面遇到了一些问题。您可以尝试刷新页面或返回首页。"
            extra={[
              <Button type="primary" key="reload" onClick={this.handleReload}>
                刷新页面
              </Button>,
              <Button key="reset" onClick={this.handleReset}>
                重试
              </Button>,
              <Button key="home" onClick={() => window.location.href = '/'}>
                返回首页
              </Button>,
            ]}
          >
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <div style={{ textAlign: 'left', marginTop: '20px' }}>
                <details style={{ whiteSpace: 'pre-wrap', fontSize: '12px' }}>
                  <summary style={{ cursor: 'pointer', marginBottom: '10px' }}>
                    <strong>错误详情（仅开发环境显示）</strong>
                  </summary>
                  <div style={{ background: '#f5f5f5', padding: '10px', borderRadius: '4px' }}>
                    <p><strong>错误消息:</strong></p>
                    <p style={{ color: '#ff4d4f' }}>{this.state.error.message}</p>
                    
                    <p><strong>错误堆栈:</strong></p>
                    <pre style={{ fontSize: '11px', overflow: 'auto' }}>
                      {this.state.error.stack}
                    </pre>
                    
                    {this.state.errorInfo && (
                      <>
                        <p><strong>组件堆栈:</strong></p>
                        <pre style={{ fontSize: '11px', overflow: 'auto' }}>
                          {this.state.errorInfo.componentStack}
                        </pre>
                      </>
                    )}
                  </div>
                </details>
              </div>
            )}
          </Result>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
