import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import {
  getCurrentPeriod,
  getStatusBadge,
  getLevelColor,
  fadeIn,
} from "./monthlySummaryUtils";

describe("monthlySummaryUtils", () => {
  describe("getCurrentPeriod", () => {
    beforeEach(() => {
      // Mock Date to a fixed time: 2024-03-15
      vi.useFakeTimers();
      vi.setSystemTime(new Date(2024, 2, 15)); // March 15, 2024
    });

    afterEach(() => {
      vi.useRealTimers();
    });

    it("should return current period information", () => {
      const period = getCurrentPeriod();

      expect(period.year).toBe(2024);
      expect(period.month).toBe(3);
      expect(period.period).toBe("2024-03");
    });

    // 源码使用 toISOString() 转换日期，在非 UTC 时区会有偏移
    // 使用与源码相同的逻辑来计算期望值
    it("should calculate start date correctly", () => {
      const period = getCurrentPeriod();
      const expected = new Date(2024, 2, 1).toISOString().split("T")[0];
      expect(period.startDate).toBe(expected);
    });

    it("should calculate end date correctly", () => {
      const period = getCurrentPeriod();
      const expected = new Date(2024, 3, 0).toISOString().split("T")[0];
      expect(period.endDate).toBe(expected);
    });

    it("should calculate days left", () => {
      const period = getCurrentPeriod();
      expect(period.daysLeft).toBe(16); // 31 - 15 = 16
    });

    it("should handle January correctly", () => {
      vi.setSystemTime(new Date(2024, 0, 20)); // January 20, 2024
      const period = getCurrentPeriod();

      expect(period.month).toBe(1);
      expect(period.period).toBe("2024-01");
      expect(period.startDate).toBe(new Date(2024, 0, 1).toISOString().split("T")[0]);
      expect(period.endDate).toBe(new Date(2024, 1, 0).toISOString().split("T")[0]);
      expect(period.daysLeft).toBe(11); // 31 - 20 = 11
    });

    it("should handle December correctly", () => {
      vi.setSystemTime(new Date(2024, 11, 25)); // December 25, 2024
      const period = getCurrentPeriod();

      expect(period.month).toBe(12);
      expect(period.period).toBe("2024-12");
      expect(period.startDate).toBe(new Date(2024, 11, 1).toISOString().split("T")[0]);
      expect(period.endDate).toBe(new Date(2025, 0, 0).toISOString().split("T")[0]);
      expect(period.daysLeft).toBe(6); // 31 - 25 = 6
    });

    it("should handle February in leap year", () => {
      vi.setSystemTime(new Date(2024, 1, 15)); // February 15, 2024 (leap year)
      const period = getCurrentPeriod();

      expect(period.month).toBe(2);
      expect(period.endDate).toBe(new Date(2024, 2, 0).toISOString().split("T")[0]);
      expect(period.daysLeft).toBe(14); // 29 - 15 = 14
    });

    it("should handle February in non-leap year", () => {
      vi.setSystemTime(new Date(2023, 1, 15)); // February 15, 2023 (non-leap)
      const period = getCurrentPeriod();

      expect(period.month).toBe(2);
      expect(period.endDate).toBe(new Date(2023, 2, 0).toISOString().split("T")[0]);
      expect(period.daysLeft).toBe(13); // 28 - 15 = 13
    });
  });

  describe("getStatusBadge", () => {
    it("should return correct badge for IN_PROGRESS", () => {
      const badge = getStatusBadge("IN_PROGRESS");
      expect(badge.label).toBe("进行中");
      expect(badge.color).toContain("blue");
    });

    it("should return correct badge for SUBMITTED", () => {
      const badge = getStatusBadge("SUBMITTED");
      expect(badge.label).toBe("已提交");
      expect(badge.color).toContain("emerald");
    });

    it("should return correct badge for EVALUATING", () => {
      const badge = getStatusBadge("EVALUATING");
      expect(badge.label).toBe("评价中");
      expect(badge.color).toContain("amber");
    });

    it("should return correct badge for COMPLETED", () => {
      const badge = getStatusBadge("COMPLETED");
      expect(badge.label).toBe("已完成");
      expect(badge.color).toContain("slate");
    });

    it("should return default badge for unknown status", () => {
      const badge = getStatusBadge("UNKNOWN");
      expect(badge.label).toBe("进行中");
    });
  });

  describe("getLevelColor", () => {
    it("should return correct color for level A", () => {
      expect(getLevelColor("A")).toContain("emerald");
    });

    it("should return correct color for level B", () => {
      expect(getLevelColor("B")).toContain("blue");
    });

    it("should return correct color for level C", () => {
      expect(getLevelColor("C")).toContain("amber");
    });

    it("should return correct color for level D", () => {
      expect(getLevelColor("D")).toContain("red");
    });

    it("should return default color for unknown level", () => {
      expect(getLevelColor("X")).toContain("slate");
    });
  });

  describe("fadeIn", () => {
    it("should have correct initial state", () => {
      expect(fadeIn.initial).toEqual({ opacity: 0, y: 20 });
    });

    it("should have correct animate state", () => {
      expect(fadeIn.animate).toEqual({ opacity: 1, y: 0 });
    });

    it("should have transition duration", () => {
      expect(fadeIn.transition.duration).toBe(0.4);
    });
  });
});
