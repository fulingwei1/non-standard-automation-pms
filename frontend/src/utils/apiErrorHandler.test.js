import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import {
  ErrorTypes,
  shouldUseMockData,
  shouldRelogin,
  isNetworkError,
  getErrorMessage,
  getLogLevel,
  LogLevel,
  logApiError,
  handleApiError,
} from "./apiErrorHandler";

describe("apiErrorHandler", () => {
  describe("ErrorTypes", () => {
    it("should define all error types", () => {
      expect(ErrorTypes.BAD_REQUEST).toBe(400);
      expect(ErrorTypes.UNAUTHORIZED).toBe(401);
      expect(ErrorTypes.FORBIDDEN).toBe(403);
      expect(ErrorTypes.NOT_FOUND).toBe(404);
      expect(ErrorTypes.UNPROCESSABLE).toBe(422);
      expect(ErrorTypes.TOO_MANY_REQUESTS).toBe(429);
      expect(ErrorTypes.INTERNAL_ERROR).toBe(500);
      expect(ErrorTypes.BAD_GATEWAY).toBe(502);
      expect(ErrorTypes.SERVICE_UNAVAILABLE).toBe(503);
      expect(ErrorTypes.GATEWAY_TIMEOUT).toBe(504);
      expect(ErrorTypes.NETWORK_ERROR).toBe(0);
      expect(ErrorTypes.TIMEOUT).toBe("ETIMEDOUT");
    });
  });

  describe("shouldUseMockData", () => {
    it("should return false for null/undefined error", () => {
      expect(shouldUseMockData(null)).toBe(false);
      expect(shouldUseMockData(undefined)).toBe(false);
    });

    it("should return false for error without response", () => {
      const error = { request: {} };
      expect(shouldUseMockData(error)).toBe(false);
    });

    it("should return true for 404 errors", () => {
      const error = { response: { status: 404 } };
      expect(shouldUseMockData(error)).toBe(true);
    });

    it("should return true for 422 errors", () => {
      const error = { response: { status: 422 } };
      expect(shouldUseMockData(error)).toBe(true);
    });

    it("should return true for 500 errors", () => {
      const error = { response: { status: 500 } };
      expect(shouldUseMockData(error)).toBe(true);
    });

    it("should return false for other status codes", () => {
      expect(shouldUseMockData({ response: { status: 401 } })).toBe(false);
      expect(shouldUseMockData({ response: { status: 403 } })).toBe(false);
      expect(shouldUseMockData({ response: { status: 502 } })).toBe(false);
    });
  });

  describe("shouldRelogin", () => {
    it("should return false for null/undefined error", () => {
      expect(shouldRelogin(null)).toBe(false);
      expect(shouldRelogin(undefined)).toBe(false);
    });

    it("should return false for error without response", () => {
      const error = { request: {} };
      expect(shouldRelogin(error)).toBe(false);
    });

    it("should return true for 401 errors", () => {
      const error = { response: { status: 401 } };
      expect(shouldRelogin(error)).toBe(true);
    });

    it("should return false for other status codes", () => {
      expect(shouldRelogin({ response: { status: 400 } })).toBe(false);
      expect(shouldRelogin({ response: { status: 403 } })).toBe(false);
      expect(shouldRelogin({ response: { status: 500 } })).toBe(false);
    });
  });

  describe("isNetworkError", () => {
    it("should return false for null/undefined error", () => {
      expect(isNetworkError(null)).toBe(false);
      expect(isNetworkError(undefined)).toBe(false);
    });

    it("should return true for network errors (no response, has request)", () => {
      const error = { request: {} };
      expect(isNetworkError(error)).toBe(true);
    });

    it("should return false for errors with response", () => {
      const error = { response: { status: 500 }, request: {} };
      expect(isNetworkError(error)).toBe(false);
    });

    it("should return false for errors without request", () => {
      const error = { message: "Something went wrong" };
      expect(isNetworkError(error)).toBe(false);
    });
  });

  describe("getErrorMessage", () => {
    it("should return default message for null/undefined error", () => {
      expect(getErrorMessage(null)).toBe("操作失败，请稍后重试");
      expect(getErrorMessage(undefined)).toBe("操作失败，请稍后重试");
    });

    it("should use custom context in default message", () => {
      expect(getErrorMessage(null, "登录")).toBe("登录失败，请稍后重试");
    });

    it("should return message for 400 error", () => {
      const error = { response: { status: 400 } };
      expect(getErrorMessage(error)).toBe("请求参数有误，请检查输入");
    });

    it("should return detail message when available", () => {
      const error = { response: { status: 400, data: { detail: "参数错误" } } };
      expect(getErrorMessage(error)).toBe("参数错误");
    });

    it("should return message from data.message", () => {
      const error = { response: { status: 400, data: { message: "错误消息" } } };
      expect(getErrorMessage(error)).toBe("错误消息");
    });

    it("should return message for 401 error", () => {
      const error = { response: { status: 401 } };
      expect(getErrorMessage(error)).toBe("登录已过期，请重新登录");
    });

    it("should return message for 403 error", () => {
      const error = { response: { status: 403 } };
      expect(getErrorMessage(error)).toBe("您没有权限执行此操作");
    });

    it("should return message for 404 error", () => {
      const error = { response: { status: 404 } };
      expect(getErrorMessage(error)).toBe("请求的资源不存在");
    });

    it("should return message for 422 error", () => {
      const error = { response: { status: 422 } };
      expect(getErrorMessage(error)).toBe("数据格式验证失败");
    });

    it("should return message for 429 error", () => {
      const error = { response: { status: 429 } };
      expect(getErrorMessage(error)).toBe("请求过于频繁，请稍后再试");
    });

    it("should return message for 500 error", () => {
      const error = { response: { status: 500 } };
      expect(getErrorMessage(error)).toBe("服务器出错，我们正在处理中");
    });

    it("should return message for 502 error", () => {
      const error = { response: { status: 502 } };
      expect(getErrorMessage(error)).toBe("服务暂时不可用，请稍后重试");
    });

    it("should return message for 503 error", () => {
      const error = { response: { status: 503 } };
      expect(getErrorMessage(error)).toBe("服务暂时不可用，请稍后重试");
    });

    it("should return message for 504 error", () => {
      const error = { response: { status: 504 } };
      expect(getErrorMessage(error)).toBe("请求超时，请稍后重试");
    });

    it("should return network error message", () => {
      const error = { request: {} };
      expect(getErrorMessage(error)).toBe("网络连接失败，请检查网络");
    });

    it("should return detail for unknown status codes", () => {
      const error = { response: { status: 418, data: { detail: "I'm a teapot" } } };
      expect(getErrorMessage(error)).toBe("I'm a teapot");
    });

    it("should return default message for unknown status codes without detail", () => {
      const error = { response: { status: 418 } };
      expect(getErrorMessage(error)).toBe("操作失败，请稍后重试");
    });
  });

  describe("getLogLevel", () => {
    it("should return ERROR for null/undefined", () => {
      expect(getLogLevel(null)).toBe(LogLevel.ERROR);
      expect(getLogLevel(undefined)).toBe(LogLevel.ERROR);
    });

    it("should return DEBUG for mockable errors", () => {
      expect(getLogLevel({ response: { status: 404 } })).toBe(LogLevel.DEBUG);
      expect(getLogLevel({ response: { status: 422 } })).toBe(LogLevel.DEBUG);
      expect(getLogLevel({ response: { status: 500 } })).toBe(LogLevel.DEBUG);
    });

    it("should return WARN for 4xx errors", () => {
      expect(getLogLevel({ response: { status: 400 } })).toBe(LogLevel.WARN);
      expect(getLogLevel({ response: { status: 401 } })).toBe(LogLevel.WARN);
      expect(getLogLevel({ response: { status: 403 } })).toBe(LogLevel.WARN);
      expect(getLogLevel({ response: { status: 429 } })).toBe(LogLevel.WARN);
    });

    it("should return ERROR for 5xx errors (non-mockable)", () => {
      expect(getLogLevel({ response: { status: 502 } })).toBe(LogLevel.ERROR);
      expect(getLogLevel({ response: { status: 503 } })).toBe(LogLevel.ERROR);
      expect(getLogLevel({ response: { status: 504 } })).toBe(LogLevel.ERROR);
    });

    it("should return ERROR for network errors", () => {
      const error = { request: {} };
      expect(getLogLevel(error)).toBe(LogLevel.ERROR);
    });

    it("should return INFO for other cases", () => {
      const error = { response: { status: 200 } };
      expect(getLogLevel(error)).toBe(LogLevel.INFO);
    });
  });

  describe("logApiError", () => {
    let consoleDebugSpy, consoleInfoSpy, consoleWarnSpy, consoleErrorSpy;

    beforeEach(() => {
      consoleDebugSpy = vi.spyOn(console, "debug").mockImplementation(() => {});
      consoleInfoSpy = vi.spyOn(console, "info").mockImplementation(() => {});
      consoleWarnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});
      consoleErrorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    });

    afterEach(() => {
      consoleDebugSpy.mockRestore();
      consoleInfoSpy.mockRestore();
      consoleWarnSpy.mockRestore();
      consoleErrorSpy.mockRestore();
    });

    it("should log DEBUG level in DEV mode for mockable errors", () => {
      const error = { response: { status: 404 } };
      logApiError(error, "测试");
      // DEBUG only logs in DEV mode
      if (import.meta.env.DEV) {
        expect(consoleDebugSpy).toHaveBeenCalled();
      }
    });

    it("should log INFO level", () => {
      const error = { response: { status: 200 } };
      logApiError(error, "测试");
      expect(consoleInfoSpy).toHaveBeenCalledWith(
        "[API] 测试:",
        "测试失败,请稍后重试"
      );
    });

    it("should log WARN level", () => {
      const error = { response: { status: 400 } };
      logApiError(error, "测试");
      expect(consoleWarnSpy).toHaveBeenCalledWith(
        "[API] 测试:",
        "请求参数有误，请检查输入"
      );
    });

    it("should log ERROR level", () => {
      const error = { request: {} };
      logApiError(error, "测试");
      expect(consoleErrorSpy).toHaveBeenCalledWith("[API] 测试:", error);
    });
  });

  describe("handleApiError", () => {
    let consoleErrorSpy;
    let originalLocalStorage;
    let originalLocation;

    beforeEach(() => {
      consoleErrorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
      
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
      consoleErrorSpy.mockRestore();
      global.localStorage = originalLocalStorage;
      window.location = originalLocation;
    });

    it("should handle 401 error and redirect to login", () => {
      const error = { response: { status: 401 } };
      const result = handleApiError(error);
      
      expect(localStorage.removeItem).toHaveBeenCalledWith("token");
      expect(localStorage.removeItem).toHaveBeenCalledWith("user");
      expect(window.location.href).toBe("/login");
      expect(result.shouldRelogin).toBe(true);
      expect(result.useMockData).toBe(false);
    });

    it("should return useMockData true for mockable errors", () => {
      const error = { response: { status: 404 } };
      const result = handleApiError(error);
      
      expect(result.useMockData).toBe(true);
      expect(result.shouldRelogin).toBe(false);
      expect(result.message).toBe("请求的资源不存在");
    });

    it("should return useMockData false for non-mockable errors", () => {
      const error = { response: { status: 403 } };
      const result = handleApiError(error);
      
      expect(result.useMockData).toBe(false);
      expect(result.shouldRelogin).toBe(false);
      expect(result.message).toBe("您没有权限执行此操作");
    });

    it("should handle network errors", () => {
      const error = { request: {} };
      const result = handleApiError(error);
      
      expect(result.useMockData).toBe(false);
      expect(result.shouldRelogin).toBe(false);
      expect(result.message).toBe("网络连接失败，请检查网络");
    });

    it("should use custom context", () => {
      const error = { response: { status: 500 } };
      const result = handleApiError(error, "保存数据");
      
      expect(result.message).toBe("服务器出错，我们正在处理中");
    });
  });
});
