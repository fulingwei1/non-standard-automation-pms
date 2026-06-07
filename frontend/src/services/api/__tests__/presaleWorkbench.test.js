import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { setupApiTest, teardownApiTest } from './_test-setup.js';

describe('presaleWorkbenchApi', () => {
  let mock;
  let presaleWorkbenchApi;

  beforeEach(async () => {
    const setup = await setupApiTest();
    mock = setup.mock;

    const workbenchModule = await import('../presaleWorkbench.js');
    presaleWorkbenchApi = workbenchModule.presaleWorkbenchApi;

    vi.clearAllMocks();
  });

  afterEach(() => {
    teardownApiTest(mock);
  });

  it('loadContext() - 应该通过售前工作台聚合接口获取上下文', async () => {
    mock.onGet('/api/v1/presale/workbench/context').reply((config) => {
      expect(config.params).toMatchObject({
        source_type: 'lead',
        source_id: 1,
        entity_type: 'LEAD',
        entity_id: 1,
      });

      return [200, {
        code: 200,
        data: {
          source: { type: 'lead', id: 1 },
          ticket: null,
          assessment: {
            items: [{ id: 11, status: 'COMPLETED', total_score: 88 }],
            total: 1,
            current: { id: 11, status: 'COMPLETED', total_score: 88 },
            requirementDetail: { id: 101, requirement_version: 'REQ-1.0' },
            risks: {
              items: [{ id: 7, risk_title: '关键部件交期风险' }],
              total: 1,
            },
            versions: {
              items: [{ id: 8, version_no: 'V1.0' }],
              total: 1,
            },
          },
          templates: {
            assessment: {
              items: [{ id: 1, template_name: '标准评估模板' }],
              total: 1,
            },
            technical: {
              items: [{ id: 2, name: 'ICT 标准模板' }],
              total: 1,
            },
          },
          solutions: { items: [], total: 0 },
          funnel: {
            entityType: 'LEAD',
            entityId: 1,
            gateConfigs: {
              items: [{ id: 3, gate_type: 'G1' }],
              total: 1,
            },
            stages: {
              items: [{ id: 4, stage_code: 'NEW', stage_name: '新线索' }],
              total: 1,
            },
            transitionLogs: {
              items: [{ id: 5, transition_reason: '手动推进' }],
              total: 1,
            },
            dwellAlerts: {
              items: [{ id: 6, severity: 'WARNING' }],
              total: 1,
            },
            gateStatus: { gate_type: 'G1', is_valid: true },
          },
          meta: { failures: [] },
        },
      }];
    });

    const context = await presaleWorkbenchApi.loadContext({
      sourceType: 'lead',
      sourceId: 1,
    });

    expect(context.assessment.current.id).toBe(11);
    expect(context.assessment.requirementDetail.id).toBe(101);
    expect(context.assessment.risks.total).toBe(1);
    expect(context.templates.assessment.items[0].template_name).toBe('标准评估模板');
    expect(context.templates.technical.items[0].name).toBe('ICT 标准模板');
    expect(context.funnel.gateConfigs.items[0].gate_type).toBe('G1');
    expect(context.funnel.stages.items[0].stage_code).toBe('NEW');
    expect(context.meta.failures).toEqual([]);
    expect(mock.history.get).toHaveLength(1);
    expect(mock.history.get[0].url).toBe('/presale/workbench/context');
  });

  it('loadContext() - 应该保留后端聚合接口返回的局部失败信息', async () => {
    mock.onGet('/api/v1/presale/workbench/context').reply((config) => {
      expect(config.params).toMatchObject({
        source_type: 'opportunity',
        source_id: 9,
        entity_type: 'OPPORTUNITY',
        entity_id: 9,
      });

      return [200, {
        code: 200,
        data: {
          source: { type: 'opportunity', id: 9 },
          ticket: null,
          assessment: {
            items: [{ id: 21, status: 'COMPLETED', total_score: 76 }],
            total: 1,
            current: { id: 21, status: 'COMPLETED', total_score: 76 },
            requirementDetail: null,
            risks: { items: [], total: 0 },
            versions: {
              items: [{ id: 22, version_no: 'V2.0' }],
              total: 1,
            },
          },
          templates: {
            assessment: {
              items: [{ id: 1, template_name: '定制项目模板' }],
              total: 1,
            },
            technical: {
              items: [{ id: 2, name: 'FCT 定制模板' }],
              total: 1,
            },
          },
          solutions: {
            items: [{ id: 31, solution_name: '方案 A' }],
            total: 1,
          },
          funnel: {
            entityType: 'OPPORTUNITY',
            entityId: 9,
            gateConfigs: { items: [], total: 0 },
            stages: {
              items: [{ id: 4, stage_code: 'DISCOVERY' }],
              total: 1,
            },
            transitionLogs: { items: [], total: 0 },
            dwellAlerts: { items: [], total: 0 },
            gateStatus: { gate_type: 'G2', is_valid: false },
          },
          meta: {
            failures: [{ key: 'risks', message: '风险服务暂不可用' }],
          },
        },
      }];
    });

    const context = await presaleWorkbenchApi.loadContext({
      sourceType: 'opportunity',
      sourceId: 9,
    });

    expect(context.assessment.current.id).toBe(21);
    expect(context.assessment.versions.total).toBe(1);
    expect(context.assessment.risks.total).toBe(0);
    expect(context.solutions.total).toBe(1);
    expect(context.meta.failures).toEqual([
      { key: 'risks', message: '风险服务暂不可用' },
    ]);
    expect(mock.history.get).toHaveLength(1);
    expect(mock.history.get[0].url).toBe('/presale/workbench/context');
  });

  it('loadAssessmentArtifacts() - 应该按评估拉取结构化风险和版本', async () => {
    mock.onGet('/api/v1/sales/assessments/42/risks').reply(200, {
      code: 200,
      data: {
        items: [{ id: 1, risk_title: '治具兼容性风险' }],
        total: 1,
      },
    });
    mock.onGet('/api/v1/sales/assessments/42/versions').reply(500, {
      detail: '版本服务异常',
    });

    const artifacts = await presaleWorkbenchApi.loadAssessmentArtifacts(42);

    expect(artifacts.risks.total).toBe(1);
    expect(artifacts.risks.items[0].risk_title).toBe('治具兼容性风险');
    expect(artifacts.versions.total).toBe(0);
    expect(artifacts.meta.failures).toEqual([
      { key: 'versions', message: '版本服务异常' },
    ]);
  });

  it('saveRequirementDetail() - 应该清洗只读字段并序列化 JSON 字段', async () => {
    mock.onPut('/api/v1/sales/leads/5/requirement-detail').reply((config) => {
      const payload = JSON.parse(config.data);

      expect(payload.id).toBeUndefined();
      expect(payload.lead_id).toBeUndefined();
      expect(payload.requirement_version).toBeUndefined();
      expect(payload.is_frozen).toBeUndefined();
      expect(payload.technical_spec).toBe(JSON.stringify({ fixture: 'ICT' }));
      expect(payload.requirement_items).toBe(JSON.stringify([{ name: '相机' }]));
      expect(payload.cycle_time_seconds).toBeNull();
      expect(payload.workstation_count).toBe(8);

      return [200, {
        id: 15,
        lead_id: 5,
        technical_spec: payload.technical_spec,
        requirement_items: payload.requirement_items,
      }];
    });

    const response = await presaleWorkbenchApi.saveRequirementDetail(
      5,
      {
        id: 9,
        lead_id: 5,
        requirement_version: 'REQ-1.0',
        is_frozen: false,
        technical_spec: { fixture: 'ICT' },
        requirement_items: [{ name: '相机' }],
        cycle_time_seconds: '',
        workstation_count: '8',
      },
      { hasExisting: true },
    );

    expect(response.data.lead_id).toBe(5);
  });

  it('loadOverview() - 应该聚合工单、方案、模板和漏斗健康数据', async () => {
    mock.onGet('/api/v1/presale/workbench/overview').reply(200, {
      code: 200,
      data: {
        tickets: {
          items: [{ id: 1, ticket_no: 'PS-001' }],
          total: 1,
        },
        solutions: {
          items: [{ id: 2, solution_name: '整线方案 A' }],
          total: 1,
        },
        templates: {
          assessment: {
            items: [{ id: 3, template_name: '标准评估模板' }],
            total: 1,
          },
          technical: {
            items: [{ id: 4, name: 'FCT 模板' }],
            total: 1,
          },
        },
        funnel: {
          summary: {
            leads: 12,
            opportunities: 6,
            quotes: 3,
            contracts: 1,
          },
          health: {
            dashboard_date: '2026-03-13',
            overall_health: { score: 78, level: 'GOOD' },
            key_metrics: { target_coverage: 112.5 },
            alerts: [{ title: 'Pipeline 达标' }],
          },
          conversion: {
            stages: [{ stage: 'DISCOVERY', count: 6 }],
            overall_metrics: { total_leads: 6, total_won: 1 },
          },
          dwellAlerts: {
            items: [{ id: 5, severity: 'WARNING' }],
            total: 1,
          },
        },
        meta: { failures: [] },
      },
    });

    const overview = await presaleWorkbenchApi.loadOverview();

    expect(overview.tickets.total).toBe(1);
    expect(overview.solutions.total).toBe(1);
    expect(overview.templates.assessment.total).toBe(1);
    expect(overview.funnel.summary.leads).toBe(12);
    expect(overview.funnel.health.overall_health.score).toBe(78);
    expect(overview.funnel.dwellAlerts.total).toBe(1);
    expect(overview.meta.failures).toEqual([]);
    expect(mock.history.get).toHaveLength(1);
    expect(mock.history.get[0].url).toBe('/presale/workbench/overview');
  });
});
