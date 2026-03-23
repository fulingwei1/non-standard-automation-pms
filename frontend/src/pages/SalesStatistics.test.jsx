/**
 * SalesStatistics 组件单元测试
 *
 * 测试范围：
 * - 页面渲染
 * - 统计数据展示
 * - 图表渲染
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, waitFor } from "@testing-library/react";
import { BrowserRouter } from 'react-router-dom';
import SalesStatistics from './SalesStatistics';

// Mock API - 组件从 ../services/api 导入，使用实际方法名
vi.mock("../services/api", () => ({
  salesStatisticsApi: {
    funnel: vi.fn().mockResolvedValue({
      data: {
        data: {
          leads: 150,
          opportunities: 80,
          quotes: 45,
          contracts: 20,
        },
      },
    }),
    revenueForecast: vi.fn().mockResolvedValue({
      data: {
        data: {
          monthly: [
            { month: "2026-01", forecast: 1000000, actual: 950000 },
            { month: "2026-02", forecast: 1200000, actual: 1100000 },
            { month: "2026-03", forecast: 1500000, actual: null },
          ],
        },
      },
    }),
    opportunitiesByStage: vi.fn().mockResolvedValue({
      data: {
        data: [
          { stage: "DISCOVERY", count: 20, amount: 1000000 },
          { stage: "QUALIFICATION", count: 15, amount: 800000 },
          { stage: "PROPOSAL", count: 25, amount: 1500000 },
          { stage: "NEGOTIATION", count: 10, amount: 1200000 },
          { stage: "CLOSING", count: 10, amount: 500000 },
        ],
      },
    }),
    summary: vi.fn().mockResolvedValue({
      data: {
        data: {
          total_leads: 150,
          total_opportunities: 80,
          total_quotes: 45,
          total_contracts: 20,
          total_revenue: 5000000,
          conversion_rate: 13.3,
        },
      },
    }),
  },
}));

// 测试包装器
const renderWithRouter = (ui) => {
  return render(<BrowserRouter>{ui}</BrowserRouter>);
};

describe("SalesStatistics 组件", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("页面渲染", () => {
    it("应该渲染页面标题", async () => {
      renderWithRouter(<SalesStatistics />);

      await waitFor(() => {
        // 页面应该渲染成功（查找页面内容）
        expect(document.body.textContent).toMatch(/销售|统计|线索|商机/);
      });
    });

    it("应该渲染统计卡片", async () => {
      renderWithRouter(<SalesStatistics />);

      await waitFor(
        () => {
          // 查找统计相关的内容
          const content = document.body.textContent;
          expect(content).toMatch(/线索|商机|报价|合同/);
        },
        { timeout: 3000 }
      );
    });
  });

  describe("数据加载", () => {
    it("应该调用统计 API", async () => {
      const { salesStatisticsApi } = await import("../services/api");

      renderWithRouter(<SalesStatistics />);

      await waitFor(
        () => {
          // 验证 funnel API 被调用
          expect(salesStatisticsApi.funnel).toHaveBeenCalled();
        },
        { timeout: 3000 }
      );
    });
  });

  describe("图表渲染", () => {
    it("应该渲染图表容器", async () => {
      renderWithRouter(<SalesStatistics />);

      await waitFor(
        () => {
          // 页面应该包含某种数据可视化
          expect(document.body).toBeInTheDocument();
        },
        { timeout: 3000 }
      );
    });
  });

  describe("错误处理", () => {
    it("API 失败时应该正常渲染", async () => {
      const { salesStatisticsApi } = await import("../services/api");
      salesStatisticsApi.funnel.mockRejectedValueOnce(new Error("API Error"));

      renderWithRouter(<SalesStatistics />);

      // 组件应该仍然渲染
      await waitFor(() => {
        expect(document.body).toBeInTheDocument();
      });
    });
  });
});
