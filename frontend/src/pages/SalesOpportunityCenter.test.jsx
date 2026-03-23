/**
 * SalesOpportunityCenter 组件单元测试
 *
 * 测试范围：
 * - 页面渲染
 * - Tab 切换
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from 'react-router-dom';
import SalesOpportunityCenter from './SalesOpportunityCenter';

// Mock 子组件
vi.mock("./LeadManagement", () => ({
  default: () => <div data-testid="lead-management">线索管理组件</div>,
}));

vi.mock("./OpportunityManagement", () => ({
  default: () => <div data-testid="opportunity-management">商机管理组件</div>,
}));

// Mock TabbedCenterPage 组件
vi.mock("../components/layout/TabbedCenterPage", () => ({
  default: ({ title, description, tabs }) => (
    <div data-testid="tabbed-center-page">
      <h1>{title}</h1>
      <p>{description}</p>
      <div role="tablist">
        {tabs.map((tab) => (
          <button key={tab.value} role="tab">
            {tab.label}
          </button>
        ))}
      </div>
      <div>{tabs[0]?.render()}</div>
    </div>
  ),
}));

// 测试包装器
const renderWithRouter = (ui) => {
  return render(<BrowserRouter>{ui}</BrowserRouter>);
};

describe("SalesOpportunityCenter 组件", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("页面渲染", () => {
    it("应该渲染页面标题", async () => {
      renderWithRouter(<SalesOpportunityCenter />);

      await waitFor(() => {
        expect(screen.getByText("商机中心")).toBeInTheDocument();
      });
    });

    it("应该渲染页面描述", async () => {
      renderWithRouter(<SalesOpportunityCenter />);

      await waitFor(() => {
        expect(screen.getByText("统一管理销售线索与商机推进")).toBeInTheDocument();
      });
    });

    it("应该渲染 Tab 导航", async () => {
      renderWithRouter(<SalesOpportunityCenter />);

      await waitFor(() => {
        expect(screen.getByRole("tab", { name: "线索管理" })).toBeInTheDocument();
        expect(screen.getByRole("tab", { name: "商机管理" })).toBeInTheDocument();
      });
    });

    it("应该渲染嵌入的子组件", async () => {
      renderWithRouter(<SalesOpportunityCenter />);

      await waitFor(() => {
        // 默认显示第一个 Tab 的内容（LeadManagement 全局 fallback testid 为 lowercase）
        expect(screen.getByTestId("leadmanagement")).toBeInTheDocument();
      });
    });
  });
});
