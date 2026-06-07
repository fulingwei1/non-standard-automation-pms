import { describe, expect, it } from "vitest";
import { presaleWorkbenchApi, technicalAssessmentApi } from "../index.js";

describe("services/api index", () => {
  it("exports presaleWorkbenchApi for sales presale pages", () => {
    expect(presaleWorkbenchApi).toBeDefined();
    expect(typeof presaleWorkbenchApi.loadOverview).toBe("function");
  });

  it("exports technicalAssessmentApi for presale technical pages", () => {
    expect(technicalAssessmentApi).toBeDefined();
    expect(typeof technicalAssessmentApi.getRequirementFreezes).toBe("function");
  });
});
