/**
 * HR API 测试
 * 测试范围：
 * - employeeApi: 员工管理
 * - departmentApi: 部门管理
 * - hrApi: 人力资源管理
 * - performanceApi: 绩效管理
 * - bonusApi: 奖金管理
 * - timesheetApi: 工时管理
 * - qualificationApi: 任职资格
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import MockAdapter from 'axios-mock-adapter';

describe('HR API', () => {
  let api, mock;
  let employeeApi, departmentApi, hrApi, performanceApi, bonusApi;
  let timesheetApi, qualificationApi, staffMatchingApi, hourlyRateApi;

  beforeEach(async () => {
    vi.resetModules();
    
    const clientModule = await import('../client.js');
    api = clientModule.default || clientModule.api;
    
    const hrModule = await import('../hr.js');
    employeeApi = hrModule.employeeApi;
    departmentApi = hrModule.departmentApi;
    hrApi = hrModule.hrApi;
    performanceApi = hrModule.performanceApi;
    bonusApi = hrModule.bonusApi;
    timesheetApi = hrModule.timesheetApi;
    qualificationApi = hrModule.qualificationApi;
    staffMatchingApi = hrModule.staffMatchingApi;
    hourlyRateApi = hrModule.hourlyRateApi;
    
    mock = new MockAdapter(api);
    vi.clearAllMocks();
  });

  afterEach(() => {
    if (mock) {
      mock.restore();
    }
  });

  describe('employeeApi - 员工API', () => {
    it('list() - 应该获取员工列表', async () => {
      mock.onGet('/api/v1/employees').reply(200, {
        success: true,
        data: [{ id: 1, name: 'John Doe' }],
      });

      const response = await employeeApi.list({ department_id: 1 });

      expect(response.status).toBe(200);
    });

    it('create() - 应该创建员工', async () => {
      const employee = { name: 'Jane Doe', email: 'jane@example.com' };
      mock.onPost('/api/v1/employees').reply(201, {
        success: true,
        data: { id: 1, ...employee },
      });

      const response = await employeeApi.create(employee);

      expect(response.status).toBe(201);
    });

    it('update() - 应该更新员工信息', async () => {
      const updates = { position: 'Senior Engineer' };
      mock.onPut('/api/v1/employees/1').reply(200, {
        success: true,
        data: { id: 1, ...updates },
      });

      const response = await employeeApi.update(1, updates);

      expect(response.status).toBe(200);
    });

    it('getStatistics() - 应该获取员工统计', async () => {
      mock.onGet('/api/v1/employees/statistics').reply(200, {
        success: true,
        data: { total: 100, active: 95 },
      });

      const response = await employeeApi.getStatistics({ year: 2024 });

      expect(response.status).toBe(200);
    });
  });

  describe('departmentApi - 部门API', () => {
    it('list() - 应该获取部门列表', async () => {
      mock.onGet('/api/v1/org/departments').reply(200, {
        success: true,
        data: [{ id: 1, name: 'Engineering' }],
      });

      const response = await departmentApi.list({});

      expect(response.status).toBe(200);
    });

    it('create() - 应该创建部门', async () => {
      const dept = { name: 'New Department', manager_id: 1 };
      mock.onPost('/api/v1/org/departments').reply(201, {
        success: true,
        data: { id: 1, ...dept },
      });

      const response = await departmentApi.create(dept);

      expect(response.status).toBe(201);
    });

    it('delete() - 应该删除部门', async () => {
      mock.onDelete('/api/v1/org/departments/1').reply(204);

      const response = await departmentApi.delete(1);

      expect(response.status).toBe(204);
    });
  });

  describe('hrApi - 人力资源API', () => {
    it('transactions.list() - 应该获取人事事务列表', async () => {
      mock.onGet('/api/v1/hr/transactions').reply(200, {
        success: true,
        data: [{ id: 1, type: 'ONBOARD' }],
      });

      const response = await hrApi.transactions.list({ status: 'PENDING' });

      expect(response.status).toBe(200);
    });

    it('transactions.create() - 应该创建人事事务', async () => {
      const transaction = { employee_id: 1, type: 'PROMOTION' };
      mock.onPost('/api/v1/hr/transactions').reply(201, {
        success: true,
        data: { id: 1, ...transaction },
      });

      const response = await hrApi.transactions.create(transaction);

      expect(response.status).toBe(201);
    });

    it('contracts.list() - 应该获取合同列表', async () => {
      mock.onGet('/api/v1/hr/contracts').reply(200, {
        success: true,
        data: [{ id: 1, employee_id: 1 }],
      });

      const response = await hrApi.contracts.list({ status: 'ACTIVE' });

      expect(response.status).toBe(200);
    });

    it('contracts.renew() - 应该续签合同', async () => {
      const renewData = { new_end_date: '2025-12-31' };
      mock.onPost('/api/v1/hr/contracts/1/renew').reply(200, {
        success: true,
        data: { ...renewData },
      });

      const response = await hrApi.contracts.renew(1, renewData);

      expect(response.status).toBe(200);
    });

    it('contracts.getExpiring() - 应该获取即将到期合同', async () => {
      mock.onGet('/api/v1/hr/contracts/expiring').reply(200, {
        success: true,
        data: [{ id: 1, end_date: '2024-12-31' }],
      });

      const response = await hrApi.contracts.getExpiring({ days: 30 });

      expect(response.status).toBe(200);
    });

    it('dashboard.overview() - 应该获取仪表板概览', async () => {
      mock.onGet('/api/v1/hr/dashboard/overview').reply(200, {
        success: true,
        data: { total_employees: 100 },
      });

      const response = await hrApi.dashboard.overview();

      expect(response.status).toBe(200);
    });
  });

  describe('performanceApi - 绩效API', () => {
    it('createMonthlySummary() - 应该创建月度总结', async () => {
      const summary = { period: '2024-01', content: 'Monthly work summary' };
      mock.onPost('/api/v1/performance/monthly-summary').reply(201, {
        success: true,
        data: { id: 1, ...summary },
      });

      const response = await performanceApi.createMonthlySummary(summary);

      expect(response.status).toBe(201);
    });

    it('getMyPerformance() - 应该获取我的绩效', async () => {
      mock.onGet('/api/v1/performance/my-performance').reply(200, {
        success: true,
        data: { score: 95 },
      });

      const response = await performanceApi.getMyPerformance();

      expect(response.status).toBe(200);
    });

    it('getEvaluationTasks() - 应该获取待评价任务', async () => {
      mock.onGet('/api/v1/performance/evaluation-tasks').reply(200, {
        success: true,
        data: [{ id: 1, employee_id: 1 }],
      });

      const response = await performanceApi.getEvaluationTasks({ status: 'PENDING' });

      expect(response.status).toBe(200);
    });

    it('submitEvaluation() - 应该提交评价', async () => {
      const evaluation = { score: 90, comment: 'Good performance' };
      mock.onPost('/api/v1/performance/evaluation/1').reply(200, {
        success: true,
        data: { ...evaluation },
      });

      const response = await performanceApi.submitEvaluation(1, evaluation);

      expect(response.status).toBe(200);
    });

    it('getWeightConfig() - 应该获取权重配置', async () => {
      mock.onGet('/api/v1/performance/weight-config').reply(200, {
        success: true,
        data: { weights: {} },
      });

      const response = await performanceApi.getWeightConfig();

      expect(response.status).toBe(200);
    });

    it('calculateIntegratedPerformance() - 应该计算融合绩效', async () => {
      mock.onPost('/api/v1/performance/calculate-integrated').reply(200, {
        success: true,
        data: { calculated: true },
      });

      const response = await performanceApi.calculateIntegratedPerformance({
        period: '2024-01',
      });

      expect(response.status).toBe(200);
    });
  });

  describe('bonusApi - 奖金API', () => {
    it('getMyBonus() - 应该获取我的奖金', async () => {
      mock.onGet('/api/v1/bonus/my').reply(200, {
        success: true,
        data: { total_bonus: 10000 },
      });

      const response = await bonusApi.getMyBonus();

      expect(response.status).toBe(200);
    });

    it('getCalculations() - 应该获取奖金计算记录', async () => {
      mock.onGet('/api/v1/bonus/calculations').reply(200, {
        success: true,
        data: [{ id: 1, amount: 5000 }],
      });

      const response = await bonusApi.getCalculations({ year: 2024 });

      expect(response.status).toBe(200);
    });

    it('calculateSalesBonus() - 应该计算销售奖金', async () => {
      const data = { employee_id: 1, period: '2024-Q1' };
      mock.onPost('/api/v1/bonus/calculate/sales').reply(200, {
        success: true,
        data: { bonus_amount: 15000 },
      });

      const response = await bonusApi.calculateSalesBonus(data);

      expect(response.status).toBe(200);
    });

    it('calculateProjectBonus() - 应该计算项目奖金', async () => {
      const data = { project_id: 1 };
      mock.onPost('/api/v1/bonus/calculate/project').reply(200, {
        success: true,
        data: { bonus_amount: 20000 },
      });

      const response = await bonusApi.calculateProjectBonus(data);

      expect(response.status).toBe(200);
    });
  });

  describe('timesheetApi - 工时API', () => {
    it('list() - 应该获取工时记录列表', async () => {
      mock.onGet('/api/v1/timesheets').reply(200, {
        success: true,
        data: [{ id: 1, hours: 8 }],
      });

      const response = await timesheetApi.list({ date: '2024-01-01' });

      expect(response.status).toBe(200);
    });

    it('create() - 应该创建工时记录', async () => {
      const timesheet = { project_id: 1, hours: 8, date: '2024-01-01' };
      mock.onPost('/api/v1/timesheets').reply(201, {
        success: true,
        data: { id: 1, ...timesheet },
      });

      const response = await timesheetApi.create(timesheet);

      expect(response.status).toBe(201);
    });

    it('batchCreate() - 应该批量创建工时', async () => {
      const timesheets = [
        { project_id: 1, hours: 8, date: '2024-01-01' },
        { project_id: 1, hours: 8, date: '2024-01-02' },
      ];
      mock.onPost('/api/v1/timesheets/batch').reply(201, {
        success: true,
        data: timesheets,
      });

      const response = await timesheetApi.batchCreate(timesheets);

      expect(response.status).toBe(201);
    });

    it('submitWeek() - 应该提交周工时', async () => {
      const weekData = { week: '2024-W01', timesheets: [] };
      mock.onPost('/api/v1/timesheets/week/submit').reply(200, {
        success: true,
        data: { submitted: true },
      });

      const response = await timesheetApi.submitWeek(weekData);

      expect(response.status).toBe(200);
    });

    it('approve() - 应该审批工时', async () => {
      const approval = { approved: true, comment: 'Approved' };
      mock.onPut('/api/v1/timesheets/1/approve').reply(200, {
        success: true,
        data: { status: 'APPROVED' },
      });

      const response = await timesheetApi.approve(1, approval);

      expect(response.status).toBe(200);
    });

    it('getStatistics() - 应该获取工时统计', async () => {
      mock.onGet('/api/v1/timesheets/statistics').reply(200, {
        success: true,
        data: { total_hours: 160 },
      });

      const response = await timesheetApi.getStatistics({ month: '2024-01' });

      expect(response.status).toBe(200);
    });

    it('getHrReport() - 应该获取HR报表', async () => {
      mock.onGet('/api/v1/timesheets/reports/hr').reply(200, {
        success: true,
        data: { report: [] },
      });

      const response = await timesheetApi.getHrReport({
        month: '2024-01',
        format: 'json',
      });

      expect(response.status).toBe(200);
    });

    it('getHrReport() - 应该导出Excel格式', async () => {
      mock.onGet('/api/v1/timesheets/reports/hr').reply(200, new Blob());

      const response = await timesheetApi.getHrReport({
        month: '2024-01',
        format: 'excel',
      });

      expect(response.status).toBe(200);
    });
  });

  describe('qualificationApi - 任职资格API', () => {
    it('getLevels() - 应该获取等级列表', async () => {
      mock.onGet('/api/v1/qualifications/levels').reply(200, {
        success: true,
        data: [{ id: 1, name: 'Level 1' }],
      });

      const response = await qualificationApi.getLevels({ position_type: 'ENGINEER' });

      expect(response.status).toBe(200);
    });

    it('createLevel() - 应该创建等级', async () => {
      const level = { name: 'Senior Engineer', position_type: 'ENGINEER' };
      mock.onPost('/api/v1/qualifications/levels').reply(201, {
        success: true,
        data: { id: 1, ...level },
      });

      const response = await qualificationApi.createLevel(level);

      expect(response.status).toBe(201);
    });

    it('getModels() - 应该获取能力模型', async () => {
      mock.onGet('/api/v1/qualifications/models').reply(200, {
        success: true,
        data: [{ id: 1, competencies: [] }],
      });

      const response = await qualificationApi.getModels({ position_type: 'ENGINEER' });

      expect(response.status).toBe(200);
    });

    it('certifyEmployee() - 应该认证员工', async () => {
      const certification = { level_id: 1, assessment_score: 85 };
      mock.onPost('/api/v1/qualifications/employees/1/certify').reply(200, {
        success: true,
        data: { certified: true },
      });

      const response = await qualificationApi.certifyEmployee(1, certification);

      expect(response.status).toBe(200);
    });

    it('promoteEmployee() - 应该晋升员工', async () => {
      const promotion = { new_level_id: 2 };
      mock.onPost('/api/v1/qualifications/employees/1/promote').reply(200, {
        success: true,
        data: { promoted: true },
      });

      const response = await qualificationApi.promoteEmployee(1, promotion);

      expect(response.status).toBe(200);
    });
  });

  describe('staffMatchingApi - 人员匹配API', () => {
    it('getStaffingNeeds() - 应该获取人员需求', async () => {
      mock.onGet('/api/v1/staff-matching/staffing-needs').reply(200, {
        success: true,
        data: [{ id: 1, position: 'Engineer' }],
      });

      const response = await staffMatchingApi.getStaffingNeeds({ status: 'OPEN' });

      expect(response.status).toBe(200);
    });

    it('executeMatching() - 应该执行AI匹配', async () => {
      mock.onPost('/api/v1/staff-matching/matching/execute/1').reply(200, {
        success: true,
        data: { request_id: 'abc123' },
      });

      const response = await staffMatchingApi.executeMatching(1, { top_n: 5 });

      expect(response.status).toBe(200);
    });

    it('getMatchingResults() - 应该获取匹配结果', async () => {
      mock.onGet('/api/v1/staff-matching/matching/results/1').reply(200, {
        success: true,
        data: { candidates: [] },
      });

      const response = await staffMatchingApi.getMatchingResults(1, 'abc123');

      expect(response.status).toBe(200);
    });

    it('getDashboard() - 应该获取仪表板', async () => {
      mock.onGet('/api/v1/staff-matching/dashboard').reply(200, {
        success: true,
        data: { open_needs: 5 },
      });

      const response = await staffMatchingApi.getDashboard();

      expect(response.status).toBe(200);
    });
  });

  describe('hourlyRateApi - 小时费率API', () => {
    it('list() - 应该获取费率列表', async () => {
      mock.onGet('/api/v1/hourly-rates').reply(200, {
        success: true,
        data: [{ id: 1, rate: 100 }],
      });

      const response = await hourlyRateApi.list({ user_id: 1 });

      expect(response.status).toBe(200);
    });

    it('getUserHourlyRate() - 应该获取用户小时费率', async () => {
      mock.onGet('/api/v1/hourly-rates/users/1/hourly-rate').reply(200, {
        success: true,
        data: { rate: 100 },
      });

      const response = await hourlyRateApi.getUserHourlyRate(1, '2024-01-01');

      expect(response.status).toBe(200);
    });

    it('create() - 应该创建费率', async () => {
      const rate = { user_id: 1, rate: 100, effective_date: '2024-01-01' };
      mock.onPost('/api/v1/hourly-rates').reply(201, {
        success: true,
        data: { id: 1, ...rate },
      });

      const response = await hourlyRateApi.create(rate);

      expect(response.status).toBe(201);
    });
  });

  describe('错误处理', () => {
    it('应该处理404错误', async () => {
      mock.onGet('/api/v1/employees/999').reply(404, {
        success: false,
        message: 'Employee not found',
      });

      await expect(employeeApi.get(999)).rejects.toThrow();
    });

    it('应该处理验证错误', async () => {
      mock.onPost('/api/v1/employees').reply(422, {
        success: false,
        message: 'Validation failed',
        errors: { name: ['Name is required'] },
      });

      await expect(employeeApi.create({})).rejects.toThrow();
    });

    it('应该处理权限错误', async () => {
      mock.onDelete('/api/v1/org/departments/1').reply(403, {
        success: false,
        message: 'Permission denied',
      });

      await expect(departmentApi.delete(1)).rejects.toThrow();
    });

    it('应该处理网络错误', async () => {
      mock.onGet('/api/v1/timesheets').networkError();

      await expect(timesheetApi.list()).rejects.toThrow();
    });

    it('应该处理超时错误', async () => {
      mock.onGet('/api/v1/performance/my-performance').timeout();

      await expect(performanceApi.getMyPerformance()).rejects.toThrow();
    });
  });
});
