import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { setupApiTest, teardownApiTest } from "./_test-setup.js";

describe("assessmentApi compatibility", () => {
  let mock;
  let assessmentApi;

  beforeEach(async () => {
    const setup = await setupApiTest();
    mock = setup.mock;

    const module = await import("../assessment.js");
    assessmentApi = module.assessmentApi;

    vi.clearAllMocks();
  });

  afterEach(() => {
    teardownApiTest(mock);
  });

  it("list() maps a lead source to the real lead assessments endpoint", async () => {
    mock.onGet("/api/v1/sales/leads/7/assessments").reply(200, [
      { id: 1, status: "PENDING" },
    ]);

    const response = await assessmentApi.list({
      source_type: "LEAD",
      source_id: 7,
    });

    expect(response.status).toBe(200);
  });

  it("create() maps an opportunity source to the real apply endpoint", async () => {
    mock.onPost("/api/v1/sales/opportunities/9/assessments/apply").reply(
      (config) => {
        expect(JSON.parse(config.data)).toEqual({
          evaluator_id: 3,
          presale_ticket_id: 91,
        });
        return [201, { data: { assessment_id: 12 } }];
      }
    );

    const response = await assessmentApi.create({
      source_type: "OPPORTUNITY",
      source_id: 9,
      evaluator_id: 3,
      presale_ticket_id: 91,
    });

    expect(response.status).toBe(201);
  });

  it("submit() maps to the real evaluate endpoint and normalizes payload", async () => {
    mock.onPost("/api/v1/sales/assessments/12/evaluate").reply((config) => {
      expect(JSON.parse(config.data)).toEqual({
        requirement_data: { tech_maturity: "mature" },
        enable_ai: false,
      });
      return [200, { id: 12, status: "COMPLETED" }];
    });

    const response = await assessmentApi.submit(12, {
      tech_maturity: "mature",
    });

    expect(response.status).toBe(200);
  });
});
