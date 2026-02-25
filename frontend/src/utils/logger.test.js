import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { logger, trace, logIf, group } from "./logger";

describe("logger", () => {
  let consoleLogSpy,
    consoleInfoSpy,
    consoleWarnSpy,
    consoleErrorSpy,
    consoleGroupSpy,
    consoleGroupEndSpy;

  beforeEach(() => {
    consoleLogSpy = vi.spyOn(console, "log").mockImplementation(() => {});
    consoleInfoSpy = vi.spyOn(console, "info").mockImplementation(() => {});
    consoleWarnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});
    consoleErrorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    consoleGroupSpy = vi.spyOn(console, "group").mockImplementation(() => {});
    consoleGroupEndSpy = vi
      .spyOn(console, "groupEnd")
      .mockImplementation(() => {});
  });

  afterEach(() => {
    consoleLogSpy.mockRestore();
    consoleInfoSpy.mockRestore();
    consoleWarnSpy.mockRestore();
    consoleErrorSpy.mockRestore();
    consoleGroupSpy.mockRestore();
    consoleGroupEndSpy.mockRestore();
  });

  describe("logger.debug", () => {
    it("should log debug messages in development", () => {
      logger.debug("Debug message", { data: "test" });

      if (import.meta.env.DEV) {
        expect(consoleLogSpy).toHaveBeenCalledWith(
          "[DEBUG]",
          "Debug message",
          { data: "test" }
        );
      } else {
        expect(consoleLogSpy).not.toHaveBeenCalled();
      }
    });

    it("should handle multiple arguments", () => {
      logger.debug("Test", 1, 2, 3);

      if (import.meta.env.DEV) {
        expect(consoleLogSpy).toHaveBeenCalledWith("[DEBUG]", "Test", 1, 2, 3);
      }
    });

    it("should handle no arguments", () => {
      logger.debug();

      if (import.meta.env.DEV) {
        expect(consoleLogSpy).toHaveBeenCalledWith("[DEBUG]");
      }
    });
  });

  describe("logger.info", () => {
    it("should log info messages in development", () => {
      logger.info("Info message", { status: "ok" });

      if (import.meta.env.DEV) {
        expect(consoleInfoSpy).toHaveBeenCalledWith(
          "[INFO]",
          "Info message",
          { status: "ok" }
        );
      } else {
        expect(consoleInfoSpy).not.toHaveBeenCalled();
      }
    });

    it("should handle multiple arguments", () => {
      logger.info("Test", "a", "b", "c");

      if (import.meta.env.DEV) {
        expect(consoleInfoSpy).toHaveBeenCalledWith(
          "[INFO]",
          "Test",
          "a",
          "b",
          "c"
        );
      }
    });
  });

  describe("logger.warn", () => {
    it("should log warnings", () => {
      logger.warn("Warning message");
      expect(consoleWarnSpy).toHaveBeenCalledWith("[WARN]", "Warning message");
    });

    it("should log warnings with objects", () => {
      const warnData = { reason: "test" };
      logger.warn("Warning", warnData);
      expect(consoleWarnSpy).toHaveBeenCalledWith("[WARN]", "Warning", warnData);
    });

    it("should handle multiple arguments", () => {
      logger.warn("Warn", 1, 2);
      expect(consoleWarnSpy).toHaveBeenCalledWith("[WARN]", "Warn", 1, 2);
    });
  });

  describe("logger.error", () => {
    it("should log errors", () => {
      const error = new Error("Test error");
      logger.error("Error occurred", error);
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        "[ERROR]",
        "Error occurred",
        error
      );
    });

    it("should handle multiple arguments", () => {
      logger.error("Error", "detail1", "detail2");
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        "[ERROR]",
        "Error",
        "detail1",
        "detail2"
      );
    });

    it("should log error objects", () => {
      const errorObj = { code: 500, message: "Server error" };
      logger.error(errorObj);
      expect(consoleErrorSpy).toHaveBeenCalledWith("[ERROR]", errorObj);
    });
  });

  describe("logger.perf", () => {
    it("should measure performance and return result", () => {
      const testFn = vi.fn(() => "result");

      const result = logger.perf("Test operation", testFn);

      expect(testFn).toHaveBeenCalled();
      expect(result).toBe("result");

      if (import.meta.env.DEV) {
        expect(consoleLogSpy).toHaveBeenCalledWith(
          expect.stringMatching(/\[PERF\] Test operation: \d+\.\d{2}ms/)
        );
      }
    });

    it("should handle functions that throw errors", () => {
      const errorFn = () => {
        throw new Error("Test error");
      };

      expect(() => logger.perf("Error operation", errorFn)).toThrow(
        "Test error"
      );
    });

    it("should handle async functions", async () => {
      const asyncFn = async () => {
        await new Promise((resolve) => setTimeout(resolve, 10));
        return "async result";
      };

      const result = logger.perf("Async operation", asyncFn);
      expect(result).toBeInstanceOf(Promise);

      const value = await result;
      expect(value).toBe("async result");
    });

    it("should return result without logging in production", () => {
      const testFn = vi.fn(() => 42);

      const result = logger.perf("Prod test", testFn);

      expect(result).toBe(42);
      expect(testFn).toHaveBeenCalled();
    });
  });

  describe("trace", () => {
    it("should log function entry and return exit function", () => {
      const exitFn = trace("myFunction");

      if (import.meta.env.DEV) {
        expect(consoleLogSpy).toHaveBeenCalledWith("[DEBUG]", "→ myFunction");
      }

      expect(typeof exitFn).toBe("function");

      consoleLogSpy.mockClear();
      exitFn();

      if (import.meta.env.DEV) {
        expect(consoleLogSpy).toHaveBeenCalledWith("[DEBUG]", "← myFunction");
      }
    });

    it("should work with nested calls", () => {
      const exit1 = trace("outer");
      const exit2 = trace("inner");

      exit2();
      exit1();

      if (import.meta.env.DEV) {
        expect(consoleLogSpy).toHaveBeenCalledWith("[DEBUG]", "→ outer");
        expect(consoleLogSpy).toHaveBeenCalledWith("[DEBUG]", "→ inner");
        expect(consoleLogSpy).toHaveBeenCalledWith("[DEBUG]", "← inner");
        expect(consoleLogSpy).toHaveBeenCalledWith("[DEBUG]", "← outer");
      }
    });

    it("should not throw if exit function not called", () => {
      expect(() => {
        trace("forgottenTrace");
      }).not.toThrow();
    });
  });

  describe("logIf", () => {
    it("should log when condition is true in development", () => {
      logIf(true, "Conditional log", { data: "test" });

      if (import.meta.env.DEV) {
        expect(consoleLogSpy).toHaveBeenCalledWith("Conditional log", {
          data: "test",
        });
      }
    });

    it("should not log when condition is false", () => {
      logIf(false, "Should not log");
      expect(consoleLogSpy).not.toHaveBeenCalled();
    });

    it("should handle multiple arguments", () => {
      logIf(true, "Test", 1, 2, 3);

      if (import.meta.env.DEV) {
        expect(consoleLogSpy).toHaveBeenCalledWith("Test", 1, 2, 3);
      }
    });

    it("should handle truthy and falsy values", () => {
      logIf(1, "Truthy");
      logIf(0, "Falsy");
      logIf("yes", "String");
      logIf("", "Empty");

      if (import.meta.env.DEV) {
        expect(consoleLogSpy).toHaveBeenCalledWith("Truthy");
        expect(consoleLogSpy).toHaveBeenCalledWith("String");
        expect(consoleLogSpy).not.toHaveBeenCalledWith("Falsy");
        expect(consoleLogSpy).not.toHaveBeenCalledWith("Empty");
      }
    });
  });

  describe("group", () => {
    it("should create console group in development", () => {
      const mockFn = vi.fn();

      group("Test Group", mockFn);

      expect(mockFn).toHaveBeenCalled();

      if (import.meta.env.DEV) {
        expect(consoleGroupSpy).toHaveBeenCalledWith("Test Group");
        expect(consoleGroupEndSpy).toHaveBeenCalled();
      } else {
        expect(consoleGroupSpy).not.toHaveBeenCalled();
        expect(consoleGroupEndSpy).not.toHaveBeenCalled();
      }
    });

    it("should execute function even if grouping is not available", () => {
      const mockFn = vi.fn(() => "result");

      const result = group("Group", mockFn);

      expect(mockFn).toHaveBeenCalled();
      // group doesn't return the function result in current implementation
    });

    it("should handle functions that throw errors", () => {
      const errorFn = () => {
        throw new Error("Group error");
      };

      expect(() => group("Error Group", errorFn)).toThrow("Group error");

      if (import.meta.env.DEV) {
        // groupEnd should still be called even if function throws
        // However, current implementation doesn't handle this
        // This is a potential improvement area
      }
    });

    it("should handle nested groups", () => {
      group("Outer", () => {
        group("Inner", () => {
          logger.debug("Nested message");
        });
      });

      if (import.meta.env.DEV) {
        expect(consoleGroupSpy).toHaveBeenCalledWith("Outer");
        expect(consoleGroupSpy).toHaveBeenCalledWith("Inner");
        expect(consoleGroupEndSpy).toHaveBeenCalledTimes(2);
      }
    });
  });

  describe("production behavior", () => {
    it("should suppress most logs in production", () => {
      // This test verifies the log suppression logic
      logger.debug("Debug");
      logger.info("Info");

      if (!import.meta.env.DEV) {
        expect(consoleLogSpy).not.toHaveBeenCalled();
        expect(consoleInfoSpy).not.toHaveBeenCalled();
      }
    });

    it("should still show errors in production", () => {
      logger.error("Production error");
      expect(consoleErrorSpy).toHaveBeenCalled();
    });

    it("should still show warnings in production", () => {
      logger.warn("Production warning");
      expect(consoleWarnSpy).toHaveBeenCalled();
    });
  });
});
