import { describe, expect, it } from "vitest";
import {
  getStatusBadge,
  getLevelInfo,
  getTrendIcon,
  calculateQuarterComparison,
} from "./performanceUtils";
import {
  Clock,
  CheckCircle2,
  AlertCircle,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
} from "lucide-react";

describe("performanceUtils", () => {
  describe("getStatusBadge", () => {
    it("should return IN_PROGRESS badge", () => {
      const badge = getStatusBadge("IN_PROGRESS");
      expect(badge.label).toBe("填写中");
      expect(badge.color).toBe("bg-slate-500/20 text-slate-400");
      expect(badge.icon).toBe(Clock);
    });

    it("should return SUBMITTED badge", () => {
      const badge = getStatusBadge("SUBMITTED");
      expect(badge.label).toBe("已提交");
      expect(badge.color).toBe("bg-blue-500/20 text-blue-400");
      expect(badge.icon).toBe(CheckCircle2);
    });

    it("should return EVALUATING badge", () => {
      const badge = getStatusBadge("EVALUATING");
      expect(badge.label).toBe("评价中");
      expect(badge.color).toBe("bg-amber-500/20 text-amber-400");
      expect(badge.icon).toBe(Clock);
    });

    it("should return COMPLETED badge", () => {
      const badge = getStatusBadge("COMPLETED");
      expect(badge.label).toBe("已完成");
      expect(badge.color).toBe("bg-emerald-500/20 text-emerald-400");
      expect(badge.icon).toBe(CheckCircle2);
    });

    it("should return PENDING badge", () => {
      const badge = getStatusBadge("PENDING");
      expect(badge.label).toBe("待评价");
      expect(badge.color).toBe("bg-orange-500/20 text-orange-400");
      expect(badge.icon).toBe(AlertCircle);
    });

    it("should return IN_PROGRESS badge for unknown status", () => {
      const badge = getStatusBadge("UNKNOWN");
      expect(badge.label).toBe("填写中");
    });
  });

  describe("getLevelInfo", () => {
    it("should return info for A level", () => {
      const info = getLevelInfo("A");
      expect(info.name).toBe("优秀");
      expect(info.color).toBe("text-emerald-400");
      expect(info.bgColor).toBe("bg-emerald-500/20");
      expect(info.borderColor).toBe("border-emerald-500/30");
    });

    it("should return info for B level", () => {
      const info = getLevelInfo("B");
      expect(info.name).toBe("良好");
      expect(info.color).toBe("text-blue-400");
      expect(info.bgColor).toBe("bg-blue-500/20");
      expect(info.borderColor).toBe("border-blue-500/30");
    });

    it("should return info for C level", () => {
      const info = getLevelInfo("C");
      expect(info.name).toBe("合格");
      expect(info.color).toBe("text-amber-400");
      expect(info.bgColor).toBe("bg-amber-500/20");
      expect(info.borderColor).toBe("border-amber-500/30");
    });

    it("should return info for D level", () => {
      const info = getLevelInfo("D");
      expect(info.name).toBe("待改进");
      expect(info.color).toBe("text-red-400");
      expect(info.bgColor).toBe("bg-red-500/20");
      expect(info.borderColor).toBe("border-red-500/30");
    });

    it("should return C level info for unknown level", () => {
      const info = getLevelInfo("X");
      expect(info.name).toBe("合格");
      expect(info.color).toBe("text-amber-400");
    });

    it("should have all required properties", () => {
      const info = getLevelInfo("A");
      expect(info).toHaveProperty("name");
      expect(info).toHaveProperty("color");
      expect(info).toHaveProperty("bgColor");
      expect(info).toHaveProperty("borderColor");
    });
  });

  describe("getTrendIcon", () => {
    it("should return Minus icon when no previous value", () => {
      const trend = getTrendIcon(80, null);
      expect(trend.icon).toBe(Minus);
      expect(trend.color).toBe("text-slate-400");
    });

    it("should return Minus icon when no previous value (undefined)", () => {
      const trend = getTrendIcon(80, undefined);
      expect(trend.icon).toBe(Minus);
      expect(trend.color).toBe("text-slate-400");
    });

    it("should return ArrowUpRight for increasing trend", () => {
      const trend = getTrendIcon(90, 80);
      expect(trend.icon).toBe(ArrowUpRight);
      expect(trend.color).toBe("text-emerald-400");
    });

    it("should return ArrowDownRight for decreasing trend", () => {
      const trend = getTrendIcon(80, 90);
      expect(trend.icon).toBe(ArrowDownRight);
      expect(trend.color).toBe("text-red-400");
    });

    it("should return Minus for no change", () => {
      const trend = getTrendIcon(80, 80);
      expect(trend.icon).toBe(Minus);
      expect(trend.color).toBe("text-slate-400");
    });

    it("should handle decimal values", () => {
      const trendUp = getTrendIcon(85.5, 85.4);
      expect(trendUp.icon).toBe(ArrowUpRight);

      const trendDown = getTrendIcon(85.4, 85.5);
      expect(trendDown.icon).toBe(ArrowDownRight);
    });
  });

  describe("calculateQuarterComparison", () => {
    it("should return null for empty array", () => {
      const result = calculateQuarterComparison([]);
      expect(result).toBeNull();
    });

    it("should return null for single item", () => {
      const result = calculateQuarterComparison([{ score: 80 }]);
      expect(result).toBeNull();
    });

    it("should calculate comparison for two quarters", () => {
      const quarterlyTrend = [
        { quarter: "Q1", score: 80 },
        { quarter: "Q2", score: 90 },
      ];

      const result = calculateQuarterComparison(quarterlyTrend);

      expect(result).toEqual({
        current: 90,
        previous: 80,
        change: 10,
        percentChange: "12.5",
      });
    });

    it("should use last two items from array", () => {
      const quarterlyTrend = [
        { score: 70 },
        { score: 80 },
        { score: 85 },
        { score: 90 },
      ];

      const result = calculateQuarterComparison(quarterlyTrend);

      expect(result.current).toBe(90);
      expect(result.previous).toBe(85);
      expect(result.change).toBe(5);
      expect(result.percentChange).toBe("5.9");
    });

    it("should calculate negative change", () => {
      const quarterlyTrend = [
        { score: 90 },
        { score: 80 },
      ];

      const result = calculateQuarterComparison(quarterlyTrend);

      expect(result.change).toBe(-10);
      expect(result.percentChange).toBe("-11.1");
    });

    it("should calculate zero change", () => {
      const quarterlyTrend = [
        { score: 85 },
        { score: 85 },
      ];

      const result = calculateQuarterComparison(quarterlyTrend);

      expect(result.change).toBe(0);
      expect(result.percentChange).toBe("0.0");
    });

    it("should handle decimal scores", () => {
      const quarterlyTrend = [
        { score: 85.5 },
        { score: 90.25 },
      ];

      const result = calculateQuarterComparison(quarterlyTrend);

      expect(result.current).toBe(90.25);
      expect(result.previous).toBe(85.5);
      expect(result.change).toBeCloseTo(4.75, 2);
    });

    it("should format percentChange to 1 decimal place", () => {
      const quarterlyTrend = [
        { score: 80 },
        { score: 85 },
      ];

      const result = calculateQuarterComparison(quarterlyTrend);

      expect(result.percentChange).toBe("6.2"); // (5/80)*100 = 6.25 -> "6.2"
    });

    it("should return null for null/undefined input", () => {
      expect(calculateQuarterComparison(null)).toBeNull();
      expect(calculateQuarterComparison(undefined)).toBeNull();
    });
  });
});
