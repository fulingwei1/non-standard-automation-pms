import { describe, expect, it } from "vitest";

import { formatCurrency } from "../utils";

describe("formatCurrency", () => {
  it("falls back to zero for non-finite values", () => {
    expect(formatCurrency(Number.NaN)).not.toContain("NaN");
    expect(formatCurrency("not-a-number")).not.toContain("NaN");
    expect(formatCurrency(Number.NaN)).toBe("¥0.00");
  });
});
