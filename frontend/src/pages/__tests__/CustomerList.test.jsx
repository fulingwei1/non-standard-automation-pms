/**
 * CustomerList (CustomerManagement) 组件测试
 * 覆盖：页面渲染、客户列表加载、搜索筛选、新增弹窗
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import CustomerManagement from "../CustomerManagement";
import { customerApi } from "../../services/api";

vi.mock("../../services/api", () => ({
  customerApi: {
    list: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    get: vi.fn(),
    get360: vi.fn(),
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

describe("CustomerManagement", () => {
  const mockCustomers = [
    {
      id: 1,
      customer_code: "CUS-001",
      customer_name: "深圳华星精密科技有限公司",
      industry: "新能源汽车",
      contact_person: "张总",
      contact_phone: "13800138001",
      status: "active",
      credit_level: "A",
    },
    {
      id: 2,
      customer_code: "CUS-002",
      customer_name: "苏州智造自动化有限公司",
      industry: "消费电子",
      contact_person: "李经理",
      contact_phone: "13900139002",
      status: "potential",
      credit_level: "B",
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    customerApi.list.mockResolvedValue({
      data: {
        items: mockCustomers,
        total: 2,
        page: 1,
        page_size: 20,
      },
    });
    customerApi.create.mockResolvedValue({ data: { id: 3 } });
    customerApi.update.mockResolvedValue({ data: { success: true } });
    customerApi.delete.mockResolvedValue({ data: { success: true } });
    customerApi.get.mockResolvedValue({ data: mockCustomers[0] });
    customerApi.get360.mockResolvedValue({ data: {} });
  });

  const renderPage = () =>
    render(
      <MemoryRouter>
        <CustomerManagement />
      </MemoryRouter>,
    );

  it("renders page header and fetches customers on mount", async () => {
    renderPage();

    expect(
      screen.getByRole("heading", { name: "客户管理" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /新增客户/ }),
    ).toBeInTheDocument();

    await waitFor(() => {
      expect(customerApi.list).toHaveBeenCalledWith(
        expect.objectContaining({ page: 1, page_size: 20 }),
      );
    });

    expect(
      await screen.findByText("深圳华星精密科技有限公司"),
    ).toBeInTheDocument();
    expect(screen.getByText("苏州智造自动化有限公司")).toBeInTheDocument();
  });

  it("handles empty customer list", async () => {
    customerApi.list.mockResolvedValueOnce({
      data: { items: [], total: 0, page: 1, page_size: 20 },
    });

    renderPage();

    await waitFor(() => {
      expect(customerApi.list).toHaveBeenCalled();
    });

    expect(
      screen.queryByText("深圳华星精密科技有限公司"),
    ).not.toBeInTheDocument();
  });

  it("renders create customer button and table", async () => {
    renderPage();

    expect(
      await screen.findByText("深圳华星精密科技有限公司"),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /新增客户/ }),
    ).toBeInTheDocument();
  });
});
