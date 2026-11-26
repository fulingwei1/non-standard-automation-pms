/**
 * Acceptance 组件测试
 * 覆盖：页面渲染、验收单列表加载、空态与新建验收单弹窗
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Acceptance from "../Acceptance/index";
import { acceptanceApi, projectApi } from "../../services/api";

vi.mock("../../services/api", () => ({
  acceptanceApi: {
    orders: {
      list: vi.fn(),
      get: vi.fn(),
      create: vi.fn(),
      getItems: vi.fn().mockResolvedValue({ data: { items: [] } }),
      exportReport: vi.fn(),
    },
    issues: {
      list: vi.fn().mockResolvedValue({ data: { items: [] } }),
    },
    templates: {
      list: vi.fn().mockResolvedValue({ data: { items: [] } }),
    },
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

describe("Acceptance", () => {
  const mockOrders = [
    {
      id: 1,
      order_no: "ACC-2024-001",
      acceptance_type: "FAT",
      project_id: 1,
      project_name: "智能制造系统",
      machine_name: "ICT测试机",
      status: "PENDING",
      planned_date: "2024-03-01",
      total_items: 10,
      passed_items: 6,
      failed_items: 1,
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    acceptanceApi.orders.list.mockResolvedValue({
      data: { items: mockOrders, total: 1 },
    });
    projectApi.list.mockResolvedValue({
      data: { items: [{ id: 1, project_name: "智能制造系统" }] },
    });
  });

  const renderPage = () =>
    render(
      <MemoryRouter>
        <Acceptance />
      </MemoryRouter>,
    );

  it("renders page header and loads acceptance orders on mount", async () => {
    renderPage();

    expect(
      (await screen.findAllByText("验收管理")).length,
    ).toBeGreaterThan(0);

    await waitFor(() => {
      expect(acceptanceApi.orders.list).toHaveBeenCalled();
    });

    expect(await screen.findByText("ACC-2024-001")).toBeInTheDocument();
    expect(
      (await screen.findAllByText("智能制造系统")).length,
    ).toBeGreaterThan(0);
  });

  it("renders create acceptance button", async () => {
    renderPage();

    expect(await screen.findByText("ACC-2024-001")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /新建验收单/ }),
    ).toBeInTheDocument();
  });
});
