/**
 * 错误处理工具测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  parseError,
  getErrorCode,
  getErrorMessage,
  getUserFriendlyMessage,
  getErrorDetails,
  validateFileSize,
  validateFileFormat,
  validateUrl,
  validateFiles,
  ErrorType,
} from '../utils/errorHandler';

// Mock Ant Design message
vi.mock('antd', () => ({
  message: {
    error: vi.fn(),
    success: vi.fn(),
    warning: vi.fn(),
  },
  notification: {
    error: vi.fn(),
    success: vi.fn(),
    warning: vi.fn(),
  },
}));

describe('errorHandler', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('parseError', () => {
    it('should parse Axios error response', () => {
      const error = {
        response: {
          data: {
            error: {
              code: 'FILE_SIZE_EXCEEDED',
              message: '文件大小超过限制',
              details: { file_size: 6000000000 },
            },
          },
        },
      };

      const parsed = parseError(error);
      expect(parsed).toBeDefined();
      expect(parsed?.error.code).toBe('FILE_SIZE_EXCEEDED');
    });

    it('should parse direct error response', () => {
      const error = {
        error: {
          code: 'INVALID_URL',
          message: '无效的URL',
        },
      };

      const parsed = parseError(error);
      expect(parsed).toBeDefined();
      expect(parsed?.error.code).toBe('INVALID_URL');
    });

    it('should return null for invalid error', () => {
      const parsed = parseError(null);
      expect(parsed).toBeNull();
    });
  });

  describe('getErrorCode', () => {
    it('should get error code from parsed error', () => {
      const error = {
        response: {
          data: {
            error: {
              code: 'UNSUPPORTED_FORMAT',
              message: '不支持的格式',
            },
          },
        },
      };

      const code = getErrorCode(error);
      expect(code).toBe('UNSUPPORTED_FORMAT');
    });

    it('should return TIMEOUT_ERROR for timeout', () => {
      const error = { code: 'ECONNABORTED' };
      const code = getErrorCode(error);
      expect(code).toBe(ErrorType.TIMEOUT_ERROR);
    });

    it('should return NETWORK_ERROR for network error', () => {
      const error = { code: 'ERR_NETWORK' };
      const code = getErrorCode(error);
      expect(code).toBe(ErrorType.NETWORK_ERROR);
    });

    it('should map HTTP status codes', () => {
      expect(getErrorCode({ response: { status: 413 } })).toBe(ErrorType.FILE_SIZE_EXCEEDED);
      expect(getErrorCode({ response: { status: 415 } })).toBe(ErrorType.UNSUPPORTED_FORMAT);
      expect(getErrorCode({ response: { status: 400 } })).toBe(ErrorType.INVALID_URL);
      expect(getErrorCode({ response: { status: 401 } })).toBe(ErrorType.INVALID_TOKEN);
      expect(getErrorCode({ response: { status: 403 } })).toBe(ErrorType.UNAUTHORIZED_ACCESS);
      expect(getErrorCode({ response: { status: 404 } })).toBe(ErrorType.VIDEO_NOT_ACCESSIBLE);
      expect(getErrorCode({ response: { status: 500 } })).toBe(ErrorType.INTERNAL_SERVER_ERROR);
    });

    it('should return UNKNOWN_ERROR for unknown error', () => {
      const code = getErrorCode({});
      expect(code).toBe(ErrorType.UNKNOWN_ERROR);
    });
  });

  describe('getErrorMessage', () => {
    it('should get message from parsed error', () => {
      const error = {
        response: {
          data: {
            error: {
              code: 'FILE_SIZE_EXCEEDED',
              message: '文件大小超过限制（5GB）',
            },
          },
        },
      };

      const message = getErrorMessage(error);
      expect(message).toBe('文件大小超过限制（5GB）');
    });

    it('should get message from error code mapping', () => {
      const error = { response: { status: 415 } };
      const message = getErrorMessage(error);
      expect(message).toContain('不支持的视频格式');
    });
  });

  describe('getUserFriendlyMessage', () => {
    it('should return user-friendly message for known errors', () => {
      const error = { response: { status: 413 } };
      const message = getUserFriendlyMessage(error);
      expect(message).toContain('文件太大');
    });

    it('should fallback to error message for unknown errors', () => {
      const error = {
        response: {
          data: {
            error: {
              code: 'CUSTOM_ERROR',
              message: 'Custom error message',
            },
          },
        },
      };

      const message = getUserFriendlyMessage(error);
      expect(message).toBe('Custom error message');
    });
  });

  describe('getErrorDetails', () => {
    it('should get error details', () => {
      const error = {
        response: {
          data: {
            error: {
              code: 'FILE_SIZE_EXCEEDED',
              message: '文件大小超过限制',
              details: {
                file_size: 6000000000,
                max_size: 5000000000,
                file_name: 'test.mp4',
              },
            },
          },
        },
      };

      const details = getErrorDetails(error);
      expect(details).toBeDefined();
      expect(details?.file_size).toBe(6000000000);
      expect(details?.file_name).toBe('test.mp4');
    });

    it('should return undefined for no details', () => {
      const details = getErrorDetails({});
      expect(details).toBeUndefined();
    });
  });

  describe('validateFileSize', () => {
    it('should validate file size within limit', () => {
      const file = new File([''], 'test.mp4', { type: 'video/mp4' });
      Object.defineProperty(file, 'size', { value: 4.5 * 1024 * 1024 * 1024 });

      const result = validateFileSize(file, 5);
      expect(result).toBe(true);
    });

    it('should reject file size exceeding limit', () => {
      const file = new File([''], 'test.mp4', { type: 'video/mp4' });
      Object.defineProperty(file, 'size', { value: 5.5 * 1024 * 1024 * 1024 });

      const result = validateFileSize(file, 5);
      expect(result).toBe(false);
    });
  });

  describe('validateFileFormat', () => {
    it('should validate supported formats', () => {
      const mp4File = new File([''], 'test.mp4', { type: 'video/mp4' });
      expect(validateFileFormat(mp4File)).toBe(true);

      const aviFile = new File([''], 'test.avi', { type: 'video/x-msvideo' });
      expect(validateFileFormat(aviFile)).toBe(true);

      const movFile = new File([''], 'test.mov', { type: 'video/quicktime' });
      expect(validateFileFormat(movFile)).toBe(true);

      const mkvFile = new File([''], 'test.mkv', { type: 'video/x-matroska' });
      expect(validateFileFormat(mkvFile)).toBe(true);
    });

    it('should reject unsupported formats', () => {
      const wmvFile = new File([''], 'test.wmv', { type: 'video/x-ms-wmv' });
      expect(validateFileFormat(wmvFile)).toBe(false);
    });

    it('should reject files without extension', () => {
      const noExtFile = new File([''], 'test', { type: 'video/mp4' });
      expect(validateFileFormat(noExtFile)).toBe(false);
    });
  });

  describe('validateUrl', () => {
    it('should validate valid URLs', () => {
      expect(validateUrl('https://www.youtube.com/watch?v=dQw4w9WgXcQ')).toBe(true);
      expect(validateUrl('http://example.com/video.mp4')).toBe(true);
    });

    it('should reject empty URL', () => {
      expect(validateUrl('')).toBe(false);
      expect(validateUrl('   ')).toBe(false);
    });

    it('should reject URL without protocol', () => {
      expect(validateUrl('www.example.com/video.mp4')).toBe(false);
    });

    it('should reject URL with spaces', () => {
      expect(validateUrl('https://example.com/video file.mp4')).toBe(false);
    });

    it('should reject too long URL', () => {
      const longUrl = 'https://example.com/' + 'a'.repeat(2100);
      expect(validateUrl(longUrl)).toBe(false);
    });
  });

  describe('validateFiles', () => {
    it('should validate valid files', () => {
      const files = [
        new File([''], 'test1.mp4', { type: 'video/mp4' }),
        new File([''], 'test2.avi', { type: 'video/x-msvideo' }),
      ];

      // Set file sizes
      Object.defineProperty(files[0], 'size', { value: 1024 * 1024 * 1024 }); // 1GB
      Object.defineProperty(files[1], 'size', { value: 2 * 1024 * 1024 * 1024 }); // 2GB

      const result = validateFiles(files);
      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('should reject too many files', () => {
      const files = Array.from({ length: 51 }, (_, i) =>
        new File([''], `test${i}.mp4`, { type: 'video/mp4' })
      );

      const result = validateFiles(files, 50);
      expect(result.valid).toBe(false);
      expect(result.errors.length).toBeGreaterThan(0);
      expect(result.errors[0]).toContain('最多只能上传');
    });

    it('should collect errors for invalid files', () => {
      const files = [
        new File([''], 'test1.mp4', { type: 'video/mp4' }),
        new File([''], 'test2.wmv', { type: 'video/x-ms-wmv' }), // Invalid format
      ];

      // Set file sizes
      Object.defineProperty(files[0], 'size', { value: 6 * 1024 * 1024 * 1024 }); // 6GB - too large
      Object.defineProperty(files[1], 'size', { value: 1024 * 1024 * 1024 }); // 1GB

      const result = validateFiles(files);
      expect(result.valid).toBe(false);
      expect(result.errors.length).toBeGreaterThan(0);
    });
  });
});
