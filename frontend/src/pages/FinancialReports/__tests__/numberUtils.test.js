import { describe, expect, it } from "vitest";

import { safePercent, toFiniteNumber } from "../numberUtils";

describe("financial report number utils", () => {
  it("normalizes invalid numbers to zero", () => {
    expect(toFiniteNumber(Number.NaN)).toBe(0);
    expect(toFiniteNumber("bad-value")).toBe(0);
  });

  it("does not produce NaN when calculating percentages", () => {
    expect(safePercent(10, 0)).toBe(0);
    expect(safePercent(Number.NaN, 100)).toBe(0);
  });
});
