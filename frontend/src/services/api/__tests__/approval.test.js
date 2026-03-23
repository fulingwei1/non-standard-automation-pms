/**
 * Approval API 测试
 * 测试范围：
 * - 统一审批系统API
 * - 审批提交、通过、驳回、委托、撤回
 * - 专用审批方法 (ECN, Quote, Contract, Invoice)
 * - 审批状态和进度计算
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import MockAdapter from 'axios-mock-adapter';

// 取消 setupTests.js 对 client 的全局 mock，使用真实 axios 实例 + MockAdapter
vi.unmock('../client.js');
vi.unmock('../client');

describe('Approval API', () => {
  let api, mock;
  let submitApproval, approveApproval, rejectApproval, delegateApproval, withdrawApproval;
  let getApprovalHistory, getApprovalDetail, getMyApprovalTasks;
  let submitEcnApproval, submitQuoteApproval, submitContractApproval, submitInvoiceApproval;
  let APPROVAL_STATUS, getStatusConfig, calculateProgress;

  beforeEach(async () => {
    vi.resetModules();

    const clientModule = await import('../client.js');
    api = clientModule.default || clientModule.api;

    const approvalModule = await import('../approval.js');
    submitApproval = approvalModule.submitApproval;
    approveApproval = approvalModule.approveApproval;
    rejectApproval = approvalModule.rejectApproval;
    delegateApproval = approvalModule.delegateApproval;
    withdrawApproval = approvalModule.withdrawApproval;
    getApprovalHistory = approvalModule.getApprovalHistory;
    getApprovalDetail = approvalModule.getApprovalDetail;
    getMyApprovalTasks = approvalModule.getMyApprovalTasks;
    submitEcnApproval = approvalModule.submitEcnApproval;
    submitQuoteApproval = approvalModule.submitQuoteApproval;
    submitContractApproval = approvalModule.submitContractApproval;
    submitInvoiceApproval = approvalModule.submitInvoiceApproval;
    APPROVAL_STATUS = approvalModule.APPROVAL_STATUS;
    getStatusConfig = approvalModule.getStatusConfig;
    calculateProgress = approvalModule.calculateProgress;

    mock = new MockAdapter(api);
    vi.clearAllMocks();
  });

  afterEach(() => {
    if (mock) {
      mock.restore();
    }
  });

  describe('submitApproval() - 提交审批', () => {
    it('应该成功提交审批', async () => {
      const approvalData = {
        entity_type: 'QUOTE',
        entity_id: 1,
        title: '报价审批',
        summary: '需要审批报价单',
        urgency: 'NORMAL',
        cc_user_ids: [1, 2],
      };

      mock.onPost('/api/v1/approvals/instances/submit').reply(201, {
        success: true,
        data: {
          instance_id: 1,
          status: 'PENDING',
          ...approvalData,
        },
      });

      const response = await submitApproval(approvalData);

      expect(response.status).toBe(201);
      expect(mock.history.post).toHaveLength(1);
      expect(JSON.parse(mock.history.post[0].data)).toEqual(approvalData);
    });

    it('应该处理必填字段缺失错误', async () => {
      mock.onPost('/api/v1/approvals/instances/submit').reply(422, {
        success: false,
        message: 'Validation failed',
        errors: {
          entity_type: ['Entity type is required'],
          entity_id: ['Entity ID is required'],
        },
      });

      await expect(submitApproval({})).rejects.toThrow();
    });
  });

  describe('approveApproval() - 通过审批', () => {
    it('应该成功通过审批', async () => {
      const comment = 'Approved, looks good';

      mock.onPost('/api/v1/approvals/tasks/1/approve').reply(200, {
        success: true,
        data: {
          instance_id: 1,
          status: 'APPROVED',
        },
      });

      const response = await approveApproval(1, comment);

      expect(response.status).toBe(200);
      expect(JSON.parse(mock.history.post[0].data)).toEqual({
        decision: 'APPROVE',
        comment: comment,
      });
    });

    it('应该处理无权限审批错误', async () => {
      mock.onPost('/api/v1/approvals/tasks/1/approve').reply(403, {
        success: false,
        message: 'Not authorized to approve',
      });

      await expect(approveApproval(1, 'Test')).rejects.toThrow();
    });
  });

  describe('rejectApproval() - 驳回审批', () => {
    it('应该成功驳回审批', async () => {
      const comment = 'Needs more information';

      mock.onPost('/api/v1/approvals/tasks/1/reject').reply(200, {
        success: true,
        data: {
          instance_id: 1,
          status: 'REJECTED',
        },
      });

      const response = await rejectApproval(1, comment);

      expect(response.status).toBe(200);
      expect(JSON.parse(mock.history.post[0].data)).toEqual({
        decision: 'REJECT',
        comment: comment,
      });
    });
  });

  describe('delegateApproval() - 委托审批', () => {
    it('应该成功委托审批', async () => {
      const delegateToId = 2;
      const comment = 'Delegating to manager';

      mock.onPost('/api/v1/approvals/delegates').reply(200, {
        success: true,
        data: {
          instance_id: 1,
          status: 'DELEGATED',
          delegate_to_id: delegateToId,
        },
      });

      const response = await delegateApproval(1, delegateToId, comment);

      expect(response.status).toBe(200);
      expect(JSON.parse(mock.history.post[0].data)).toEqual({
        instance_id: 1,
        delegate_to_id: delegateToId,
        comment: comment,
      });
    });

    it('应该处理无效的被委托人错误', async () => {
      mock.onPost('/api/v1/approvals/delegates').reply(400, {
        success: false,
        message: 'Invalid delegate user',
      });

      await expect(delegateApproval(1, 999, 'Test')).rejects.toThrow();
    });
  });

  describe('withdrawApproval() - 撤回审批', () => {
    it('应该成功撤回审批', async () => {
      const comment = 'Needs modification';

      mock.onPost('/api/v1/approvals/instances/1/withdraw').reply(200, {
        success: true,
        data: {
          instance_id: 1,
          status: 'WITHDRAWN',
        },
      });

      const response = await withdrawApproval(1, comment);

      expect(response.status).toBe(200);
      expect(JSON.parse(mock.history.post[0].data)).toEqual({
        decision: 'WITHDRAW',
        comment: comment,
      });
    });

    it('应该处理已完成审批无法撤回错误', async () => {
      mock.onPost('/api/v1/approvals/instances/1/withdraw').reply(400, {
        success: false,
        message: 'Cannot withdraw completed approval',
      });

      await expect(withdrawApproval(1, 'Test')).rejects.toThrow();
    });
  });

  describe('getApprovalHistory() - 查询审批历史', () => {
    it('应该成功获取审批历史', async () => {
      const mockHistory = [
        {
          id: 1,
          action: 'SUBMITTED',
          user_id: 1,
          timestamp: '2024-01-01T10:00:00Z',
        },
        {
          id: 2,
          action: 'APPROVED',
          user_id: 2,
          timestamp: '2024-01-01T11:00:00Z',
        },
      ];

      mock.onGet('/api/v1/approvals/tasks/instances/1/comments').reply(200, {
        success: true,
        data: mockHistory,
      });

      const response = await getApprovalHistory(1);

      expect(response.status).toBe(200);
      expect(response.data.data).toHaveLength(2);
    });
  });

  describe('getApprovalDetail() - 查询审批详情', () => {
    it('应该成功获取审批详情', async () => {
      const mockDetail = {
        instance_id: 1,
        entity_type: 'QUOTE',
        entity_id: 1,
        status: 'IN_PROGRESS',
        current_level: 2,
        total_levels: 3,
      };

      mock.onGet('/api/v1/approvals/instances/1').reply(200, {
        success: true,
        data: mockDetail,
      });

      const response = await getApprovalDetail(1);

      expect(response.status).toBe(200);
      expect(response.data.data.instance_id).toBe(1);
    });

    it('应该处理审批不存在错误', async () => {
      mock.onGet('/api/v1/approvals/instances/999').reply(404, {
        success: false,
        message: 'Approval not found',
      });

      await expect(getApprovalDetail(999)).rejects.toThrow();
    });
  });

  describe('getMyApprovalTasks() - 查询我的待审批任务', () => {
    it('应该成功获取待审批任务列表', async () => {
      const mockTasks = [
        {
          instance_id: 1,
          title: 'Quote Approval',
          urgency: 'URGENT',
          submitted_at: '2024-01-01T10:00:00Z',
        },
        {
          instance_id: 2,
          title: 'Contract Approval',
          urgency: 'NORMAL',
          submitted_at: '2024-01-02T10:00:00Z',
        },
      ];

      mock.onGet('/api/v1/approvals/pending/mine').reply(200, {
        success: true,
        data: mockTasks,
      });

      const response = await getMyApprovalTasks();

      expect(response.status).toBe(200);
      expect(response.data.data).toHaveLength(2);
    });
  });

  describe('专用审批方法', () => {
    it('submitEcnApproval() - 应该提交ECN审批', async () => {
      mock.onPost('/api/v1/approvals/instances/submit').reply(201, {
        success: true,
        data: { instance_id: 1 },
      });

      const response = await submitEcnApproval(
        1,
        'ECN审批',
        'ECN变更需要审批',
        'URGENT',
        [1, 2]
      );

      expect(response.status).toBe(201);
      const requestData = JSON.parse(mock.history.post[0].data);
      expect(requestData.entity_type).toBe('ECN');
      expect(requestData.entity_id).toBe(1);
      expect(requestData.urgency).toBe('URGENT');
    });

    it('submitQuoteApproval() - 应该提交报价审批', async () => {
      mock.onPost('/api/v1/approvals/instances/submit').reply(201, {
        success: true,
        data: { instance_id: 1 },
      });

      const response = await submitQuoteApproval(1, '报价审批', '需要审批');

      expect(response.status).toBe(201);
      const requestData = JSON.parse(mock.history.post[0].data);
      expect(requestData.entity_type).toBe('QUOTE');
      expect(requestData.entity_id).toBe(1);
    });

    it('submitContractApproval() - 应该提交合同审批', async () => {
      mock.onPost('/api/v1/approvals/instances/submit').reply(201, {
        success: true,
        data: { instance_id: 1 },
      });

      const response = await submitContractApproval(1);

      expect(response.status).toBe(201);
      const requestData = JSON.parse(mock.history.post[0].data);
      expect(requestData.entity_type).toBe('CONTRACT');
      expect(requestData.title).toBe('合同审批');
    });

    it('submitInvoiceApproval() - 应该提交发票审批', async () => {
      mock.onPost('/api/v1/approvals/instances/submit').reply(201, {
        success: true,
        data: { instance_id: 1 },
      });

      const response = await submitInvoiceApproval(1);

      expect(response.status).toBe(201);
      const requestData = JSON.parse(mock.history.post[0].data);
      expect(requestData.entity_type).toBe('INVOICE');
      expect(requestData.title).toBe('发票审批');
    });
  });

  describe('APPROVAL_STATUS - 审批状态常量', () => {
    it('应该定义所有审批状态', () => {
      expect(APPROVAL_STATUS.PENDING).toBe('PENDING');
      expect(APPROVAL_STATUS.IN_PROGRESS).toBe('IN_PROGRESS');
      expect(APPROVAL_STATUS.APPROVED).toBe('APPROVED');
      expect(APPROVAL_STATUS.REJECTED).toBe('REJECTED');
      expect(APPROVAL_STATUS.WITHDRAWN).toBe('WITHDRAWN');
      expect(APPROVAL_STATUS.DELEGATED).toBe('DELEGATED');
    });
  });

  describe('getStatusConfig() - 获取状态配置', () => {
    it('应该返回PENDING状态配置', () => {
      const config = getStatusConfig(APPROVAL_STATUS.PENDING);

      expect(config.label).toBe('待审批');
      expect(config.color).toBe('orange');
      expect(config.icon).toBe('⏳');
    });

    it('应该返回IN_PROGRESS状态配置', () => {
      const config = getStatusConfig(APPROVAL_STATUS.IN_PROGRESS);

      expect(config.label).toBe('审批中');
      expect(config.color).toBe('blue');
      expect(config.icon).toBe('🔄');
    });

    it('应该返回APPROVED状态配置', () => {
      const config = getStatusConfig(APPROVAL_STATUS.APPROVED);

      expect(config.label).toBe('已通过');
      expect(config.color).toBe('green');
      expect(config.icon).toBe('✅');
    });

    it('应该返回REJECTED状态配置', () => {
      const config = getStatusConfig(APPROVAL_STATUS.REJECTED);

      expect(config.label).toBe('已驳回');
      expect(config.color).toBe('red');
      expect(config.icon).toBe('❌');
    });

    it('应该返回WITHDRAWN状态配置', () => {
      const config = getStatusConfig(APPROVAL_STATUS.WITHDRAWN);

      expect(config.label).toBe('已撤回');
      expect(config.color).toBe('gray');
      expect(config.icon).toBe('↩️');
    });

    it('应该返回DELEGATED状态配置', () => {
      const config = getStatusConfig(APPROVAL_STATUS.DELEGATED);

      expect(config.label).toBe('已委托');
      expect(config.color).toBe('purple');
      expect(config.icon).toBe('👤');
    });

    it('应该处理未知状态', () => {
      const config = getStatusConfig('UNKNOWN_STATUS');

      expect(config.label).toBe('未知');
      expect(config.color).toBe('gray');
      expect(config.icon).toBe('❓');
    });
  });

  describe('calculateProgress() - 计算审批进度', () => {
    it('应该正确计算进度百分比', () => {
      expect(calculateProgress(1, 3)).toBe(33);
      expect(calculateProgress(2, 3)).toBe(67);
      expect(calculateProgress(3, 3)).toBe(100);
    });

    it('应该处理完成状态', () => {
      expect(calculateProgress(3, 3)).toBe(100);
    });

    it('应该处理开始状态', () => {
      expect(calculateProgress(0, 3)).toBe(0);
    });

    it('应该处理除零错误', () => {
      expect(calculateProgress(1, 0)).toBe(0);
      expect(calculateProgress(5, null)).toBe(0);
      expect(calculateProgress(5, undefined)).toBe(0);
    });

    it('应该四舍五入到整数', () => {
      expect(calculateProgress(1, 7)).toBe(14); // 14.28... -> 14
      expect(calculateProgress(5, 7)).toBe(71); // 71.42... -> 71
    });
  });

  describe('错误处理', () => {
    it('应该处理网络错误', async () => {
      mock.onPost('/api/v1/approvals/instances/submit').networkError();

      await expect(
        submitApproval({
          entity_type: 'QUOTE',
          entity_id: 1,
        })
      ).rejects.toThrow();
    });

    it('应该处理服务器错误', async () => {
      mock.onPost('/api/v1/approvals/instances/submit').reply(500, {
        success: false,
        message: 'Internal Server Error',
      });

      await expect(
        submitApproval({
          entity_type: 'QUOTE',
          entity_id: 1,
        })
      ).rejects.toThrow();
    });

    it('应该处理超时错误', async () => {
      mock.onGet('/api/v1/approvals/pending/mine').timeout();

      await expect(getMyApprovalTasks()).rejects.toThrow();
    });

    it('应该处理业务逻辑错误', async () => {
      mock.onPost('/api/v1/approvals/tasks/1/approve').reply(400, {
        success: false,
        message: 'Approval already processed',
      });

      await expect(approveApproval(1, 'Test')).rejects.toThrow();
    });
  });
});
