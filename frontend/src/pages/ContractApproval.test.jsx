import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";

vi.mock("../services/api", () => ({
  contractApi: {
    list: vi.fn(),
    approvalAction: vi.fn(),
  },
}));

import ContractApproval from "./ContractApproval.jsx";
import { contractApi } from "../services/api";

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

    // Wait for initial fetch + render
    await screen.findByText("合同A");

    // Open detail dialog
    await userEvent.click(screen.getByRole("button", { name: "审批" }));
    await screen.findByText("审批详情");

    // Fill comment
    await userEvent.type(
      screen.getByPlaceholderText("请输入审批意见..."),
      "同意，按当前条款执行",
    );

    // Approve
    await userEvent.click(screen.getByRole("button", { name: "批准" }));

    await waitFor(() => {
      expect(contractApi.approvalAction).toHaveBeenCalledWith(1, {
        action: "APPROVE",
        comment: "同意，按当前条款执行",
      });
    });

    // Dialog should close
    await waitFor(() => {
      expect(screen.queryByText("审批详情")).not.toBeInTheDocument();
    });

    // Switch to history tab and verify item is there
    await userEvent.click(screen.getByRole("button", { name: "审批历史 (1)" }));
    const historyTitle = await screen.findByText("合同A");
    expect(within(historyTitle.parentElement).getByText("已批准")).toBeInTheDocument();
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

    await screen.findByText("合同B");

    await userEvent.click(screen.getByRole("button", { name: "审批" }));
    await screen.findByText("审批详情");

    await userEvent.click(screen.getByRole("button", { name: "拒绝" }));

    await waitFor(() => {
      expect(contractApi.approvalAction).toHaveBeenCalledWith(2, {
        action: "REJECT",
        comment: "审批驳回",
      });
    });

    await userEvent.click(screen.getByRole("button", { name: "审批历史 (1)" }));
    const historyTitle = await screen.findByText("合同B");
    expect(within(historyTitle.parentElement).getByText("已拒绝")).toBeInTheDocument();
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

    await screen.findByText("合同C");

    await userEvent.click(screen.getByRole("button", { name: "审批" }));
    await screen.findByText("审批详情");

    await userEvent.click(screen.getByRole("button", { name: "批准" }));

    await waitFor(() => {
      expect(contractApi.approvalAction).toHaveBeenCalledWith(3, {
        action: "APPROVE",
        comment: undefined,
      });
    });

    // Dialog should remain open and show error
    expect(screen.getByText("审批详情")).toBeInTheDocument();
    expect(
      screen.getByText("审批通过失败，请稍后重试"),
    ).toBeInTheDocument();

    // Close dialog (dialog open will aria-hide the page)
    const dialog = screen.getByRole("dialog", { name: "审批详情" });
    await userEvent.click(within(dialog).getByRole("button", { name: "取消" }));

    // Item should still be pending; history should not include it
    expect(await screen.findByText("合同C")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "审批历史 (0)" }));
    expect(screen.queryByText("合同C")).not.toBeInTheDocument();
  });
});
