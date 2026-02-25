/**
 * Engineering API 测试
 * 测试范围：
 * - projectReviewApi: 项目复盘
 * - technicalReviewApi: 技术评审
 * - technicalAssessmentApi: 技术评估
 * - rdProjectApi: 研发项目
 * - rdReportApi: 研发报表
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { setupApiTest, teardownApiTest } from './_test-setup.js';

describe('Engineering API', () => {
  let api, mock;
  let projectReviewApi, technicalReviewApi, technicalAssessmentApi;
  let rdProjectApi, rdReportApi, engineersApi;

  beforeEach(async () => {
    vi.resetModules();
    
    const clientModule = await import('../client.js');
    api = clientModule.default || clientModule.api;
    
    const engineeringModule = await import('../engineering.js');
    projectReviewApi = engineeringModule.projectReviewApi;
    technicalReviewApi = engineeringModule.technicalReviewApi;
    technicalAssessmentApi = engineeringModule.technicalAssessmentApi;
    rdProjectApi = engineeringModule.rdProjectApi;
    rdReportApi = engineeringModule.rdReportApi;
    engineersApi = engineeringModule.engineersApi;
    
    mock = new MockAdapter(api);
    vi.clearAllMocks();
  });

  afterEach(() => {
    if (mock) {
      mock.restore();
    }
  });

  describe('projectReviewApi - 项目复盘API', () => {
    it('list() - 应该获取复盘报告列表', async () => {
      mock.onGet('/api/v1/projects/project-reviews').reply(200, {
        success: true,
        data: [{ id: 1, title: 'Review 1' }],
      });

      const response = await projectReviewApi.list({ status: 'PUBLISHED' });

      expect(response.status).toBe(200);
    });

    it('create() - 应该创建复盘报告', async () => {
      const review = { project_id: 1, title: 'Project Review' };
      mock.onPost('/api/v1/projects/project-reviews').reply(201, {
        success: true,
        data: { id: 1, ...review },
      });

      const response = await projectReviewApi.create(review);

      expect(response.status).toBe(201);
    });

    it('publish() - 应该发布复盘报告', async () => {
      mock.onPut('/api/v1/projects/project-reviews/1/publish').reply(200, {
        success: true,
        data: { status: 'PUBLISHED' },
      });

      const response = await projectReviewApi.publish(1);

      expect(response.status).toBe(200);
    });

    it('getLessons() - 应该获取经验教训', async () => {
      mock.onGet('/api/v1/projects/project-reviews/1/lessons').reply(200, {
        success: true,
        data: [{ id: 1, content: 'Lesson learned' }],
      });

      const response = await projectReviewApi.getLessons(1, {});

      expect(response.status).toBe(200);
    });

    it('createLesson() - 应该创建经验教训', async () => {
      const lesson = { content: 'Important lesson', category: 'TECHNICAL' };
      mock.onPost('/api/v1/projects/project-reviews/1/lessons').reply(201, {
        success: true,
        data: { id: 1, ...lesson },
      });

      const response = await projectReviewApi.createLesson(1, lesson);

      expect(response.status).toBe(201);
    });

    it('getBestPractices() - 应该获取最佳实践', async () => {
      mock.onGet('/api/v1/projects/project-reviews/1/best-practices').reply(200, {
        success: true,
        data: [{ id: 1, title: 'Best Practice 1' }],
      });

      const response = await projectReviewApi.getBestPractices(1, {});

      expect(response.status).toBe(200);
    });

    it('searchBestPractices() - 应该搜索最佳实践库', async () => {
      mock.onGet('/api/v1/projects/best-practices').reply(200, {
        success: true,
        data: [{ id: 1, title: 'Practice 1' }],
      });

      const response = await projectReviewApi.searchBestPractices({
        keyword: 'testing',
      });

      expect(response.status).toBe(200);
    });

    it('recommendBestPractices() - 应该推荐最佳实践', async () => {
      const criteria = { project_type: 'AUTOMATION', tags: ['quality'] };
      mock.onPost('/api/v1/projects/best-practices/recommend').reply(200, {
        success: true,
        data: [{ id: 1, relevance_score: 0.95 }],
      });

      const response = await projectReviewApi.recommendBestPractices(criteria);

      expect(response.status).toBe(200);
    });
  });

  describe('technicalReviewApi - 技术评审API', () => {
    it('list() - 应该获取评审列表', async () => {
      mock.onGet('/api/v1/technical-reviews').reply(200, {
        success: true,
        data: [{ id: 1, title: 'Design Review' }],
      });

      const response = await technicalReviewApi.list({ status: 'SCHEDULED' });

      expect(response.status).toBe(200);
    });

    it('create() - 应该创建技术评审', async () => {
      const review = { title: 'Design Review', review_type: 'DESIGN' };
      mock.onPost('/api/v1/technical-reviews').reply(201, {
        success: true,
        data: { id: 1, ...review },
      });

      const response = await technicalReviewApi.create(review);

      expect(response.status).toBe(201);
    });

    it('getParticipants() - 应该获取参与人员', async () => {
      mock.onGet('/api/v1/technical-reviews/1/participants').reply(200, {
        success: true,
        data: [{ id: 1, user_id: 1, role: 'REVIEWER' }],
      });

      const response = await technicalReviewApi.getParticipants(1);

      expect(response.status).toBe(200);
    });

    it('addParticipant() - 应该添加参与人', async () => {
      const participant = { user_id: 1, role: 'REVIEWER' };
      mock.onPost('/api/v1/technical-reviews/1/participants').reply(201, {
        success: true,
        data: { id: 1, ...participant },
      });

      const response = await technicalReviewApi.addParticipant(1, participant);

      expect(response.status).toBe(201);
    });

    it('getIssues() - 应该获取评审问题', async () => {
      mock.onGet('/api/v1/technical-reviews/issues').reply(200, {
        success: true,
        data: [{ id: 1, title: 'Issue 1' }],
      });

      const response = await technicalReviewApi.getIssues({ review_id: 1 });

      expect(response.status).toBe(200);
    });

    it('createIssue() - 应该创建评审问题', async () => {
      const issue = { title: 'Critical Issue', severity: 'HIGH' };
      mock.onPost('/api/v1/technical-reviews/1/issues').reply(201, {
        success: true,
        data: { id: 1, ...issue },
      });

      const response = await technicalReviewApi.createIssue(1, issue);

      expect(response.status).toBe(201);
    });
  });

  describe('technicalAssessmentApi - 技术评估API', () => {
    it('applyForLead() - 应该申请线索技术评估', async () => {
      const assessment = { assessor_id: 1, urgency: 'HIGH' };
      mock.onPost('/api/v1/sales/leads/1/assessments/apply').reply(201, {
        success: true,
        data: { id: 1, ...assessment },
      });

      const response = await technicalAssessmentApi.applyForLead(1, assessment);

      expect(response.status).toBe(201);
    });

    it('evaluate() - 应该执行技术评估', async () => {
      const evaluation = { feasibility_score: 85, risk_level: 'LOW' };
      mock.onPost('/api/v1/sales/assessments/1/evaluate').reply(200, {
        success: true,
        data: { ...evaluation },
      });

      const response = await technicalAssessmentApi.evaluate(1, evaluation);

      expect(response.status).toBe(200);
    });

    it('getFailureCases() - 应该获取失败案例', async () => {
      mock.onGet('/api/v1/sales/failure-cases').reply(200, {
        success: true,
        data: [{ id: 1, title: 'Failure Case 1' }],
      });

      const response = await technicalAssessmentApi.getFailureCases({
        category: 'TECHNICAL',
      });

      expect(response.status).toBe(200);
    });

    it('createFailureCase() - 应该创建失败案例', async () => {
      const failureCase = { title: 'Case 1', root_cause: 'Technical' };
      mock.onPost('/api/v1/sales/failure-cases').reply(201, {
        success: true,
        data: { id: 1, ...failureCase },
      });

      const response = await technicalAssessmentApi.createFailureCase(failureCase);

      expect(response.status).toBe(201);
    });

    it('getOpenItems() - 应该获取未决事项', async () => {
      mock.onGet('/api/v1/sales/open-items').reply(200, {
        success: true,
        data: [{ id: 1, title: 'Open Item 1' }],
      });

      const response = await technicalAssessmentApi.getOpenItems({ status: 'OPEN' });

      expect(response.status).toBe(200);
    });

    it('closeOpenItem() - 应该关闭未决事项', async () => {
      mock.onPost('/api/v1/sales/open-items/1/close').reply(200, {
        success: true,
        data: { status: 'CLOSED' },
      });

      const response = await technicalAssessmentApi.closeOpenItem(1);

      expect(response.status).toBe(200);
    });
  });

  describe('rdProjectApi - 研发项目API', () => {
    it('list() - 应该获取研发项目列表', async () => {
      mock.onGet('/api/v1/rd-projects').reply(200, {
        success: true,
        data: [{ id: 1, name: 'R&D Project 1' }],
      });

      const response = await rdProjectApi.list({ status: 'IN_PROGRESS' });

      expect(response.status).toBe(200);
    });

    it('create() - 应该创建研发项目', async () => {
      const project = { name: 'New R&D Project', category_id: 1 };
      mock.onPost('/api/v1/rd-projects').reply(201, {
        success: true,
        data: { id: 1, ...project },
      });

      const response = await rdProjectApi.create(project);

      expect(response.status).toBe(201);
    });

    it('approve() - 应该审批研发项目', async () => {
      const approval = { approved: true, comment: 'Approved' };
      mock.onPut('/api/v1/rd-projects/1/approve').reply(200, {
        success: true,
        data: { status: 'APPROVED' },
      });

      const response = await rdProjectApi.approve(1, approval);

      expect(response.status).toBe(200);
    });

    it('getCosts() - 应该获取研发费用', async () => {
      mock.onGet('/api/v1/rd-costs').reply(200, {
        success: true,
        data: [{ id: 1, amount: 10000 }],
      });

      const response = await rdProjectApi.getCosts({ project_id: 1 });

      expect(response.status).toBe(200);
    });

    it('calculateLaborCost() - 应该计算人工成本', async () => {
      const data = { project_id: 1, period: '2024-01' };
      mock.onPost('/api/v1/rd-costs/calc-labor').reply(200, {
        success: true,
        data: { labor_cost: 50000 },
      });

      const response = await rdProjectApi.calculateLaborCost(data);

      expect(response.status).toBe(200);
    });

    it('getCostSummary() - 应该获取费用汇总', async () => {
      mock.onGet('/api/v1/rd-projects/1/cost-summary').reply(200, {
        success: true,
        data: { total_cost: 100000 },
      });

      const response = await rdProjectApi.getCostSummary(1);

      expect(response.status).toBe(200);
    });

    it('uploadDocument() - 应该上传文档', async () => {
      const formData = new FormData();
      formData.append('file', new Blob(['test']), 'doc.pdf');

      mock.onPost('/api/v1/rd-projects/1/documents/upload').reply(200, {
        success: true,
        data: { id: 1, filename: 'doc.pdf' },
      });

      const response = await rdProjectApi.uploadDocument(1, formData);

      expect(response.status).toBe(200);
    });
  });

  describe('rdReportApi - 研发报表API', () => {
    it('getAuxiliaryLedger() - 应该获取辅助账', async () => {
      mock.onGet('/api/v1/reports/rd-auxiliary-ledger').reply(200, {
        success: true,
        data: { total: 500000 },
      });

      const response = await rdReportApi.getAuxiliaryLedger({ year: 2024 });

      expect(response.status).toBe(200);
    });

    it('getDeductionDetail() - 应该获取加计扣除明细', async () => {
      mock.onGet('/api/v1/reports/rd-deduction-detail').reply(200, {
        success: true,
        data: { deduction_amount: 750000 },
      });

      const response = await rdReportApi.getDeductionDetail({ year: 2024 });

      expect(response.status).toBe(200);
    });

    it('getHighTechReport() - 应该获取高新企业报表', async () => {
      mock.onGet('/api/v1/reports/rd-high-tech').reply(200, {
        success: true,
        data: { total_rd_expense: 1000000 },
      });

      const response = await rdReportApi.getHighTechReport({ year: 2024 });

      expect(response.status).toBe(200);
    });

    it('getIntensityReport() - 应该获取研发投入强度', async () => {
      mock.onGet('/api/v1/reports/rd-intensity').reply(200, {
        success: true,
        data: { intensity: 0.08 },
      });

      const response = await rdReportApi.getIntensityReport({ year: 2024 });

      expect(response.status).toBe(200);
    });

    it('exportReport() - 应该导出研发报表', async () => {
      mock.onGet('/api/v1/reports/rd-export').reply(200, new Blob());

      const response = await rdReportApi.exportReport({
        year: 2024,
        format: 'excel',
      });

      expect(response.status).toBe(200);
    });
  });

  describe('engineersApi - 工程师API', () => {
    it('getProgressVisibility() - 应该获取项目进度可见性', async () => {
      mock.onGet('/api/v1/engineers/projects/1/progress-visibility').reply(200, {
        success: true,
        data: { departments: [] },
      });

      const response = await engineersApi.getProgressVisibility(1);

      expect(response.status).toBe(200);
    });
  });

  describe('错误处理', () => {
    it('应该处理404错误', async () => {
      mock.onGet('/api/v1/projects/project-reviews/999').reply(404, {
        success: false,
        message: 'Review not found',
      });

      await expect(projectReviewApi.get(999)).rejects.toThrow();
    });

    it('应该处理验证错误', async () => {
      mock.onPost('/api/v1/rd-projects').reply(422, {
        success: false,
        message: 'Validation failed',
        errors: { name: ['Name is required'] },
      });

      await expect(rdProjectApi.create({})).rejects.toThrow();
    });

    it('应该处理权限错误', async () => {
      mock.onPost('/api/v1/technical-reviews/1/issues').reply(403, {
        success: false,
        message: 'Permission denied',
      });

      await expect(
        technicalReviewApi.createIssue(1, { title: 'Test' })
      ).rejects.toThrow();
    });

    it('应该处理网络错误', async () => {
      mock.onGet('/api/v1/rd-projects').networkError();

      await expect(rdProjectApi.list()).rejects.toThrow();
    });
  });
});
