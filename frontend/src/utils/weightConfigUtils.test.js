import { describe, expect, it } from "vitest";
import {
  defaultWeights,
  fadeIn,
  validateWeights,
} from "./weightConfigUtils";

describe("weightConfigUtils", () => {
  describe("defaultWeights", () => {
    it("should have correct default weights", () => {
      expect(defaultWeights.deptManager).toBe(50);
      expect(defaultWeights.projectManager).toBe(50);
    });

    it("should sum to 100", () => {
      const total = defaultWeights.deptManager + defaultWeights.projectManager;
      expect(total).toBe(100);
    });

    it("should be an object with two properties", () => {
      expect(typeof defaultWeights).toBe("object");
      expect(Object.keys(defaultWeights)).toHaveLength(2);
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

  describe("validateWeights", () => {
    it("should validate weights that sum to 100", () => {
      const weights = { deptManager: 50, projectManager: 50 };
      const result = validateWeights(weights);

      expect(result.totalWeight).toBe(100);
      expect(result.isValid).toBe(true);
    });

    it("should validate weights that sum to 100 (different split)", () => {
      const weights = { deptManager: 60, projectManager: 40 };
      const result = validateWeights(weights);

      expect(result.totalWeight).toBe(100);
      expect(result.isValid).toBe(true);
    });

    it("should invalidate weights that sum less than 100", () => {
      const weights = { deptManager: 40, projectManager: 40 };
      const result = validateWeights(weights);

      expect(result.totalWeight).toBe(80);
      expect(result.isValid).toBe(false);
    });

    it("should invalidate weights that sum more than 100", () => {
      const weights = { deptManager: 60, projectManager: 60 };
      const result = validateWeights(weights);

      expect(result.totalWeight).toBe(120);
      expect(result.isValid).toBe(false);
    });

    it("should handle zero weights", () => {
      const weights = { deptManager: 0, projectManager: 100 };
      const result = validateWeights(weights);

      expect(result.totalWeight).toBe(100);
      expect(result.isValid).toBe(true);
    });

    it("should handle decimal weights", () => {
      const weights = { deptManager: 33.3, projectManager: 66.7 };
      const result = validateWeights(weights);

      expect(result.totalWeight).toBe(100);
      expect(result.isValid).toBe(true);
    });

    it("should handle negative weights", () => {
      const weights = { deptManager: -10, projectManager: 110 };
      const result = validateWeights(weights);

      expect(result.totalWeight).toBe(100);
      expect(result.isValid).toBe(true);
    });

    it("should return totalWeight correctly", () => {
      const weights1 = { deptManager: 25, projectManager: 25 };
      expect(validateWeights(weights1).totalWeight).toBe(50);

      const weights2 = { deptManager: 75, projectManager: 75 };
      expect(validateWeights(weights2).totalWeight).toBe(150);
    });
  });
});
