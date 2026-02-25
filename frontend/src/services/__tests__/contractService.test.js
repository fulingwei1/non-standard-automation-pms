/**
 * Contract Service 测试
 * 测试范围：
 * - 获取合同列表
 * - 获取合同详情
 * - 创建合同
 * - 更新合同
 * - 删除合同
 * - 获取合同历史记录
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import MockAdapter from 'axios-mock-adapter';
import * as contractService from '../contractService';
import apiClient from '../apiClient';

describe('Contract Service', () => {
  let mock;

  beforeEach(() => {
    mock = new MockAdapter(apiClient);
    vi.clearAllMocks();
  });

  afterEach(() => {
    mock.reset();
  });

  describe('getContracts()', () => {
    it('应该获取合同列表', async () => {
      const mockData = {
        items: [
          { id: 1, contract_no: 'C001', status: 'ACTIVE' },
          { id: 2, contract_no: 'C002', status: 'SIGNED' },
        ],
        total: 2,
      };

      mock.onGet('/api/v1/sales/contracts').reply(200, mockData);

      const result = await contractService.getContracts();

      expect(result).toEqual(mockData);
      expect(result.items).toHaveLength(2);
      expect(mock.history.get).toHaveLength(1);
    });

    it('应该支持查询参数', async () => {
      mock.onGet('/api/v1/sales/contracts').reply(200, { items: [], total: 0 });

      await contractService.getContracts({
        status: 'ACTIVE',
        page: 1,
        page_size: 10,
      });

      expect(mock.history.get[0].params).toEqual({
        status: 'ACTIVE',
        page: 1,
        page_size: 10,
      });
    });

    it('应该处理空参数', async () => {
      mock.onGet('/api/v1/sales/contracts').reply(200, { items: [], total: 0 });

      await contractService.getContracts();

      expect(mock.history.get).toHaveLength(1);
    });
  });

  describe('getContractDetail()', () => {
    it('应该获取合同详情', async () => {
      const mockData = {
        id: 1,
        contract_no: 'C001',
        customer_id: 1,
        customer_name: 'Test Company',
        value: 100000,
        status: 'SIGNED',
        signed_date: '2024-01-15',
      };

      mock.onGet('/api/v1/sales/contracts/1').reply(200, mockData);

      const result = await contractService.getContractDetail(1);

      expect(result).toEqual(mockData);
      expect(result.contract_no).toBe('C001');
      expect(result.value).toBe(100000);
    });

    it('应该处理合同不存在', async () => {
      mock.onGet('/api/v1/sales/contracts/999').reply(404, {
        message: 'Contract not found',
      });

      await expect(contractService.getContractDetail(999)).rejects.toThrow();
    });
  });

  describe('createContract()', () => {
    it('应该创建合同', async () => {
      const contractData = {
        customer_id: 1,
        quote_id: 1,
        title: 'Test Contract',
        value: 100000,
      };

      const mockResponse = {
        id: 1,
        contract_no: 'C001',
        ...contractData,
        status: 'DRAFT',
      };

      mock.onPost('/api/v1/sales/contracts').reply(201, mockResponse);

      const result = await contractService.createContract(contractData);

      expect(result).toEqual(mockResponse);
      expect(result.status).toBe('DRAFT');
      expect(mock.history.post).toHaveLength(1);
      expect(JSON.parse(mock.history.post[0].data)).toEqual(contractData);
    });

    it('应该处理验证错误', async () => {
      mock.onPost('/api/v1/sales/contracts').reply(422, {
        message: 'Validation failed',
        errors: {
          customer_id: ['Customer is required'],
        },
      });

      await expect(contractService.createContract({})).rejects.toThrow();
    });

    it('应该处理权限错误', async () => {
      mock.onPost('/api/v1/sales/contracts').reply(403, {
        message: 'Permission denied',
      });

      await expect(
        contractService.createContract({ customer_id: 1 })
      ).rejects.toThrow();
    });
  });

  describe('updateContract()', () => {
    it('应该更新合同', async () => {
      const updates = {
        title: 'Updated Contract',
        value: 120000,
      };

      const mockResponse = {
        id: 1,
        contract_no: 'C001',
        ...updates,
      };

      mock.onPut('/api/v1/sales/contracts/1').reply(200, mockResponse);

      const result = await contractService.updateContract(1, updates);

      expect(result).toEqual(mockResponse);
      expect(result.title).toBe('Updated Contract');
      expect(mock.history.put).toHaveLength(1);
      expect(JSON.parse(mock.history.put[0].data)).toEqual(updates);
    });

    it('应该处理合同不存在', async () => {
      mock.onPut('/api/v1/sales/contracts/999').reply(404, {
        message: 'Contract not found',
      });

      await expect(
        contractService.updateContract(999, { title: 'Test' })
      ).rejects.toThrow();
    });

    it('应该处理已签署合同不可修改', async () => {
      mock.onPut('/api/v1/sales/contracts/1').reply(400, {
        message: 'Cannot update signed contract',
      });

      await expect(
        contractService.updateContract(1, { value: 100000 })
      ).rejects.toThrow();
    });
  });

  describe('deleteContract()', () => {
    it('应该删除合同', async () => {
      const mockResponse = {
        message: 'Contract deleted successfully',
      };

      mock.onDelete('/api/v1/sales/contracts/1').reply(200, mockResponse);

      const result = await contractService.deleteContract(1);

      expect(result).toEqual(mockResponse);
      expect(mock.history.delete).toHaveLength(1);
    });

    it('应该处理合同不存在', async () => {
      mock.onDelete('/api/v1/sales/contracts/999').reply(404, {
        message: 'Contract not found',
      });

      await expect(contractService.deleteContract(999)).rejects.toThrow();
    });

    it('应该处理已签署合同不可删除', async () => {
      mock.onDelete('/api/v1/sales/contracts/1').reply(400, {
        message: 'Cannot delete signed contract',
      });

      await expect(contractService.deleteContract(1)).rejects.toThrow();
    });
  });

  describe('getContractHistory()', () => {
    it('应该获取合同历史记录', async () => {
      const mockData = {
        items: [
          {
            id: 1,
            action: 'CREATED',
            user: 'John Doe',
            timestamp: '2024-01-01T10:00:00Z',
          },
          {
            id: 2,
            action: 'UPDATED',
            user: 'Jane Smith',
            timestamp: '2024-01-05T14:30:00Z',
          },
        ],
        total: 2,
      };

      mock.onGet('/api/v1/sales/contracts/1/history').reply(200, mockData);

      const result = await contractService.getContractHistory(1);

      expect(result).toEqual(mockData);
      expect(result.items).toHaveLength(2);
    });

    it('应该支持分页参数', async () => {
      mock
        .onGet('/api/v1/sales/contracts/1/history')
        .reply(200, { items: [], total: 0 });

      await contractService.getContractHistory(1, {
        page: 2,
        page_size: 20,
      });

      expect(mock.history.get[0].params).toEqual({
        page: 2,
        page_size: 20,
      });
    });

    it('应该支持时间范围过滤', async () => {
      mock
        .onGet('/api/v1/sales/contracts/1/history')
        .reply(200, { items: [], total: 0 });

      await contractService.getContractHistory(1, {
        start_date: '2024-01-01',
        end_date: '2024-12-31',
      });

      expect(mock.history.get[0].params).toEqual({
        start_date: '2024-01-01',
        end_date: '2024-12-31',
      });
    });

    it('应该处理合同不存在', async () => {
      mock.onGet('/api/v1/sales/contracts/999/history').reply(404, {
        message: 'Contract not found',
      });

      await expect(contractService.getContractHistory(999)).rejects.toThrow();
    });
  });

  describe('错误处理', () => {
    it('应该处理网络错误', async () => {
      mock.onGet('/api/v1/sales/contracts').networkError();

      await expect(contractService.getContracts()).rejects.toThrow();
    });

    it('应该处理服务器错误', async () => {
      mock.onGet('/api/v1/sales/contracts/1').reply(500, {
        message: 'Internal Server Error',
      });

      await expect(contractService.getContractDetail(1)).rejects.toThrow();
    });

    it('应该处理超时错误', async () => {
      mock.onGet('/api/v1/sales/contracts').timeout();

      await expect(contractService.getContracts()).rejects.toThrow();
    });

    it('应该处理401未授权错误', async () => {
      mock.onGet('/api/v1/sales/contracts').reply(401, {
        message: 'Unauthorized',
      });

      await expect(contractService.getContracts()).rejects.toThrow();
    });
  });

  describe('默认导出', () => {
    it('应该导出所有方法', () => {
      expect(contractService.default).toEqual({
        getContracts: contractService.getContracts,
        getContractDetail: contractService.getContractDetail,
        createContract: contractService.createContract,
        updateContract: contractService.updateContract,
        deleteContract: contractService.deleteContract,
        getContractHistory: contractService.getContractHistory,
      });
    });
  });
});
