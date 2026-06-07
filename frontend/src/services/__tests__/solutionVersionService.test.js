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

  it("uses the shared /api/v1 base URL for solution version endpoints", async () => {
    mock.onPost("/api/v1/sales/solutions/5/versions").reply((config) => {
      expect(JSON.parse(config.data)).toEqual({ version_no: "V1.0" });
      return [200, { id: 9, solution_id: 5, version_no: "V1.0" }];
    });
    mock.onGet("/api/v1/sales/solutions/5/versions").reply(200, [
      { id: 9, solution_id: 5, version_no: "V1.0" },
    ]);
    mock.onGet("/api/v1/sales/solution-versions/9").reply(200, {
      id: 9,
      version_no: "V1.0",
    });
    mock.onPut("/api/v1/sales/solution-versions/9").reply((config) => {
      expect(JSON.parse(config.data)).toEqual({ content: "updated" });
      return [200, { id: 9, content: "updated" }];
    });
    mock.onPost("/api/v1/sales/solution-versions/9/submit").reply(200, {
      id: 9,
      status: "reviewing",
    });
    mock.onPost("/api/v1/sales/solution-versions/9/approve").reply((config) => {
      expect(JSON.parse(config.data)).toEqual({
        action: "approve",
        comments: "ok",
      });
      return [200, { id: 9, status: "approved" }];
    });
    mock.onGet("/api/v1/sales/solution-versions/compare").reply((config) => {
      expect(config.params).toEqual({ version_id_1: 9, version_id_2: 10 });
      return [200, { version_id_1: 9, version_id_2: 10, differences: [] }];
    });
    mock.onGet("/api/v1/sales/solution-versions/9/impact").reply(200, {
      version_id: 9,
      affected_quotes: [],
    });

    await expect(
      solutionVersionService.createVersion(5, { version_no: "V1.0" })
    ).resolves.toMatchObject({ solution_id: 5 });
    await expect(solutionVersionService.getVersionHistory(5)).resolves.toHaveLength(1);
    await expect(solutionVersionService.getVersion(9)).resolves.toMatchObject({ id: 9 });
    await expect(
      solutionVersionService.updateVersion(9, { content: "updated" })
    ).resolves.toMatchObject({ content: "updated" });
    await expect(solutionVersionService.submitForReview(9)).resolves.toMatchObject({
      status: "reviewing",
    });
    await expect(
      solutionVersionService.approveVersion(9, "approve", "ok")
    ).resolves.toMatchObject({ status: "approved" });
    await expect(solutionVersionService.compareVersions(9, 10)).resolves.toMatchObject({
      differences: [],
    });
    await expect(solutionVersionService.checkUpdateImpact(9)).resolves.toMatchObject({
      version_id: 9,
    });

    expect(mock.history.post.map((request) => api.getUri(request))).toEqual([
      "/api/v1/sales/solutions/5/versions",
      "/api/v1/sales/solution-versions/9/submit",
      "/api/v1/sales/solution-versions/9/approve",
    ]);
    expect(mock.history.get.map((request) => api.getUri(request))).toEqual([
      "/api/v1/sales/solutions/5/versions",
      "/api/v1/sales/solution-versions/9",
      "/api/v1/sales/solution-versions/compare?version_id_1=9&version_id_2=10",
      "/api/v1/sales/solution-versions/9/impact",
    ]);
    expect(mock.history.put.map((request) => api.getUri(request))).toEqual([
      "/api/v1/sales/solution-versions/9",
    ]);
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
