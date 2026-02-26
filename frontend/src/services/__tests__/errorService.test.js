/**
 * Error Service 测试
 * 测试范围：
 * - 错误类型定义
 * - 错误消息格式化
 * - 错误提示显示
 * - API错误处理
 * - 异步错误边界
 */

import { describe, it, expect, vi, beforeEach, _afterEach } from 'vitest';
import { message, Modal } from 'antd';
import * as errorService from '../errorService';

// Mock antd components
vi.mock('antd', () => ({
  message: {
    error: vi.fn(),
    success: vi.fn(),
    warning: vi.fn(),
    info: vi.fn(),
  },
  Modal: {
    error: vi.fn(),
  },
}));

describe('Error Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('ERROR_TYPES', () => {
    it('应该定义所有错误类型', () => {
      expect(errorService.ERROR_TYPES).toEqual({
        NETWORK: '网络错误',
        VALIDATION: '数据验证错误',
        AUTH: '认证错误',
        PERMISSION: '权限错误',
        NOT_FOUND: '资源未找到',
        SERVER: '服务器错误',
        UNKNOWN: '未知错误',
      });
    });

    it('错误类型应该是字符串', () => {
      Object.values(errorService.ERROR_TYPES).forEach((type) => {
        expect(typeof type).toBe('string');
      });
    });
  });

  describe('formatErrorMessage()', () => {
    it('应该正确格式化错误消息', () => {
      const result = errorService.formatErrorMessage('网络错误', '无法连接服务器');

      expect(result).toBe('[网络错误] 无法连接服务器');
    });

    it('应该处理空消息', () => {
      const result = errorService.formatErrorMessage('网络错误', '');

      expect(result).toBe('[网络错误] ');
    });

    it('应该处理特殊字符', () => {
      const result = errorService.formatErrorMessage(
        '服务器错误',
        '错误：系统崩溃 (500)'
      );

      expect(result).toBe('[服务器错误] 错误：系统崩溃 (500)');
    });
  });

  describe('showError()', () => {
    it('应该显示错误提示', () => {
      errorService.showError('测试错误');

      expect(message.error).toHaveBeenCalledWith('测试错误', 5);
    });

    it('应该支持自定义显示时长', () => {
      errorService.showError('测试错误', 10);

      expect(message.error).toHaveBeenCalledWith('测试错误', 10);
    });

    it('应该使用默认5秒时长', () => {
      errorService.showError('测试错误');

      expect(message.error).toHaveBeenCalledWith('测试错误', 5);
    });
  });

  describe('showSuccess()', () => {
    it('应该显示成功提示', () => {
      errorService.showSuccess('操作成功');

      expect(message.success).toHaveBeenCalledWith('操作成功', 3);
    });

    it('应该支持自定义显示时长', () => {
      errorService.showSuccess('操作成功', 5);

      expect(message.success).toHaveBeenCalledWith('操作成功', 5);
    });
  });

  describe('showWarning()', () => {
    it('应该显示警告提示', () => {
      errorService.showWarning('警告信息');

      expect(message.warning).toHaveBeenCalledWith('警告信息', 4);
    });

    it('应该支持自定义显示时长', () => {
      errorService.showWarning('警告信息', 6);

      expect(message.warning).toHaveBeenCalledWith('警告信息', 6);
    });
  });

  describe('showInfo()', () => {
    it('应该显示信息提示', () => {
      errorService.showInfo('提示信息');

      expect(message.info).toHaveBeenCalledWith('提示信息', 3);
    });

    it('应该支持自定义显示时长', () => {
      errorService.showInfo('提示信息', 8);

      expect(message.info).toHaveBeenCalledWith('提示信息', 8);
    });
  });

  describe('showErrorModal()', () => {
    it('应该显示错误弹窗', () => {
      const onOk = vi.fn();
      errorService.showErrorModal('错误', '发生严重错误', onOk);

      expect(Modal.error).toHaveBeenCalledWith({
        title: '错误',
        content: '发生严重错误',
        onOk,
      });
    });

    it('应该支持无回调', () => {
      errorService.showErrorModal('错误', '发生错误', undefined);

      expect(Modal.error).toHaveBeenCalledWith({
        title: '错误',
        content: '发生错误',
        onOk: undefined,
      });
    });
  });

  describe('handleApiError()', () => {
    it('应该处理null错误', () => {
      const result = errorService.handleApiError(null);

      expect(result).toBe('未知错误');
    });

    it('应该处理undefined错误', () => {
      const result = errorService.handleApiError(undefined);

      expect(result).toBe('未知错误');
    });

    it('应该处理401认证错误', () => {
      const error = {
        response: {
          status: 401,
          data: {},
        },
      };

      const result = errorService.handleApiError(error);

      expect(result).toContain('[认证错误]');
      expect(result).toContain('未授权，请重新登录');
    });

    it('应该处理403权限错误', () => {
      const error = {
        response: {
          status: 403,
          data: {},
        },
      };

      const result = errorService.handleApiError(error);

      expect(result).toContain('[权限错误]');
      expect(result).toContain('权限不足');
    });

    it('应该处理404资源未找到', () => {
      const error = {
        response: {
          status: 404,
          data: {},
        },
      };

      const result = errorService.handleApiError(error);

      expect(result).toContain('[资源未找到]');
      expect(result).toContain('资源未找到');
    });

    it('应该处理422验证错误', () => {
      const error = {
        response: {
          status: 422,
          data: {
            detail: '用户名已存在',
          },
        },
      };

      const result = errorService.handleApiError(error);

      expect(result).toContain('[数据验证错误]');
      expect(result).toContain('用户名已存在');
    });

    it('应该处理422验证错误（无detail）', () => {
      const error = {
        response: {
          status: 422,
          data: {},
        },
      };

      const result = errorService.handleApiError(error);

      expect(result).toContain('[数据验证错误]');
      expect(result).toContain('请求参数错误');
    });

    it('应该处理500服务器错误', () => {
      const error = {
        response: {
          status: 500,
          data: {},
        },
      };

      const result = errorService.handleApiError(error);

      expect(result).toContain('[服务器错误]');
      expect(result).toContain('服务器内部错误');
    });

    it('应该处理502/503服务器错误', () => {
      const error502 = {
        response: {
          status: 502,
          data: {},
        },
      };

      const result502 = errorService.handleApiError(error502);
      expect(result502).toContain('服务器内部错误');

      const error503 = {
        response: {
          status: 503,
          data: {},
        },
      };

      const result503 = errorService.handleApiError(error503);
      expect(result503).toContain('服务器内部错误');
    });

    it('应该优先使用响应中的message', () => {
      const error = {
        response: {
          status: 400,
          data: {
            message: '自定义错误消息',
          },
        },
      };

      const result = errorService.handleApiError(error);

      expect(result).toContain('[服务器错误]');
      expect(result).toContain('自定义错误消息');
    });

    it('应该处理无response的错误', () => {
      const error = {
        message: '网络连接失败',
      };

      const result = errorService.handleApiError(error);

      expect(result).toBe('网络连接失败');
    });

    it('应该处理完全未知的错误', () => {
      const error = {};

      const result = errorService.handleApiError(error);

      expect(result).toContain('[未知错误]');
      expect(result).toContain('发生未知错误');
    });
  });

  describe('withErrorHandling()', () => {
    it('应该成功执行回调', async () => {
      const callback = vi.fn().mockResolvedValue('success');
      const errorHandler = vi.fn();

      await errorService.withErrorHandling(callback, errorHandler);

      expect(callback).toHaveBeenCalled();
      expect(errorHandler).not.toHaveBeenCalled();
    });

    it('应该捕获并处理错误', async () => {
      const error = new Error('测试错误');
      const callback = vi.fn().mockRejectedValue(error);
      const errorHandler = vi.fn();

      await errorService.withErrorHandling(callback, errorHandler);

      expect(callback).toHaveBeenCalled();
      expect(errorHandler).toHaveBeenCalledWith('测试错误');
    });

    it('应该处理API错误', async () => {
      const error = {
        response: {
          status: 404,
          data: {},
        },
      };
      const callback = vi.fn().mockRejectedValue(error);
      const errorHandler = vi.fn();

      await errorService.withErrorHandling(callback, errorHandler);

      expect(errorHandler).toHaveBeenCalled();
      const errorMessage = errorHandler.mock.calls[0][0];
      expect(errorMessage).toContain('资源未找到');
    });

    it('应该处理异步回调', async () => {
      const callback = vi.fn(async () => {
        await new Promise((resolve) => setTimeout(resolve, 10));
        return 'success';
      });
      const errorHandler = vi.fn();

      await errorService.withErrorHandling(callback, errorHandler);

      expect(callback).toHaveBeenCalled();
      expect(errorHandler).not.toHaveBeenCalled();
    });

    it('应该处理异步回调中的错误', async () => {
      const callback = vi.fn(async () => {
        await new Promise((resolve) => setTimeout(resolve, 10));
        throw new Error('异步错误');
      });
      const errorHandler = vi.fn();

      await errorService.withErrorHandling(callback, errorHandler);

      expect(callback).toHaveBeenCalled();
      expect(errorHandler).toHaveBeenCalledWith('异步错误');
    });
  });

  describe('默认导出', () => {
    it('应该导出所有方法和常量', () => {
      expect(errorService.default).toEqual({
        ERROR_TYPES: errorService.ERROR_TYPES,
        formatErrorMessage: errorService.formatErrorMessage,
        showError: errorService.showError,
        showSuccess: errorService.showSuccess,
        showWarning: errorService.showWarning,
        showInfo: errorService.showInfo,
        showErrorModal: errorService.showErrorModal,
        handleApiError: errorService.handleApiError,
        withErrorHandling: errorService.withErrorHandling,
      });
    });
  });
});
