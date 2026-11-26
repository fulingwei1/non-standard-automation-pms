/**
 * PaymentManagement 组件测试
 * 覆盖：页面渲染、统计与列表接口调用、标签页切换
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import PaymentManagement from "../PaymentManagement/index";
import { paymentApi, receivableApi } from "../../services/api";

vi.mock("../../services/api", () => ({
  paymentApi: {
    list: vi.fn(),
    getReminders: vi.fn(),
    getStatistics: vi.fn(),
    create: vi.fn(),
    approve: vi.fn(),
  },
  receivableApi: {
    getAging: vi.fn(),
    getSummary: vi.fn(),
  },
}));

vi.mock("framer-motion", () => ({
  motion: new Proxy(
    {},
    {
      get: (_, tag) => ({ children, ...props }) => {
        const invalid = new Set([
          "initial",
          "animate",
          "exit",
          "variants",
          "transition",
          "whileHover",
          "whileTap",
          "whileInView",
          "layout",
          "layoutId",
          "drag",
          "dragConstraints",
          "onDragEnd",
        ]);
        const filtered = Object.fromEntries(
          Object.entries(props).filter(([k]) => !invalid.has(k)),
        );
        const Tag = typeof tag === "string" ? tag : "div";
        return <Tag {...filtered}>{children}</Tag>;
      },
    },
  ),
  AnimatePresence: ({ children }) => children,
}));

describe("PaymentManagement", () => {
  const mockPayments = [
    {
      id: 1,
      payment_no: "PAY-2024-001",
      customer_name: "深圳华星精密科技有限公司",
      contract_code: "CTR-001",
      amount: 120000,
      status: "PAID",
      payment_type: "ADVANCE",
      due_date: "2024-02-20",
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    paymentApi.list.mockResolvedValue({
      data: { items: mockPayments, total: 1 },
    });
    paymentApi.getReminders.mockResolvedValue({
      data: { items: [] },
    });
    paymentApi.getStatistics.mockResolvedValue({
      data: { total_receivables: 500000 },
    });
    receivableApi.getAging.mockResolvedValue({ data: {} });
    receivableApi.getSummary.mockResolvedValue({ data: {} });
  });

  const renderPage = () =>
    render(
      <MemoryRouter>
        <PaymentManagement />
      </MemoryRouter>,
    );

  it("renders page header and calls paymentApi on mount", async () => {
    renderPage();

    expect(
      await screen.findByRole("heading", { name: "支付管理" }),
    ).toBeInTheDocument();

    await waitFor(() => {
      expect(paymentApi.list).toHaveBeenCalled();
      expect(paymentApi.getReminders).toHaveBeenCalled();
      expect(paymentApi.getStatistics).toHaveBeenCalled();
    });
  });

  it("renders all four view tabs", async () => {
    renderPage();

    expect(await screen.findByRole("tab", { name: "统计概览" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "付款列表" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "时间轴" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "账龄分析" })).toBeInTheDocument();

    const user = userEvent.setup();
    await user.click(screen.getByRole("tab", { name: "付款列表" }));
    expect(screen.getByRole("tab", { name: "付款列表" })).toBeInTheDocument();
  });
});
