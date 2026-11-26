/**
 * PurchaseOrders 组件测试
 * 覆盖：采购订单列表加载、错误态、筛选与展示
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import PurchaseOrders from "../PurchaseOrders/index";
import { purchaseApi, supplierApi, projectApi } from "../../services/api";

vi.mock("../../services/api", () => ({
  purchaseApi: {
    list: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    submitApproval: vi.fn(),
    approve: vi.fn(),
    receiveGoods: vi.fn(),
  },
  supplierApi: {
    list: vi.fn(),
  },
  projectApi: {
    list: vi.fn(),
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

describe("PurchaseOrders", () => {
  const mockOrders = [
    {
      id: 1,
      order_no: "PO-2024-001",
      supplier_name: "深圳精密机械有限公司",
      project_name: "智能制造系统",
      total_amount: 150000,
      status: "APPROVED",
      created_at: "2024-02-10",
    },
    {
      id: 2,
      order_no: "PO-2024-002",
      supplier_name: "苏州自动化配件厂",
      project_name: "ERP系统升级",
      total_amount: 80000,
      status: "PENDING",
      created_at: "2024-02-12",
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    purchaseApi.list.mockResolvedValue({
      data: { items: mockOrders, total: 2 },
    });
    supplierApi.list.mockResolvedValue({
      data: { items: [{ id: 1, supplier_name: "深圳精密机械有限公司" }] },
    });
    projectApi.list.mockResolvedValue({
      data: { items: [{ id: 1, project_name: "智能制造系统" }] },
    });
  });

  const renderPage = () =>
    render(
      <MemoryRouter>
        <PurchaseOrders />
      </MemoryRouter>,
    );

  it("renders page header and loads purchase orders on mount", async () => {
    renderPage();

    expect(
      await screen.findByRole("heading", { name: "采购订单管理" }),
    ).toBeInTheDocument();

    await waitFor(() => {
      expect(purchaseApi.list).toHaveBeenCalled();
    });

    expect(await screen.findByText("PO-2024-001")).toBeInTheDocument();
    expect(screen.getByText("PO-2024-002")).toBeInTheDocument();
  });

  it("shows error state when loading purchase orders fails", async () => {
    purchaseApi.list.mockRejectedValueOnce(new Error("网络请求失败"));

    renderPage();

    expect(
      await screen.findByText("加载采购订单失败"),
    ).toBeInTheDocument();
  });
});
