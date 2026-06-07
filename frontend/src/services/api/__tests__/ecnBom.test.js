import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { setupApiTest, teardownApiTest } from "./_test-setup.js";

describe("ecnBomApi", () => {
  let mock;
  let ecnBomApi;

  beforeEach(async () => {
    const setup = await setupApiTest();
    mock = setup.mock;

    const module = await import("../ecnBom.js");
    ecnBomApi = module.ecnBomApi;

    vi.clearAllMocks();
  });

  afterEach(() => {
    teardownApiTest(mock);
  });

  it("list() 使用后端 /ecns 路由并保留项目上下文筛选", async () => {
    mock.onGet("/api/v1/ecns").reply((config) => {
      expect(config.params).toMatchObject({
        project_id: "42",
        ecn_type: "设计变更",
        status: "DRAFT",
        priority: "HIGH",
        page: 2,
        page_size: 50,
      });

      return [200, { data: { items: [], total: 0 } }];
    });

    await ecnBomApi.list({
      project_id: "42",
      change_type: "设计变更",
      status: "DRAFT",
      priority: "HIGH",
      page: 2,
      page_size: 50,
    });

    expect(mock.history.get).toHaveLength(1);
    expect(mock.history.get[0].url).toBe("/ecns");
  });

  it("create() 将旧页面表单字段映射为后端 EcnCreate 字段", async () => {
    mock.onPost("/api/v1/ecns").reply((config) => {
      expect(JSON.parse(config.data)).toMatchObject({
        ecn_title: "夹具结构变更",
        ecn_type: "设计变更",
        source_type: "MANUAL",
        project_id: 42,
        change_reason: "客户验收标准变化",
        change_description: "客户验收标准变化",
        change_scope: "PARTIAL",
        priority: "HIGH",
        urgency: "HIGH",
        cost_impact: 0,
        schedule_impact_days: 0,
      });

      return [201, { id: 1 }];
    });

    await ecnBomApi.create({
      title: "夹具结构变更",
      change_type: "设计变更",
      affected_projects: [42],
      description: "客户验收标准变化",
      priority: "high",
    });

    expect(mock.history.post).toHaveLength(1);
    expect(mock.history.post[0].url).toBe("/ecns");
  });

  it("getImpact() 和 applyToBom() 使用后端 ECN 集成路由", async () => {
    mock.onGet("/api/v1/ecns/5/bom-impact-summary").reply(200, {
      data: { impact_summary: {} },
    });
    mock.onPost("/api/v1/ecns/5/sync-to-bom").reply(200, {
      code: 200,
      data: {},
    });

    await ecnBomApi.getImpact(5);
    await ecnBomApi.applyToBom(5);

    expect(mock.history.get[0].url).toBe("/ecns/5/bom-impact-summary");
    expect(mock.history.post[0].url).toBe("/ecns/5/sync-to-bom");
  });
});
