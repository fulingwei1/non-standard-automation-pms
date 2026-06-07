import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  setupApiTest,
  teardownApiTest,
} from "../api/__tests__/_test-setup.js";

describe("solutionVersionService", () => {
  let mock;
  let api;
  let solutionVersionService;

  beforeEach(async () => {
    const setup = await setupApiTest();
    mock = setup.mock;
    api = setup.api;

    const module = await import("../solutionVersionService.js");
    solutionVersionService = module.solutionVersionService;

    vi.clearAllMocks();
  });

  afterEach(() => {
    teardownApiTest(mock);
  });

  it("uses the shared /api/v1 base URL for quote binding endpoints", async () => {
    mock.onPost("/api/v1/sales/quote-versions/7/validate-binding").reply(200, {
      quote_version_id: 7,
      status: "valid",
      issues: [],
      is_valid: true,
    });
    mock.onPost("/api/v1/sales/quote-versions/7/sync-cost").reply(200, {
      quote_version_id: 7,
      cost_total: 120000,
      gross_margin: 40,
      binding_status: "valid",
    });
    mock.onPost("/api/v1/sales/quote-versions/7/bind").reply((config) => {
      expect(config.params).toEqual({
        solution_version_id: 11,
        cost_estimation_id: 23,
      });
      return [
        200,
        {
          quote_version_id: 7,
          solution_version_id: 11,
          cost_estimation_id: 23,
        },
      ];
    });

    await expect(solutionVersionService.validateBinding(7)).resolves.toMatchObject({
      quote_version_id: 7,
    });
    await expect(solutionVersionService.syncCostToQuote(7)).resolves.toMatchObject({
      cost_total: 120000,
    });
    await expect(
      solutionVersionService.bindQuoteVersion(7, 11, 23)
    ).resolves.toMatchObject({
      solution_version_id: 11,
      cost_estimation_id: 23,
    });

    expect(mock.history.post.map((request) => api.getUri(request))).toEqual([
      "/api/v1/sales/quote-versions/7/validate-binding",
      "/api/v1/sales/quote-versions/7/sync-cost",
      "/api/v1/sales/quote-versions/7/bind?solution_version_id=11&cost_estimation_id=23",
    ]);
  });
});
