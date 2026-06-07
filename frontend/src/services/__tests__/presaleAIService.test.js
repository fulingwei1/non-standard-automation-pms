import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  setupApiTest,
  teardownApiTest,
} from "../api/__tests__/_test-setup.js";

describe("presaleAIService", () => {
  let mock;
  let api;
  let presaleAIService;

  beforeEach(async () => {
    const setup = await setupApiTest();
    mock = setup.mock;
    api = setup.api;

    const module = await import("../presaleAIService.js");
    presaleAIService = module.presaleAIService;

    vi.clearAllMocks();
  });

  afterEach(() => {
    teardownApiTest(mock);
  });

  it("uses the shared /api/v1 base URL for dashboard stats", async () => {
    mock.onGet("/api/v1/presale/ai/dashboard/stats").reply((config) => {
      expect(config.params).toEqual({ days: 14 });
      return [
        200,
        {
          total_requests: 8,
          successful_requests: 7,
          success_rate: 87.5,
        },
      ];
    });

    await expect(presaleAIService.getDashboardStats(14)).resolves.toMatchObject({
      total_requests: 8,
    });

    expect(mock.history.get.map((request) => api.getUri(request))).toEqual([
      "/api/v1/presale/ai/dashboard/stats?days=14",
    ]);
  });

  it("posts cost estimation to the backend registered estimate-cost endpoint", async () => {
    const input = {
      presale_ticket_id: 501,
      project_type: "自动化产线",
      complexity_level: "medium",
      hardware_items: [{ name: "PLC", unit_price: 5000, quantity: 2 }],
    };

    mock.onPost("/api/v1/presale/ai/estimate-cost").reply((config) => {
      expect(JSON.parse(config.data)).toEqual(input);
      return [
        200,
        {
          id: 23,
          presale_ticket_id: 501,
          solution_id: null,
          cost_breakdown: { total_cost: 120000 },
        },
      ];
    });

    await expect(presaleAIService.estimateCost(input)).resolves.toMatchObject({
      id: 23,
      presale_ticket_id: 501,
    });

    expect(mock.history.post.map((request) => api.getUri(request))).toEqual([
      "/api/v1/presale/ai/estimate-cost",
    ]);
  });

  it("uses registered integration and win-rate AI endpoints", async () => {
    mock.onPost("/api/v1/presale/ai/workflow/start").reply((config) => {
      expect(JSON.parse(config.data)).toEqual({
        presale_ticket_id: 501,
        initial_data: { source: "lead" },
        auto_run: false,
      });
      return [200, [{ id: 1, status: "started" }]];
    });
    mock.onGet("/api/v1/presale/ai/health-check").reply(200, {
      status: "healthy",
    });
    mock.onPost("/api/v1/presale/ai/predict-win-rate").reply((config) => {
      expect(JSON.parse(config.data)).toEqual({
        presale_ticket_id: 501,
        ticket_data: { industry: "electronics" },
      });
      return [200, { presale_ticket_id: 501, win_rate_score: 76 }];
    });

    await expect(
      presaleAIService.startWorkflow(501, { source: "lead" }, false)
    ).resolves.toHaveLength(1);
    await expect(presaleAIService.healthCheck()).resolves.toMatchObject({
      status: "healthy",
    });
    await expect(
      presaleAIService.predictWinRate({
        presale_ticket_id: 501,
        ticket_data: { industry: "electronics" },
      })
    ).resolves.toMatchObject({ win_rate_score: 76 });

    expect(mock.history.post.map((request) => api.getUri(request))).toEqual([
      "/api/v1/presale/ai/workflow/start",
      "/api/v1/presale/ai/predict-win-rate",
    ]);
    expect(mock.history.get.map((request) => api.getUri(request))).toEqual([
      "/api/v1/presale/ai/health-check",
    ]);
  });

  it("uses registered requirement and quotation AI endpoints", async () => {
    const requirement = {
      presale_ticket_id: 501,
      raw_requirement: "客户需要一套FCT自动化测试线",
    };
    const quotation = {
      presale_ticket_id: 501,
      quotation_type: "standard",
      items: [{ name: "FCT测试线", quantity: 1, unit_price: 180000 }],
    };

    mock.onPost("/api/v1/presale/ai/analyze-requirement").reply((config) => {
      expect(JSON.parse(config.data)).toEqual(requirement);
      return [201, { id: 31, presale_ticket_id: 501 }];
    });
    mock.onPost("/api/v1/presale/ai/generate-quotation").reply((config) => {
      expect(JSON.parse(config.data)).toEqual(quotation);
      return [200, { id: 41, presale_ticket_id: 501 }];
    });

    await expect(
      presaleAIService.analyzeRequirement(requirement)
    ).resolves.toMatchObject({ id: 31 });
    await expect(
      presaleAIService.generateQuotation(quotation)
    ).resolves.toMatchObject({ id: 41 });

    expect(mock.history.post.map((request) => api.getUri(request))).toEqual([
      "/api/v1/presale/ai/analyze-requirement",
      "/api/v1/presale/ai/generate-quotation",
    ]);
  });

  it("uses registered solution, knowledge, emotion, and script endpoints", async () => {
    const solution = {
      presale_ticket_id: 501,
      requirements: { equipment_type: "FCT" },
      generate_architecture: true,
      generate_bom: true,
    };
    const emotion = {
      presale_ticket_id: 501,
      customer_id: 77,
      communication_content: "客户反馈方案方向认可，但担心交期",
    };

    mock.onPost("/api/v1/presale/ai/generate-solution").reply((config) => {
      expect(JSON.parse(config.data)).toEqual(solution);
      return [200, { solution: { id: 51 }, generation_time_seconds: 1.2 }];
    });
    mock.onGet("/api/v1/presale/ai/knowledge-base/search").reply((config) => {
      expect(config.params).toEqual({ keyword: "FCT夹具案例" });
      return [200, { cases: [], total: 0, page: 1, page_size: 20, total_pages: 0 }];
    });
    mock.onPost("/api/v1/presale/ai/analyze-emotion").reply((config) => {
      expect(JSON.parse(config.data)).toEqual(emotion);
      return [200, { id: 61, sentiment: "neutral", customer_id: 77 }];
    });
    mock.onGet("/api/v1/sales/ai/customers/77/recommend-scripts").reply((config) => {
      expect(config.params).toEqual({
        opportunity_id: 88,
        scenario_type: "technical_followup",
      });
      return [200, { scripts: ["强调交付计划"] }];
    });

    await expect(
      presaleAIService.generateSolution(solution)
    ).resolves.toMatchObject({ solution: { id: 51 } });
    await expect(
      presaleAIService.searchKnowledge("FCT夹具案例")
    ).resolves.toMatchObject({ total: 0 });
    await expect(
      presaleAIService.analyzeEmotion(emotion)
    ).resolves.toMatchObject({ sentiment: "neutral" });
    await expect(
      presaleAIService.recommendScript({
        customer_id: 77,
        opportunity_id: 88,
        scenario_type: "technical_followup",
      })
    ).resolves.toMatchObject({ scripts: ["强调交付计划"] });

    expect(mock.history.post.map((request) => api.getUri(request))).toEqual([
      "/api/v1/presale/ai/generate-solution",
      "/api/v1/presale/ai/analyze-emotion",
    ]);
    expect(mock.history.get.map((request) => api.getUri(request))).toEqual([
      "/api/v1/presale/ai/knowledge-base/search?keyword=FCT%E5%A4%B9%E5%85%B7%E6%A1%88%E4%BE%8B",
      "/api/v1/sales/ai/customers/77/recommend-scripts?opportunity_id=88&scenario_type=technical_followup",
    ]);
  });
});
