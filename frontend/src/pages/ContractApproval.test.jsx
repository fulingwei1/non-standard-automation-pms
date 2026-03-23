import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

vi.mock("../services/api", () => ({
  contractApi: {
    list: vi.fn(),
    approvalAction: vi.fn(),
  },
  // formatCurrencyCompact 是源码中 import 的工具函数
  formatCurrencyCompact: vi.fn((v) => `¥${v}`),
}));

import { contractApi } from "../services/api";
import { MemoryRouter } from 'react-router-dom';
import ContractApproval from './ContractApproval';

function renderPage() {
  return render(
    <MemoryRouter>
      <ContractApproval />
    </MemoryRouter>,
  );
}

describe("ContractApproval page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("approves a pending item and moves it to history", async () => {
    const pendingItem = {
      id: 1,
      type: "contract",
      priority: "high",
      title: "合同A",
      customerName: "客户A",
      customerShort: "客户A",
      projectName: "项目A",
      submitter: "张三",
      submitTime: "2026-01-01 10:00",
      totalAmount: 100000,
    };

    contractApi.list.mockImplementation(({ approval_status }) => {
      if (approval_status === "pending") {
        return Promise.resolve({ data: { items: [pendingItem] } });
      }
      if (approval_status === "completed") {
        return Promise.resolve({ data: { items: [] } });
      }
      return Promise.resolve({ data: { items: [] } });
    });

    contractApi.approvalAction.mockResolvedValue({ data: { status: "OK" } });

    renderPage();

    // 等待初始数据加载
    const matches = await screen.findAllByText("合同A");
    expect(matches.length).toBeGreaterThan(0);

    // 点击"审批"按钮打开详情弹窗
    const approvalButtons = screen.getAllByRole("button").filter(b => b.textContent.trim() === "审批");
    expect(approvalButtons.length).toBeGreaterThan(0);
    await userEvent.click(approvalButtons[0]);
    await screen.findByText("审批详情");

    // 点击"批准"按钮（不填写意见，直接批准）
    const approveButton = screen.getAllByRole("button").find(b => b.textContent.trim() === "批准");
    await userEvent.click(approveButton);

    // 验证 API 调用（未填写意见时 comment 为 undefined，因为 "" || undefined = undefined）
    await waitFor(() => {
      expect(contractApi.approvalAction).toHaveBeenCalledWith(1, {
        action: "APPROVE",
        comment: undefined,
      });
    });

    // 验证待审批数量减少，历史增加（Dialog 桩不支持 open 控制，跳过关闭断言）
    await waitFor(() => {
      // PageHeader description 包含更新后的数量
      const header = screen.getByTestId("page-header");
      expect(header.getAttribute("description")).toMatch(/已审批: 1项/);
    });
  });

  it("rejects a pending item and moves it to history", async () => {
    const pendingItem = {
      id: 2,
      type: "contract",
      priority: "medium",
      title: "合同B",
      customerName: "客户B",
      customerShort: "客户B",
      projectName: "项目B",
      submitter: "李四",
      submitTime: "2026-01-02 11:00",
      totalAmount: 50000,
    };

    contractApi.list.mockImplementation(({ approval_status }) => {
      if (approval_status === "pending") {
        return Promise.resolve({ data: { items: [pendingItem] } });
      }
      if (approval_status === "completed") {
        return Promise.resolve({ data: { items: [] } });
      }
      return Promise.resolve({ data: { items: [] } });
    });

    contractApi.approvalAction.mockResolvedValue({ data: { status: "OK" } });

    renderPage();

    const matchesB = await screen.findAllByText("合同B");
    expect(matchesB.length).toBeGreaterThan(0);

    // 点击"审批"按钮
    const approvalButtons = screen.getAllByRole("button").filter(b => b.textContent.trim() === "审批");
    await userEvent.click(approvalButtons[0]);
    await screen.findByText("审批详情");

    // 点击"拒绝"
    const rejectButton = screen.getAllByRole("button").find(b => b.textContent.trim() === "拒绝");
    await userEvent.click(rejectButton);

    // 验证 API 调用（拒绝时默认 comment 为 "审批驳回"）
    await waitFor(() => {
      expect(contractApi.approvalAction).toHaveBeenCalledWith(2, {
        action: "REJECT",
        comment: "审批驳回",
      });
    });

    // 验证历史增加（Dialog 桩不支持 open 控制，跳过关闭断言）
    await waitFor(() => {
      const header = screen.getByTestId("page-header");
      expect(header.getAttribute("description")).toMatch(/已审批: 1项/);
    });
  });

  it("shows error and keeps item pending when approval API fails", async () => {
    const pendingItem = {
      id: 3,
      type: "contract",
      priority: "low",
      title: "合同C",
      customerName: "客户C",
      customerShort: "客户C",
      projectName: "项目C",
      submitter: "王五",
      submitTime: "2026-01-03 12:00",
      totalAmount: 12345,
    };

    contractApi.list.mockImplementation(({ approval_status }) => {
      if (approval_status === "pending") {
        return Promise.resolve({ data: { items: [pendingItem] } });
      }
      if (approval_status === "completed") {
        return Promise.resolve({ data: { items: [] } });
      }
      return Promise.resolve({ data: { items: [] } });
    });

    contractApi.approvalAction.mockRejectedValue(new Error("network error"));

    renderPage();

    const matchesC = await screen.findAllByText("合同C");
    expect(matchesC.length).toBeGreaterThan(0);

    // 点击"审批"按钮
    const approvalButtons = screen.getAllByRole("button").filter(b => b.textContent.trim() === "审批");
    await userEvent.click(approvalButtons[0]);
    await screen.findByText("审批详情");

    // 点击"批准"
    const approveButton = screen.getAllByRole("button").find(b => b.textContent.trim() === "批准");
    await userEvent.click(approveButton);

    // 验证 API 调用
    await waitFor(() => {
      expect(contractApi.approvalAction).toHaveBeenCalledWith(3, {
        action: "APPROVE",
        comment: undefined,
      });
    });

    // 弹窗应保持打开并显示错误信息
    expect(screen.getByText("审批详情")).toBeInTheDocument();
    expect(
      screen.getByText("审批通过失败，请稍后重试"),
    ).toBeInTheDocument();

    // 待审批项仍然存在
    expect(screen.getAllByText("合同C").length).toBeGreaterThan(0);

    // 审批历史数量应为 0（合同C 未被移到历史）
    const historyText = screen.getAllByText(/审批历史/).find(el => el.textContent.includes("0"));
    expect(historyText).toBeTruthy();
  });
});
