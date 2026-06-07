import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { setupApiTest, teardownApiTest } from "./_test-setup.js";

describe("leadAssessmentApi compatibility", () => {
  let mock;
  let leadAssessmentApi;

  beforeEach(async () => {
    const setup = await setupApiTest();
    mock = setup.mock;

    const module = await import("../leadAssessment.js");
    leadAssessmentApi = module.leadAssessmentApi;

    vi.clearAllMocks();
  });

  afterEach(() => {
    teardownApiTest(mock);
  });

  it("list() maps to the real lead assessments endpoint for a lead id", async () => {
    mock.onGet("/api/v1/sales/leads/7/assessments").reply(200, [
      { id: 1, source_type: "LEAD", source_id: 7, status: "PENDING" },
    ]);

    const response = await leadAssessmentApi.list({ lead_id: 7 });

    expect(response.status).toBe(200);
  });

  it("submit() maps to the real assessment evaluate endpoint", async () => {
    mock.onPost("/api/v1/sales/assessments/12/evaluate").reply((config) => {
      expect(JSON.parse(config.data)).toEqual({
        requirement_data: { automation_type: "vision" },
        enable_ai: false,
      });
      return [200, { id: 12, status: "COMPLETED" }];
    });

    const response = await leadAssessmentApi.submit(12, {
      automation_type: "vision",
    });

    expect(response.status).toBe(200);
  });
});
