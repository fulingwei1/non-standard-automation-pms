import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import {
  getErrorMessage,
  isNetworkError,
  isAuthError,
  isPermissionError,
  isValidationError,
  getValidationErrors,
  handleApiError,
} from "./errorHandler";

describe("errorHandler", () => {
  describe("getErrorMessage", () => {
    it("should return default message for null/undefined", () => {
      expect(getErrorMessage(null)).toBe("未知错误");
      expect(getErrorMessage(undefined)).toBe("未知错误");
    });

    it("should extract detail from error response", () => {
      const error = {
        response: {
          status: 400,
          data: { detail: "参数错误" },
        },
      };
      expect(getErrorMessage(error)).toBe("参数错误");
    });

    it("should extract message from error response", () => {
      const error = {
        response: {
          status: 400,
          data: { message: "错误消息" },
        },
      };
      expect(getErrorMessage(error)).toBe("错误消息");
    });

    it("should prefer detail over message", () => {
      const error = {
        response: {
          status: 400,
          data: { detail: "详细错误", message: "错误消息" },
        },
      };
      expect(getErrorMessage(error)).toBe("详细错误");
    });

    it("should return appropriate message for 400 error", () => {
      const error = { response: { status: 400, data: {} } };
      expect(getErrorMessage(error)).toBe("请求参数错误");
    });

    it("should return appropriate message for 401 error", () => {
      const error = { response: { status: 401, data: {} } };
      expect(getErrorMessage(error)).toBe("未授权，请重新登录");
    });

    it("should return appropriate message for 403 error", () => {
      const error = { response: { status: 403, data: {} } };
      expect(getErrorMessage(error)).toBe("没有权限访问此资源");
    });

    it("should return appropriate message for 404 error", () => {
      const error = { response: { status: 404, data: {} } };
      expect(getErrorMessage(error)).toBe("请求的资源不存在");
    });

    it("should return appropriate message for 409 error", () => {
      const error = { response: { status: 409, data: {} } };
      expect(getErrorMessage(error)).toBe("资源冲突");
    });

    it("should return appropriate message for 422 error", () => {
      const error = { response: { status: 422, data: {} } };
      expect(getErrorMessage(error)).toBe("数据验证失败");
    });

    it("should return appropriate message for 500 error", () => {
      const error = { response: { status: 500, data: {} } };
      expect(getErrorMessage(error)).toBe("服务器内部错误");
    });

    it("should return appropriate message for 502 error", () => {
      const error = { response: { status: 502, data: {} } };
      expect(getErrorMessage(error)).toBe("网关错误");
    });

    it("should return appropriate message for 503 error", () => {
      const error = { response: { status: 503, data: {} } };
      expect(getErrorMessage(error)).toBe("服务暂时不可用");
    });

    it("should return appropriate message for 504 error", () => {
      const error = { response: { status: 504, data: {} } };
      expect(getErrorMessage(error)).toBe("网关超时");
    });

    it("should return generic message for unknown status codes", () => {
      const error = { response: { status: 418, data: {} } };
      expect(getErrorMessage(error)).toBe("请求失败 (418)");
    });

    it("should return network error message", () => {
      const error = { request: {} };
      expect(getErrorMessage(error)).toBe("网络连接失败，请检查网络设置");
    });

    it("should return error message from Error object", () => {
      const error = new Error("Something went wrong");
      expect(getErrorMessage(error)).toBe("Something went wrong");
    });

    it("should return 未知错误 for empty error object", () => {
      const error = {};
      expect(getErrorMessage(error)).toBe("未知错误");
    });
  });

  describe("isNetworkError", () => {
    it("should return true for network errors", () => {
      const error = { request: {} };
      expect(isNetworkError(error)).toBe(true);
    });

    it("should return false for errors with response", () => {
      const error = { response: { status: 500 }, request: {} };
      expect(isNetworkError(error)).toBe(false);
    });

    it("should return false for errors without request", () => {
      const error = { message: "Error" };
      expect(isNetworkError(error)).toBe(false);
    });

    it("should return false for null/undefined", () => {
      expect(isNetworkError(null)).toBe(false);
      expect(isNetworkError(undefined)).toBe(false);
    });
  });

  describe("isAuthError", () => {
    it("should return true for 401 errors", () => {
      const error = { response: { status: 401 } };
      expect(isAuthError(error)).toBe(true);
    });

    it("should return false for other status codes", () => {
      expect(isAuthError({ response: { status: 400 } })).toBe(false);
      expect(isAuthError({ response: { status: 403 } })).toBe(false);
      expect(isAuthError({ response: { status: 500 } })).toBe(false);
    });

    it("should return false for errors without response", () => {
      expect(isAuthError({ request: {} })).toBe(false);
    });

    it("should return false for null/undefined", () => {
      expect(isAuthError(null)).toBe(false);
      expect(isAuthError(undefined)).toBe(false);
    });
  });

  describe("isPermissionError", () => {
    it("should return true for 403 errors", () => {
      const error = { response: { status: 403 } };
      expect(isPermissionError(error)).toBe(true);
    });

    it("should return false for other status codes", () => {
      expect(isPermissionError({ response: { status: 400 } })).toBe(false);
      expect(isPermissionError({ response: { status: 401 } })).toBe(false);
      expect(isPermissionError({ response: { status: 500 } })).toBe(false);
    });

    it("should return false for errors without response", () => {
      expect(isPermissionError({ request: {} })).toBe(false);
    });

    it("should return false for null/undefined", () => {
      expect(isPermissionError(null)).toBe(false);
      expect(isPermissionError(undefined)).toBe(false);
    });
  });

  describe("isValidationError", () => {
    it("should return true for 400 errors", () => {
      const error = { response: { status: 400 } };
      expect(isValidationError(error)).toBe(true);
    });

    it("should return true for 422 errors", () => {
      const error = { response: { status: 422 } };
      expect(isValidationError(error)).toBe(true);
    });

    it("should return false for other status codes", () => {
      expect(isValidationError({ response: { status: 401 } })).toBe(false);
      expect(isValidationError({ response: { status: 403 } })).toBe(false);
      expect(isValidationError({ response: { status: 500 } })).toBe(false);
    });

    it("should return false for errors without response", () => {
      expect(isValidationError({ request: {} })).toBe(false);
    });

    it("should return false for null/undefined", () => {
      expect(isValidationError(null)).toBe(false);
      expect(isValidationError(undefined)).toBe(false);
    });
  });

  describe("getValidationErrors", () => {
    it("should return empty object for non-validation errors", () => {
      const error = { response: { status: 500 } };
      expect(getValidationErrors(error)).toEqual({});
    });

    it("should extract errors object", () => {
      const error = {
        response: {
          status: 400,
          data: {
            errors: { name: "名称不能为空", age: "年龄必须大于0" },
          },
        },
      };
      expect(getValidationErrors(error)).toEqual({
        name: "名称不能为空",
        age: "年龄必须大于0",
      });
    });

    it("should extract detail object", () => {
      const error = {
        response: {
          status: 422,
          data: {
            detail: { email: "邮箱格式不正确" },
          },
        },
      };
      expect(getValidationErrors(error)).toEqual({
        email: "邮箱格式不正确",
      });
    });

    it("should prefer errors over detail", () => {
      const error = {
        response: {
          status: 400,
          data: {
            errors: { name: "名称错误" },
            detail: { email: "邮箱错误" },
          },
        },
      };
      expect(getValidationErrors(error)).toEqual({
        name: "名称错误",
      });
    });

    it("should return empty object if detail is not an object", () => {
      const error = {
        response: {
          status: 400,
          data: {
            detail: "参数错误",
          },
        },
      };
      expect(getValidationErrors(error)).toEqual({});
    });

    it("should return empty object for null/undefined", () => {
      expect(getValidationErrors(null)).toEqual({});
      expect(getValidationErrors(undefined)).toEqual({});
    });
  });

  describe("handleApiError", () => {
    let consoleWarnSpy, consoleLogSpy;
    let originalLocalStorage, originalLocation;

    beforeEach(() => {
      consoleWarnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});
      consoleLogSpy = vi.spyOn(console, "log").mockImplementation(() => {});

      // Mock localStorage
      originalLocalStorage = global.localStorage;
      global.localStorage = {
        removeItem: vi.fn(),
        getItem: vi.fn(),
        setItem: vi.fn(),
        clear: vi.fn(),
      };

      // Mock window.location
      originalLocation = window.location;
      delete window.location;
      window.location = { href: "" };
    });

    afterEach(() => {
      consoleWarnSpy.mockRestore();
      consoleLogSpy.mockRestore();
      global.localStorage = originalLocalStorage;
      window.location = originalLocation;
    });

    it("should handle auth error with default behavior", () => {
      const error = { response: { status: 401 } };
      global.localStorage.getItem.mockReturnValue(null);
      
      handleApiError(error);

      expect(localStorage.removeItem).toHaveBeenCalledWith("token");
      expect(localStorage.removeItem).toHaveBeenCalledWith("user");
      expect(window.location.href).toBe("/");
    });

    it("should call custom onAuthError callback", () => {
      const error = { response: { status: 401 } };
      const onAuthError = vi.fn();
      global.localStorage.getItem.mockReturnValue(null);

      handleApiError(error, { onAuthError });

      expect(onAuthError).toHaveBeenCalledWith(error);
      expect(localStorage.removeItem).not.toHaveBeenCalled();
    });

    it("should not redirect for demo account 401 errors", () => {
      const error = { response: { status: 401 } };
      global.localStorage.getItem.mockReturnValue("demo_token_abc123");

      handleApiError(error);

      expect(localStorage.removeItem).not.toHaveBeenCalled();
      expect(window.location.href).toBe("");
      expect(consoleLogSpy).toHaveBeenCalledWith(
        "演示账号 API 调用失败，将使用 mock 数据"
      );
    });

    it("should handle permission error with default behavior", () => {
      const error = { response: { status: 403 } };
      handleApiError(error);

      expect(consoleWarnSpy).toHaveBeenCalledWith(
        "Permission denied:",
        "没有权限访问此资源"
      );
    });

    it("should call custom onPermissionError callback", () => {
      const error = { response: { status: 403 } };
      const onPermissionError = vi.fn();

      handleApiError(error, { onPermissionError });

      expect(onPermissionError).toHaveBeenCalledWith(error);
      expect(consoleWarnSpy).not.toHaveBeenCalled();
    });

    it("should handle network error", () => {
      const error = { request: {} };
      const onNetworkError = vi.fn();

      handleApiError(error, { onNetworkError });

      expect(onNetworkError).toHaveBeenCalledWith(error);
    });

    it("should handle validation error", () => {
      const error = {
        response: {
          status: 422,
          data: {
            errors: { name: "名称不能为空" },
          },
        },
      };
      const onValidationError = vi.fn();

      handleApiError(error, { onValidationError });

      expect(onValidationError).toHaveBeenCalledWith(error, {
        name: "名称不能为空",
      });
    });

    it("should handle other errors", () => {
      const error = { response: { status: 500 } };
      const onOtherError = vi.fn();

      handleApiError(error, { onOtherError });

      expect(onOtherError).toHaveBeenCalledWith(error);
    });

    it("should not call any callback if no error matches", () => {
      const error = { response: { status: 200 } };
      const callbacks = {
        onAuthError: vi.fn(),
        onPermissionError: vi.fn(),
        onNetworkError: vi.fn(),
        onValidationError: vi.fn(),
        onOtherError: vi.fn(),
      };

      handleApiError(error, callbacks);

      expect(callbacks.onAuthError).not.toHaveBeenCalled();
      expect(callbacks.onPermissionError).not.toHaveBeenCalled();
      expect(callbacks.onNetworkError).not.toHaveBeenCalled();
      expect(callbacks.onValidationError).not.toHaveBeenCalled();
      expect(callbacks.onOtherError).toHaveBeenCalled();
    });
  });
});
