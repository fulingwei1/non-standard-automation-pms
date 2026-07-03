/**
 * presaleAIService（重建版）契约：需求分析 → 确认回填 → 方案/三档报价。
 * 关键约定：方案与报价请求必须携带 requirement_analysis_id（需求只录一次）。
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { setupApiTest, teardownApiTest } from "../api/__tests__/_test-setup.js";

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

  it("需求分析打注册的 analyze-requirement 端点", async () => {
    const input = {
      presale_ticket_id: 501,
      raw_requirement: "整机FCT功能测试系统，15秒节拍，MES对接",
    };
    mock.onPost("/api/v1/presale/ai/analyze-requirement").reply((config) => {
      expect(JSON.parse(config.data)).toEqual(input);
      return [201, { id: 31, presale_ticket_id: 501, confidence_score: 0.85 }];
    });

    await expect(presaleAIService.analyzeRequirement(input)).resolves.toMatchObject({
      id: 31,
    });
  });

  it("确认分析打 confirm 端点并返回回填结果", async () => {
    mock.onPost("/api/v1/presale/ai/analysis/31/confirm").reply(200, {
      analysis_id: 31,
      status: "approved",
      backfilled: true,
      filled_fields: ["acceptance_criteria"],
    });

    await expect(presaleAIService.confirmAnalysis(31)).resolves.toMatchObject({
      backfilled: true,
    });
  });

  it("方案生成提交后台任务并携带 requirement_analysis_id", async () => {
    mock.onPost("/api/v1/presale/ai/generate-solution").reply((config) => {
      const body = JSON.parse(config.data);
      expect(body.requirement_analysis_id).toBe(31);
      expect(body.requirements).toBeUndefined();
      return [200, { job_id: 7, status: "PENDING" }];
    });

    await expect(
      presaleAIService.submitGenerateSolution({
        presale_ticket_id: 501,
        requirement_analysis_id: 31,
        generate_architecture: false,
        generate_bom: false,
      })
    ).resolves.toMatchObject({ job_id: 7 });
  });

  it("三档报价提交后台任务并携带 requirement_analysis_id（不重贴需求文本）", async () => {
    mock.onPost("/api/v1/ai-jobs/three-tier-quotations").reply((config) => {
      const body = JSON.parse(config.data);
      expect(body.requirement_analysis_id).toBe(31);
      expect(body.base_requirements ?? "").toBe("");
      return [200, { job_id: 8, status: "PENDING" }];
    });

    await expect(
      presaleAIService.submitThreeTierQuotation({
        presale_ticket_id: 501,
        requirement_analysis_id: 31,
      })
    ).resolves.toMatchObject({ job_id: 8 });
  });

  it("轮询任务状态", async () => {
    mock.onGet("/api/v1/ai-jobs/8").reply(200, {
      job_id: 8,
      status: "SUCCESS",
      result: { basic: { total: 850000 } },
    });

    await expect(presaleAIService.getJob(8)).resolves.toMatchObject({
      status: "SUCCESS",
    });
  });
});
