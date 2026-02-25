import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { diagnoseLogin } from "./diagnose";

describe("diagnose", () => {
  let consoleLogSpy,
    consoleWarnSpy,
    consoleErrorSpy;
  let fetchMock;
  let originalFetch;

  beforeEach(() => {
    consoleLogSpy = vi.spyOn(console, "log").mockImplementation(() => {});
    consoleWarnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});
    consoleErrorSpy = vi.spyOn(console, "error").mockImplementation(() => {});

    // Mock fetch
    originalFetch = global.fetch;
    fetchMock = vi.fn();
    global.fetch = fetchMock;

    // Mock setTimeout
    vi.useFakeTimers();
  });

  afterEach(() => {
    consoleLogSpy.mockRestore();
    consoleWarnSpy.mockRestore();
    consoleErrorSpy.mockRestore();
    global.fetch = originalFetch;
    vi.useRealTimers();
  });

  describe("diagnoseLogin", () => {
    it("should start diagnosis and log initial message", () => {
      fetchMock.mockResolvedValue({
        ok: true,
        status: 401,
        text: () => Promise.resolve("Unauthorized"),
      });

      diagnoseLogin();

      expect(consoleLogSpy).toHaveBeenCalledWith(
        "🔍 开始诊断登录问题...\n"
      );
    });

    it("should check backend service via /api/v1/projects/", () => {
      fetchMock.mockResolvedValue({
        ok: false,
        status: 401,
        text: () => Promise.resolve("Unauthorized"),
      });

      diagnoseLogin();

      expect(fetchMock).toHaveBeenCalledWith("/api/v1/projects/");
    });

    it("should handle 401 response as success (backend running)", async () => {
      fetchMock.mockResolvedValue({
        ok: false,
        status: 401,
        text: () => Promise.resolve("Unauthorized"),
      });

      diagnoseLogin();

      await vi.waitFor(() => {
        expect(consoleLogSpy).toHaveBeenCalledWith(
          "✅ 后端服务正常 (需要认证是预期的)"
        );
      });
    });

    it("should handle 422 response as success", async () => {
      fetchMock.mockResolvedValue({
        ok: false,
        status: 422,
        text: () => Promise.resolve("Unprocessable Entity"),
      });

      diagnoseLogin();

      await vi.waitFor(() => {
        expect(consoleLogSpy).toHaveBeenCalledWith(
          "✅ 后端服务正常 (需要认证是预期的)"
        );
      });
    });

    it("should handle 404 response with warning", async () => {
      fetchMock.mockResolvedValue({
        ok: false,
        status: 404,
        text: () => Promise.resolve("Not Found"),
      });

      diagnoseLogin();

      await vi.waitFor(() => {
        expect(consoleWarnSpy).toHaveBeenCalledWith(
          "⚠️ API路由可能未配置:",
          404,
          "Not Found"
        );
      });
    });

    it("should handle non-ok responses with error", async () => {
      fetchMock.mockResolvedValue({
        ok: false,
        status: 500,
        text: () => Promise.resolve("Internal Server Error"),
      });

      diagnoseLogin();

      await vi.waitFor(() => {
        expect(consoleErrorSpy).toHaveBeenCalledWith(
          "❌ 后端检查失败:",
          500,
          "Internal Server Error"
        );
      });
    });

    it("should handle successful JSON response", async () => {
      fetchMock.mockResolvedValue({
        ok: true,
        status: 200,
        text: () => Promise.resolve('{"status": "ok"}'),
      });

      diagnoseLogin();

      await vi.waitFor(() => {
        expect(consoleLogSpy).toHaveBeenCalledWith(
          "✅ 后端服务正常:",
          { status: "ok" }
        );
      });
    });

    it("should handle non-JSON response", async () => {
      fetchMock.mockResolvedValue({
        ok: true,
        status: 200,
        text: () => Promise.resolve("OK"),
      });

      diagnoseLogin();

      await vi.waitFor(() => {
        expect(consoleLogSpy).toHaveBeenCalledWith(
          "✅ 后端服务正常（非JSON响应）:",
          "OK"
        );
      });
    });

    it("should handle backend connection error", async () => {
      fetchMock.mockRejectedValue(new Error("Network error"));

      diagnoseLogin();

      await vi.waitFor(() => {
        expect(consoleErrorSpy).toHaveBeenCalledWith(
          "❌ 后端服务无法连接（通过代理）:",
          "Network error"
        );
      });
    });

    it("should check login API endpoint", async () => {
      fetchMock.mockResolvedValue({
        ok: false,
        status: 401,
        text: () => Promise.resolve("Unauthorized"),
      });

      diagnoseLogin();

      await vi.waitFor(() => {
        const loginApiCall = fetchMock.mock.calls.find(
          (call) => call[0] === "/api/v1/auth/login"
        );
        expect(loginApiCall).toBeDefined();
        expect(loginApiCall[1].method).toBe("POST");
        expect(loginApiCall[1].headers["Content-Type"]).toBe(
          "application/x-www-form-urlencoded"
        );
      });
    });

    it("should log summary after 2 seconds", async () => {
      fetchMock.mockResolvedValue({
        ok: false,
        status: 401,
        text: () => Promise.resolve("Unauthorized"),
      });

      diagnoseLogin();

      // Fast-forward time
      vi.advanceTimersByTime(2000);

      await vi.waitFor(() => {
        expect(consoleLogSpy).toHaveBeenCalledWith(
          expect.stringContaining("📊 诊断结果汇总:")
        );
      });
    });

    it("should attach to window object", () => {
      expect(window.diagnoseLogin).toBe(diagnoseLogin);
    });

    it("should not attach to window in non-browser environment", () => {
      const originalWindow = global.window;
      delete global.window;

      // Re-import to test the condition
      const module = require("./diagnose");

      global.window = originalWindow;

      // Should not throw error
      expect(() => module.diagnoseLogin()).not.toThrow();
    });
  });
});
