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

    it("should calculate start date correctly", () => {
      const period = getCurrentPeriod();
      expect(period.startDate).toBe("2024-03-01");
    });

    it("should calculate end date correctly", () => {
      const period = getCurrentPeriod();
      expect(period.endDate).toBe("2024-03-31");
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
      expect(period.startDate).toBe("2024-01-01");
      expect(period.endDate).toBe("2024-01-31");
      expect(period.daysLeft).toBe(11); // 31 - 20 = 11
    });

    it("should handle December correctly", () => {
      vi.setSystemTime(new Date(2024, 11, 25)); // December 25, 2024
      const period = getCurrentPeriod();

      expect(period.month).toBe(12);
      expect(period.period).toBe("2024-12");
      expect(period.startDate).toBe("2024-12-01");
      expect(period.endDate).toBe("2024-12-31");
      expect(period.daysLeft).toBe(6); // 31 - 25 = 6
    });

    it("should handle February in leap year", () => {
      vi.setSystemTime(new Date(2024, 1, 15)); // February 15, 2024 (leap year)
      const period = getCurrentPeriod();

      expect(period.month).toBe(2);
      expect(period.endDate).toBe("2024-02-29");
      expect(period.daysLeft).toBe(14); // 29 - 15 = 14
    });

    it("should handle February in non-leap year", () => {
      vi.setSystemTime(new Date(2023, 1, 15)); // February 15, 2023 (non-leap)
      const period = getCurrentPeriod();

      expect(period.month).toBe(2);
      expect(period.endDate).toBe("2023-02-28");
      expect(period.daysLeft).toBe(13); // 28 - 15 = 13
    });

    it("should pad month with zero for single digit", () => {
      vi.setSystemTime(new Date(2024, 0, 1)); // January
      expect(getCurrentPeriod().period).toBe("2024-01");

      vi.setSystemTime(new Date(2024, 8, 1)); // September
      expect(getCurrentPeriod().period).toBe("2024-09");
    });
  });

  describe("getStatusBadge", () => {
    it("should return IN_PROGRESS badge", () => {
      const badge = getStatusBadge("IN_PROGRESS");
      expect(badge.label).toBe("进行中");
      expect(badge.color).toBe("bg-blue-500/20 text-blue-400");
    });

    it("should return SUBMITTED badge", () => {
      const badge = getStatusBadge("SUBMITTED");
      expect(badge.label).toBe("已提交");
      expect(badge.color).toBe("bg-emerald-500/20 text-emerald-400");
    });

    it("should return EVALUATING badge", () => {
      const badge = getStatusBadge("EVALUATING");
      expect(badge.label).toBe("评价中");
      expect(badge.color).toBe("bg-amber-500/20 text-amber-400");
    });

    it("should return COMPLETED badge", () => {
      const badge = getStatusBadge("COMPLETED");
      expect(badge.label).toBe("已完成");
      expect(badge.color).toBe("bg-slate-500/20 text-slate-400");
    });

    it("should return IN_PROGRESS badge for unknown status", () => {
      const badge = getStatusBadge("UNKNOWN");
      expect(badge.label).toBe("进行中");
      expect(badge.color).toBe("bg-blue-500/20 text-blue-400");
    });

    it("should return IN_PROGRESS badge for null/undefined", () => {
      expect(getStatusBadge(null).label).toBe("进行中");
      expect(getStatusBadge(undefined).label).toBe("进行中");
    });
  });

  describe("getLevelColor", () => {
    it("should return emerald color for A level", () => {
      const color = getLevelColor("A");
      expect(color).toBe("text-emerald-400");
    });

    it("should return blue color for B level", () => {
      const color = getLevelColor("B");
      expect(color).toBe("text-blue-400");
    });

    it("should return amber color for C level", () => {
      const color = getLevelColor("C");
      expect(color).toBe("text-amber-400");
    });

    it("should return red color for D level", () => {
      const color = getLevelColor("D");
      expect(color).toBe("text-red-400");
    });

    it("should return slate color for unknown level", () => {
      const color = getLevelColor("X");
      expect(color).toBe("text-slate-400");
    });

    it("should return slate color for null/undefined", () => {
      expect(getLevelColor(null)).toBe("text-slate-400");
      expect(getLevelColor(undefined)).toBe("text-slate-400");
    });
  });

  describe("fadeIn", () => {
    it("should have correct animation properties", () => {
      expect(fadeIn.initial).toEqual({ opacity: 0, y: 20 });
      expect(fadeIn.animate).toEqual({ opacity: 1, y: 0 });
      expect(fadeIn.transition).toEqual({ duration: 0.4 });
    });

    it("should be an object with animation config", () => {
      expect(typeof fadeIn).toBe("object");
      expect(fadeIn).toHaveProperty("initial");
      expect(fadeIn).toHaveProperty("animate");
      expect(fadeIn).toHaveProperty("transition");
    });
  });
});
