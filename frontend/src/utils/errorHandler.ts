/**
 * 错误处理工具模块
 * 
 * 提供统一的错误处理、错误消息显示和错误日志记录功能
 */

import { message, notification } from 'antd';
import type { AxiosError } from 'axios';

/**
 * 错误响应接口
 */
export interface ErrorResponse {
  error: {
    code: string;
    message: string;
    details?: Record<string, any>;
    timestamp?: string;
    request_id?: string;
  };
}

/**
 * 错误类型枚举
 */
export enum ErrorType {
  // 输入验证错误
  FILE_SIZE_EXCEEDED = 'FILE_SIZE_EXCEEDED',
  UNSUPPORTED_FORMAT = 'UNSUPPORTED_FORMAT',
  INVALID_URL = 'INVALID_URL',
  CORRUPTED_VIDEO = 'CORRUPTED_VIDEO',
  
  // 处理错误
  METADATA_EXTRACTION_ERROR = 'METADATA_EXTRACTION_ERROR',
  FRAME_EXTRACTION_ERROR = 'FRAME_EXTRACTION_ERROR',
  FFMPEG_ERROR = 'FFMPEG_ERROR',
  WATERMARK_REMOVAL_ERROR = 'WATERMARK_REMOVAL_ERROR',
  
  // 授权错误
  INVALID_TOKEN = 'INVALID_TOKEN',
  UNAUTHORIZED_ACCESS = 'UNAUTHORIZED_ACCESS',
  
  // 合规错误
  COPYRIGHT_NOT_CONFIRMED = 'COPYRIGHT_NOT_CONFIRMED',
  
  // 系统错误
  STORAGE_ERROR = 'STORAGE_ERROR',
  TASK_QUEUE_ERROR = 'TASK_QUEUE_ERROR',
  VIDEO_NOT_ACCESSIBLE = 'VIDEO_NOT_ACCESSIBLE',
  
  // 网络错误
  NETWORK_ERROR = 'NETWORK_ERROR',
  TIMEOUT_ERROR = 'TIMEOUT_ERROR',
  
  // 未知错误
  INTERNAL_SERVER_ERROR = 'INTERNAL_SERVER_ERROR',
  UNKNOWN_ERROR = 'UNKNOWN_ERROR',
}

/**
 * 错误消息映射
 */
const ERROR_MESSAGES: Record<string, string> = {
  // 输入验证错误
  [ErrorType.FILE_SIZE_EXCEEDED]: '文件大小超过限制（5GB）',
  [ErrorType.UNSUPPORTED_FORMAT]: '不支持的视频格式',
  [ErrorType.INVALID_URL]: '无效的视频链接',
  [ErrorType.CORRUPTED_VIDEO]: '视频文件损坏或格式不支持',
  
  // 处理错误
  [ErrorType.METADATA_EXTRACTION_ERROR]: '视频元数据提取失败',
  [ErrorType.FRAME_EXTRACTION_ERROR]: '视频帧提取失败',
  [ErrorType.FFMPEG_ERROR]: '视频处理失败',
  [ErrorType.WATERMARK_REMOVAL_ERROR]: '水印去除处理失败',
  
  // 授权错误
  [ErrorType.INVALID_TOKEN]: '授权令牌无效或已过期',
  [ErrorType.UNAUTHORIZED_ACCESS]: '无权访问该资源',
  
  // 合规错误
  [ErrorType.COPYRIGHT_NOT_CONFIRMED]: '版权声明未确认，无法处理视频',
  
  // 系统错误
  [ErrorType.STORAGE_ERROR]: '存储操作失败',
  [ErrorType.TASK_QUEUE_ERROR]: '任务队列处理失败',
  [ErrorType.VIDEO_NOT_ACCESSIBLE]: '视频不可访问',
  
  // 网络错误
  [ErrorType.NETWORK_ERROR]: '网络连接失败，请检查网络设置',
  [ErrorType.TIMEOUT_ERROR]: '请求超时，请稍后重试',
  
  // 未知错误
  [ErrorType.INTERNAL_SERVER_ERROR]: '服务器内部错误',
  [ErrorType.UNKNOWN_ERROR]: '未知错误，请稍后重试',
};

/**
 * 用户友好的错误提示
 */
const USER_FRIENDLY_MESSAGES: Record<string, string> = {
  [ErrorType.FILE_SIZE_EXCEEDED]: '您上传的文件太大了，请选择小于5GB的视频文件',
  [ErrorType.UNSUPPORTED_FORMAT]: '请上传MP4、AVI、MOV或MKV格式的视频文件',
  [ErrorType.INVALID_URL]: '请输入有效的视频链接（以http://或https://开头）',
  [ErrorType.CORRUPTED_VIDEO]: '视频文件可能已损坏，请尝试其他视频',
  [ErrorType.NETWORK_ERROR]: '网络连接失败，请检查您的网络连接后重试',
  [ErrorType.TIMEOUT_ERROR]: '操作超时，请检查网络连接后重试',
};

/**
 * 解析错误响应
 */
export function parseError(error: any): ErrorResponse | null {
  if (!error) return null;
  
  // Axios错误
  if (error.response?.data?.error) {
    return error.response.data as ErrorResponse;
  }
  
  // 直接的错误响应
  if (error.error) {
    return error as ErrorResponse;
  }
  
  return null;
}

/**
 * 获取错误代码
 */
export function getErrorCode(error: any): string {
  const parsedError = parseError(error);
  if (parsedError) {
    return parsedError.error.code;
  }
  
  // Axios错误
  if (error.code === 'ECONNABORTED' || error.code === 'ETIMEDOUT') {
    return ErrorType.TIMEOUT_ERROR;
  }
  
  if (error.code === 'ERR_NETWORK') {
    return ErrorType.NETWORK_ERROR;
  }
  
  // HTTP状态码
  if (error.response?.status) {
    const status = error.response.status;
    if (status === 413) return ErrorType.FILE_SIZE_EXCEEDED;
    if (status === 415) return ErrorType.UNSUPPORTED_FORMAT;
    if (status === 400) return ErrorType.INVALID_URL;
    if (status === 401) return ErrorType.INVALID_TOKEN;
    if (status === 403) return ErrorType.UNAUTHORIZED_ACCESS;
    if (status === 404) return ErrorType.VIDEO_NOT_ACCESSIBLE;
    if (status >= 500) return ErrorType.INTERNAL_SERVER_ERROR;
  }
  
  return ErrorType.UNKNOWN_ERROR;
}

/**
 * 获取错误消息
 */
export function getErrorMessage(error: any): string {
  const parsedError = parseError(error);
  
  // 使用服务器返回的消息
  if (parsedError?.error.message) {
    return parsedError.error.message;
  }
  
  // 使用错误代码映射的消息
  const errorCode = getErrorCode(error);
  return ERROR_MESSAGES[errorCode] || ERROR_MESSAGES[ErrorType.UNKNOWN_ERROR];
}

/**
 * 获取用户友好的错误消息
 */
export function getUserFriendlyMessage(error: any): string {
  const errorCode = getErrorCode(error);
  return USER_FRIENDLY_MESSAGES[errorCode] || getErrorMessage(error);
}

/**
 * 获取错误详情
 */
export function getErrorDetails(error: any): Record<string, any> | undefined {
  const parsedError = parseError(error);
  return parsedError?.error.details;
}

/**
 * 显示错误消息（使用Ant Design message）
 */
export function showErrorMessage(error: any, customMessage?: string): void {
  const errorMessage = customMessage || getUserFriendlyMessage(error);
  message.error(errorMessage);
}

/**
 * 显示错误通知（使用Ant Design notification）
 */
export function showErrorNotification(
  error: any,
  title?: string,
  customMessage?: string
): void {
  const errorCode = getErrorCode(error);
  const errorMessage = customMessage || getUserFriendlyMessage(error);
  const details = getErrorDetails(error);
  
  let description = errorMessage;
  
  // 添加详细信息
  if (details) {
    if (details.file_name) {
      description += `\n文件: ${details.file_name}`;
    }
    if (details.url) {
      description += `\nURL: ${details.url}`;
    }
    if (details.reason) {
      description += `\n原因: ${details.reason}`;
    }
  }
  
  notification.error({
    message: title || '操作失败',
    description,
    duration: 5,
  });
}

/**
 * 记录错误到控制台
 */
export function logError(error: any, context?: Record<string, any>): void {
  const errorCode = getErrorCode(error);
  const errorMessage = getErrorMessage(error);
  const details = getErrorDetails(error);
  
  console.error('[Error]', {
    code: errorCode,
    message: errorMessage,
    details,
    context,
    timestamp: new Date().toISOString(),
    originalError: error,
  });
}

/**
 * 处理API错误（综合处理）
 */
export function handleApiError(
  error: any,
  options?: {
    showMessage?: boolean;
    showNotification?: boolean;
    customMessage?: string;
    notificationTitle?: string;
    logToConsole?: boolean;
    context?: Record<string, any>;
  }
): void {
  const {
    showMessage: shouldShowMessage = true,
    showNotification: shouldShowNotification = false,
    customMessage,
    notificationTitle,
    logToConsole = true,
    context,
  } = options || {};
  
  // 记录错误
  if (logToConsole) {
    logError(error, context);
  }
  
  // 显示错误消息
  if (shouldShowMessage) {
    showErrorMessage(error, customMessage);
  }
  
  // 显示错误通知
  if (shouldShowNotification) {
    showErrorNotification(error, notificationTitle, customMessage);
  }
}

/**
 * 创建错误处理器（用于Promise catch）
 */
export function createErrorHandler(
  options?: Parameters<typeof handleApiError>[1]
) {
  return (error: any) => {
    handleApiError(error, options);
    throw error; // 重新抛出错误，以便调用者可以进一步处理
  };
}

/**
 * 验证文件大小
 */
export function validateFileSize(file: File, maxSizeGB: number = 5): boolean {
  const maxSizeBytes = maxSizeGB * 1024 * 1024 * 1024;
  if (file.size > maxSizeBytes) {
    showErrorMessage(
      { code: ErrorType.FILE_SIZE_EXCEEDED },
      `文件大小 ${(file.size / (1024 * 1024 * 1024)).toFixed(2)}GB 超过限制 ${maxSizeGB}GB`
    );
    return false;
  }
  return true;
}

/**
 * 验证文件格式
 */
export function validateFileFormat(
  file: File,
  supportedFormats: string[] = ['mp4', 'avi', 'mov', 'mkv']
): boolean {
  const fileExt = file.name.split('.').pop()?.toLowerCase();
  if (!fileExt || !supportedFormats.includes(fileExt)) {
    showErrorMessage(
      { code: ErrorType.UNSUPPORTED_FORMAT },
      `不支持的文件格式: ${fileExt}。支持的格式: ${supportedFormats.join(', ')}`
    );
    return false;
  }
  return true;
}

/**
 * 验证URL格式
 */
export function validateUrl(url: string): boolean {
  if (!url || !url.trim()) {
    showErrorMessage({ code: ErrorType.INVALID_URL }, 'URL不能为空');
    return false;
  }
  
  const trimmedUrl = url.trim();
  
  if (!trimmedUrl.startsWith('http://') && !trimmedUrl.startsWith('https://')) {
    showErrorMessage(
      { code: ErrorType.INVALID_URL },
      'URL必须以http://或https://开头'
    );
    return false;
  }
  
  if (trimmedUrl.length > 2048) {
    showErrorMessage({ code: ErrorType.INVALID_URL }, 'URL长度超过限制');
    return false;
  }
  
  if (trimmedUrl.includes(' ')) {
    showErrorMessage({ code: ErrorType.INVALID_URL }, 'URL不能包含空格');
    return false;
  }
  
  return true;
}

/**
 * 批量验证文件
 */
export function validateFiles(
  files: File[],
  maxCount: number = 50
): { valid: boolean; errors: string[] } {
  const errors: string[] = [];
  
  // 验证文件数量
  if (files.length > maxCount) {
    errors.push(`最多只能上传 ${maxCount} 个文件，当前选择了 ${files.length} 个`);
    return { valid: false, errors };
  }
  
  // 验证每个文件
  files.forEach((file, index) => {
    // 验证文件大小
    if (!validateFileSize(file)) {
      errors.push(`文件 ${index + 1} (${file.name}): 文件大小超过限制`);
    }
    
    // 验证文件格式
    if (!validateFileFormat(file)) {
      errors.push(`文件 ${index + 1} (${file.name}): 不支持的文件格式`);
    }
  });
  
  return {
    valid: errors.length === 0,
    errors,
  };
}

export default {
  parseError,
  getErrorCode,
  getErrorMessage,
  getUserFriendlyMessage,
  getErrorDetails,
  showErrorMessage,
  showErrorNotification,
  logError,
  handleApiError,
  createErrorHandler,
  validateFileSize,
  validateFileFormat,
  validateUrl,
  validateFiles,
};
