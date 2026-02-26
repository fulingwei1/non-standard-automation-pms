/**
 * Projects API 测试
 * 测试范围：
 * - projectApi: 项目CRUD操作
 * - machineApi: 机器设备管理
 * - stageApi: 项目阶段管理
 * - milestoneApi: 里程碑管理
 * - memberApi: 成员管理
 * - costApi: 成本管理
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';

describe('Projects API', () => {
  let _api, mock;
  let projectApi, machineApi, stageApi, milestoneApi, memberApi, costApi;
  let financialCostApi, projectWorkspaceApi, projectContributionApi;

  beforeEach(async () => {
    // 设置测试环境
    
    // 导入项目模块
    const projectsModule = await import('../projects.js');
    projectApi = projectsModule.projectApi;
    machineApi = projectsModule.machineApi;
    stageApi = projectsModule.stageApi;
    milestoneApi = projectsModule.milestoneApi;
    memberApi = projectsModule.memberApi;
    costApi = projectsModule.costApi;
    financialCostApi = projectsModule.financialCostApi;
    projectWorkspaceApi = projectsModule.projectWorkspaceApi;
    projectContributionApi = projectsModule.projectContributionApi;
  });

  afterEach(() => {
    mock.restore();
  });

  describe('projectApi - 项目API', () => {
    it('list() - 应该获取项目列表', async () => {
      const mockData = {
        success: true,
        data: [
          { id: 1, name: 'Project 1', status: 'ACTIVE' },
          { id: 2, name: 'Project 2', status: 'COMPLETED' },
        ],
      };
      mock.onGet('/api/v1/projects/').reply(200, mockData);

      const response = await projectApi.list({ page: 1, page_size: 10 });

      expect(response.status).toBe(200);
      expect(mock.history.get).toHaveLength(1);
      expect(mock.history.get[0].params).toEqual({ page: 1, page_size: 10 });
    });

    it('get() - 应该获取单个项目详情', async () => {
      const mockProject = {
        success: true,
        data: { id: 1, name: 'Test Project', status: 'ACTIVE' },
      };
      mock.onGet('/api/v1/projects/1').reply(200, mockProject);

      const response = await projectApi.get(1);

      expect(response.status).toBe(200);
      expect(mock.history.get).toHaveLength(1);
    });

    it('create() - 应该创建新项目', async () => {
      const newProject = { name: 'New Project', customer_id: 1 };
      mock.onPost('/api/v1/projects/').reply(201, {
        success: true,
        data: { id: 3, ...newProject },
      });

      const response = await projectApi.create(newProject);

      expect(response.status).toBe(201);
      expect(mock.history.post).toHaveLength(1);
      expect(JSON.parse(mock.history.post[0].data)).toEqual(newProject);
    });

    it('update() - 应该更新项目', async () => {
      const updates = { name: 'Updated Project' };
      mock.onPut('/api/v1/projects/1').reply(200, {
        success: true,
        data: { id: 1, ...updates },
      });

      const response = await projectApi.update(1, updates);

      expect(response.status).toBe(200);
      expect(mock.history.put).toHaveLength(1);
    });

    it('getMachines() - 应该获取项目的机器设备', async () => {
      mock.onGet('/api/v1/projects/1/machines').reply(200, {
        success: true,
        data: [{ id: 1, name: 'Machine 1' }],
      });

      const response = await projectApi.getMachines(1);

      expect(response.status).toBe(200);
    });

    it('getBoard() - 应该获取项目看板数据', async () => {
      mock.onGet('/api/v1/projects/board').reply(200, {
        success: true,
        data: { stages: [] },
      });

      const response = await projectApi.getBoard({ status: 'ACTIVE' });

      expect(response.status).toBe(200);
      expect(mock.history.get[0].params).toEqual({ status: 'ACTIVE' });
    });

    it('checkAutoTransition() - 应该检查自动阶段转换', async () => {
      mock.onPost('/api/v1/projects/1/check-auto-transition').reply(200, {
        success: true,
        data: { can_transition: true },
      });

      const response = await projectApi.checkAutoTransition(1, true);

      expect(response.status).toBe(200);
      expect(JSON.parse(mock.history.post[0].data)).toEqual({
        auto_advance: true,
      });
    });

    it('应该处理API错误', async () => {
      mock.onGet('/api/v1/projects/999').reply(404, {
        success: false,
        message: 'Project not found',
      });

      await expect(projectApi.get(999)).rejects.toThrow();
    });
  });

  describe('machineApi - 机器设备API', () => {
    it('list() - 应该获取机器列表', async () => {
      mock.onGet('/api/v1/projects/1/machines').reply(200, {
        success: true,
        data: [{ id: 1, name: 'Machine 1' }],
      });

      const response = await machineApi.list(1, { page: 1 });

      expect(response.status).toBe(200);
      expect(mock.history.get[0].params).toEqual({ page: 1 });
    });

    it('create() - 应该创建机器设备', async () => {
      const machineData = { name: 'New Machine', model: 'ABC-123' };
      mock.onPost('/api/v1/projects/1/machines').reply(201, {
        success: true,
        data: { id: 1, ...machineData },
      });

      const response = await machineApi.create(1, machineData);

      expect(response.status).toBe(201);
    });

    it('updateProgress() - 应该更新机器进度', async () => {
      mock.onPut('/api/v1/projects/1/machines/1/progress').reply(200, {
        success: true,
        data: { progress_pct: 75 },
      });

      const response = await machineApi.updateProgress(1, 1, 75);

      expect(response.status).toBe(200);
      expect(mock.history.put[0].params).toEqual({ progress_pct: 75 });
    });

    it('uploadDocument() - 应该上传文档', async () => {
      const formData = new FormData();
      formData.append('file', new Blob(['test']), 'test.pdf');

      mock.onPost('/api/v1/projects/1/machines/1/documents/upload').reply(200, {
        success: true,
        data: { id: 1, filename: 'test.pdf' },
      });

      const response = await machineApi.uploadDocument(1, 1, formData);

      expect(response.status).toBe(200);
    });

    it('getSummary() - 应该获取机器汇总', async () => {
      mock.onGet('/api/v1/projects/1/machines/summary').reply(200, {
        success: true,
        data: { total: 5, completed: 2 },
      });

      const response = await machineApi.getSummary(1);

      expect(response.status).toBe(200);
    });
  });

  describe('stageApi - 阶段API', () => {
    it('list() - 应该获取阶段列表', async () => {
      mock.onGet('/api/v1/stages/').reply(200, {
        success: true,
        data: [{ id: 1, name: 'Stage 1' }],
      });

      const response = await stageApi.list({});

      expect(response.status).toBe(200);
    });

    it('list() - 应该支持按项目ID获取阶段', async () => {
      mock.onGet('/api/v1/stages/projects/1/stages').reply(200, {
        success: true,
        data: [{ id: 1, name: 'Stage 1' }],
      });

      const response = await stageApi.list({ project_id: 1 });

      expect(response.status).toBe(200);
    });

    it('statuses() - 应该获取阶段状态', async () => {
      mock.onGet('/api/v1/stages/statuses').reply(200, {
        success: true,
        data: ['ACTIVE', 'COMPLETED'],
      });

      const _response = await stageApi.statuses(1);

      expect(mock.history.get[0].params).toEqual({ stage_id: 1 });
    });
  });

  describe('milestoneApi - 里程碑API', () => {
    it('create() - 应该创建里程碑', async () => {
      const milestone = { name: 'Milestone 1', project_id: 1 };
      mock.onPost('/api/v1/milestones/').reply(201, {
        success: true,
        data: { id: 1, ...milestone },
      });

      const response = await milestoneApi.create(milestone);

      expect(response.status).toBe(201);
    });

    it('complete() - 应该完成里程碑', async () => {
      mock.onPut('/api/v1/milestones/1/complete').reply(200, {
        success: true,
        data: { id: 1, status: 'COMPLETED' },
      });

      const response = await milestoneApi.complete(1, {
        completion_date: '2024-01-01',
      });

      expect(response.status).toBe(200);
    });
  });

  describe('memberApi - 成员API', () => {
    it('add() - 应该添加成员', async () => {
      const member = { project_id: 1, user_id: 1, role: 'DEVELOPER' };
      mock.onPost('/api/v1/members/').reply(201, {
        success: true,
        data: { id: 1, ...member },
      });

      const response = await memberApi.add(member);

      expect(response.status).toBe(201);
    });

    it('remove() - 应该移除成员', async () => {
      mock.onDelete('/api/v1/members/1').reply(204);

      const response = await memberApi.remove(1);

      expect(response.status).toBe(204);
    });

    it('batchAdd() - 应该批量添加成员', async () => {
      const members = [
        { user_id: 1, role: 'DEVELOPER' },
        { user_id: 2, role: 'TESTER' },
      ];
      mock.onPost('/api/v1/projects/1/members/batch').reply(201, {
        success: true,
        data: members,
      });

      const response = await memberApi.batchAdd(1, members);

      expect(response.status).toBe(201);
    });

    it('checkConflicts() - 应该检查成员冲突', async () => {
      mock
        .onGet('/api/v1/projects/1/members/conflicts')
        .reply(200, { success: true, data: { has_conflict: false } });

      const response = await memberApi.checkConflicts(1, 1, {
        start_date: '2024-01-01',
      });

      expect(response.status).toBe(200);
      expect(mock.history.get[0].params).toEqual({
        user_id: 1,
        start_date: '2024-01-01',
      });
    });
  });

  describe('costApi - 成本API', () => {
    it('list() - 应该获取成本列表', async () => {
      mock.onGet('/api/v1/projects/1/costs').reply(200, {
        success: true,
        data: [{ id: 1, amount: 1000 }],
      });

      const response = await costApi.list(1, { page: 1 });

      expect(response.status).toBe(200);
    });

    it('create() - 应该创建成本记录', async () => {
      const cost = { category: 'MATERIAL', amount: 1000 };
      mock.onPost('/api/v1/projects/1/costs').reply(201, {
        success: true,
        data: { id: 1, ...cost },
      });

      const response = await costApi.create(1, cost);

      expect(response.status).toBe(201);
    });

    it('getCostAnalysis() - 应该获取成本分析', async () => {
      mock.onGet('/api/v1/projects/1/costs/cost-analysis').reply(200, {
        success: true,
        data: { total_cost: 10000 },
      });

      const response = await costApi.getCostAnalysis(1);

      expect(response.status).toBe(200);
    });

    it('getCostAnalysis() - 应该支持对比项目', async () => {
      mock.onGet('/api/v1/projects/1/costs/cost-analysis').reply(200, {
        success: true,
        data: { total_cost: 10000 },
      });

      await costApi.getCostAnalysis(1, 2);

      expect(mock.history.get[0].params).toEqual({ compare_project_id: 2 });
    });

    it('calculateLaborCost() - 应该计算人工成本', async () => {
      mock.onPost('/api/v1/projects/1/costs/calculate-labor-cost').reply(200, {
        success: true,
        data: { labor_cost: 5000 },
      });

      const response = await costApi.calculateLaborCost(1, { month: '2024-01' });

      expect(response.status).toBe(200);
      expect(mock.history.post[0].params).toEqual({ month: '2024-01' });
    });
  });

  describe('financialCostApi - 财务成本API', () => {
    it('downloadTemplate() - 应该下载模板', async () => {
      mock
        .onGet('/api/v1/projects/financial-costs/template')
        .reply(200, new Blob());

      const response = await financialCostApi.downloadTemplate();

      expect(response.status).toBe(200);
    });

    it('uploadCosts() - 应该上传成本数据', async () => {
      const file = new File(['test'], 'costs.xlsx');
      mock.onPost('/api/v1/projects/financial-costs/upload').reply(200, {
        success: true,
        data: { imported: 10 },
      });

      const response = await financialCostApi.uploadCosts(file);

      expect(response.status).toBe(200);
    });
  });

  describe('projectWorkspaceApi - 项目工作空间API', () => {
    it('getWorkspace() - 应该获取工作空间', async () => {
      mock.onGet('/api/v1/projects/1/workspace').reply(200, {
        success: true,
        data: { meetings: [], issues: [] },
      });

      const response = await projectWorkspaceApi.getWorkspace(1);

      expect(response.status).toBe(200);
    });

    it('linkMeeting() - 应该关联会议', async () => {
      mock.onPost('/api/v1/projects/1/meetings/1/link').reply(200, {
        success: true,
      });

      const response = await projectWorkspaceApi.linkMeeting(1, 1, true);

      expect(response.status).toBe(200);
      expect(mock.history.post[0].params).toEqual({ is_primary: true });
    });
  });

  describe('projectContributionApi - 项目贡献API', () => {
    it('getContributions() - 应该获取贡献列表', async () => {
      mock.onGet('/api/v1/projects/1/contributions').reply(200, {
        success: true,
        data: [{ user_id: 1, score: 95 }],
      });

      const response = await projectContributionApi.getContributions(1, {});

      expect(response.status).toBe(200);
    });

    it('rateMember() - 应该评价成员', async () => {
      const rating = { score: 95, comment: 'Great work' };
      mock.onPost('/api/v1/projects/1/contributions/1/rate').reply(200, {
        success: true,
        data: rating,
      });

      const response = await projectContributionApi.rateMember(1, 1, rating);

      expect(response.status).toBe(200);
    });

    it('calculate() - 应该计算贡献', async () => {
      mock.onPost('/api/v1/projects/1/contributions/calculate').reply(200, {
        success: true,
        data: { calculated: true },
      });

      const response = await projectContributionApi.calculate(1, '2024-01');

      expect(response.status).toBe(200);
      expect(mock.history.post[0].params).toEqual({ period: '2024-01' });
    });
  });

  describe('错误处理', () => {
    it('应该处理网络错误', async () => {
      mock.onGet('/api/v1/projects/').networkError();

      await expect(projectApi.list()).rejects.toThrow();
    });

    it('应该处理服务器错误', async () => {
      mock.onGet('/api/v1/projects/').reply(500, {
        success: false,
        message: 'Internal Server Error',
      });

      await expect(projectApi.list()).rejects.toThrow();
    });

    it('应该处理参数验证错误', async () => {
      mock.onPost('/api/v1/projects/').reply(422, {
        success: false,
        message: 'Validation Error',
        errors: { name: ['Name is required'] },
      });

      await expect(projectApi.create({})).rejects.toThrow();
    });
  });
});
