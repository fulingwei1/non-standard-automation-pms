import { describe, expect, it } from "vitest";
import {
  scoringGuidelines,
  commentTemplates,
  validateScore,
  validateComment,
} from "./evaluationUtils";

describe("evaluationUtils", () => {
  describe("scoringGuidelines", () => {
    it("should have 7 scoring levels", () => {
      expect(scoringGuidelines).toHaveLength(7);
    });

    it("should have proper structure for each guideline", () => {
      scoringGuidelines.forEach((guideline) => {
        expect(guideline).toHaveProperty("range");
        expect(guideline).toHaveProperty("level");
        expect(guideline).toHaveProperty("description");
        expect(guideline).toHaveProperty("color");
      });
    });

    it("should have A+ level for highest score", () => {
      const highest = scoringGuidelines[0];
      expect(highest.range).toBe("95-100");
      expect(highest.level).toBe("A+");
      expect(highest.color).toBe("text-emerald-400");
    });

    it("should have D level for lowest score", () => {
      const lowest = scoringGuidelines[6];
      expect(lowest.range).toBe("60-69");
      expect(lowest.level).toBe("D");
      expect(lowest.color).toBe("text-red-400");
    });

    it("should have appropriate colors for different levels", () => {
      const aPlus = scoringGuidelines.find((g) => g.level === "A+");
      const bPlus = scoringGuidelines.find((g) => g.level === "B+");
      const cPlus = scoringGuidelines.find((g) => g.level === "C+");
      const d = scoringGuidelines.find((g) => g.level === "D");

      expect(aPlus.color).toBe("text-emerald-400");
      expect(bPlus.color).toBe("text-blue-400");
      expect(cPlus.color).toBe("text-amber-400");
      expect(d.color).toBe("text-red-400");
    });
  });

  describe("commentTemplates", () => {
    it("should have 3 categories", () => {
      expect(commentTemplates).toHaveLength(3);
    });

    it("should have proper structure for each category", () => {
      commentTemplates.forEach((category) => {
        expect(category).toHaveProperty("category");
        expect(category).toHaveProperty("templates");
        expect(Array.isArray(category.templates)).toBe(true);
        expect(category.templates.length).toBeGreaterThan(0);
      });
    });

    it("should have '优秀表现' category", () => {
      const excellent = commentTemplates.find(
        (c) => c.category === "优秀表现"
      );
      expect(excellent).toBeDefined();
      expect(excellent.templates.length).toBeGreaterThan(0);
    });

    it("should have '良好表现' category", () => {
      const good = commentTemplates.find((c) => c.category === "良好表现");
      expect(good).toBeDefined();
      expect(good.templates.length).toBeGreaterThan(0);
    });

    it("should have '需改进' category", () => {
      const improve = commentTemplates.find((c) => c.category === "需改进");
      expect(improve).toBeDefined();
      expect(improve.templates.length).toBeGreaterThan(0);
    });
  });

  describe("validateScore", () => {
    it("should reject null/undefined score", () => {
      const nullResult = validateScore(null);
      expect(nullResult.valid).toBe(false);
      expect(nullResult.message).toBe("请输入评分");

      const undefinedResult = validateScore(undefined);
      expect(undefinedResult.valid).toBe(false);
      expect(undefinedResult.message).toBe("请输入评分");
    });

    it("should reject empty string", () => {
      const result = validateScore("");
      expect(result.valid).toBe(false);
      expect(result.message).toBe("请输入评分");
    });

    it("should reject score below 60", () => {
      const result = validateScore(59);
      expect(result.valid).toBe(false);
      expect(result.message).toBe("评分必须在60-100之间");
    });

    it("should reject score above 100", () => {
      const result = validateScore(101);
      expect(result.valid).toBe(false);
      expect(result.message).toBe("评分必须在60-100之间");
    });

    it("should accept score 60", () => {
      const result = validateScore(60);
      expect(result.valid).toBe(true);
    });

    it("should accept score 100", () => {
      const result = validateScore(100);
      expect(result.valid).toBe(true);
    });

    it("should accept score in valid range", () => {
      const result80 = validateScore(80);
      expect(result80.valid).toBe(true);

      const result95 = validateScore(95);
      expect(result95.valid).toBe(true);

      const result70 = validateScore(70);
      expect(result70.valid).toBe(true);
    });

    it("should accept string numbers", () => {
      const result = validateScore("85");
      expect(result.valid).toBe(true);
    });

    it("should reject invalid string numbers", () => {
      const result = validateScore("abc");
      expect(result.valid).toBe(false);
      expect(result.message).toBe("评分必须在60-100之间");
    });

    it("should handle decimal scores", () => {
      const result = validateScore(85.5);
      expect(result.valid).toBe(true);
    });
  });

  describe("validateComment", () => {
    it("should reject null/undefined comment", () => {
      const nullResult = validateComment(null);
      expect(nullResult.valid).toBe(false);
      expect(nullResult.message).toBe("请填写评价意见");

      const undefinedResult = validateComment(undefined);
      expect(undefinedResult.valid).toBe(false);
      expect(undefinedResult.message).toBe("请填写评价意见");
    });

    it("should reject empty string", () => {
      const result = validateComment("");
      expect(result.valid).toBe(false);
      expect(result.message).toBe("请填写评价意见");
    });

    it("should reject whitespace-only string", () => {
      const result = validateComment("   ");
      expect(result.valid).toBe(false);
      expect(result.message).toBe("请填写评价意见");
    });

    it("should accept valid comment", () => {
      const result = validateComment("工作表现优秀");
      expect(result.valid).toBe(true);
    });

    it("should accept comment with leading/trailing spaces", () => {
      const result = validateComment("  工作表现优秀  ");
      expect(result.valid).toBe(true);
    });

    it("should accept single character comment", () => {
      const result = validateComment("好");
      expect(result.valid).toBe(true);
    });

    it("should accept long comment", () => {
      const longComment = "这是一段很长的评价意见。".repeat(100);
      const result = validateComment(longComment);
      expect(result.valid).toBe(true);
    });
  });
});
