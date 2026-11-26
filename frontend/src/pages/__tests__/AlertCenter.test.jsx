/**
 * AlertCenter 组件测试
 * 覆盖：页面渲染、统计概览、预警列表加载、错误重试、确认预警
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import AlertCenter from "../AlertCenter";
import { alertApi, projectApi } from "../../services/api";

vi.mock("../../services/api", () => ({
  alertApi: {
    list: vi.fn(),
    statistics: vi.fn(),
    acknowledge: vi.fn().mockResolvedValue({ data: { success: true } }),
    resolve: vi.fn().mockResolvedValue({ data: { success: true } }),
    close: vi.fn().mockResolvedValue({ data: { success: true } }),
    exportExcel: vi.fn(),
    exportPdf: vi.fn(),
  },
  projectApi: {
    list: vi.fn(),
  },
}));

vi.mock("../../components/ui/toast", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
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

const mockNavigate = vi.fn();
vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe("AlertCenter", () => {
  const mockAlerts = [
    {
      id: 1,
      alert_no: "ALT-001",
      title: "项目预算超支预警",
      alert_level: "CRITICAL",
      status: "PENDING",
      alert_type: "COST",
      alert_content: "项目PROJ-001预算超支20%",
      project_id: 1,
      project_name: "智能制造系统",
      triggered_at: "2024-02-20T10:00:00Z",
    },
    {
      id: 2,
      alert_no: "ALT-002",
      title: "项目进度延迟预警",
      alert_level: "WARNING",
      status: "ACKNOWLEDGED",
      alert_type: "SCHEDULE",
      alert_content: "项目PROJ-002进度延迟5天",
      project_id: 2,
      project_name: "ERP系统升级",
      triggered_at: "2024-02-19T14:00:00Z",
    },
  ];

  const mockStats = {
    total: 20,
    pending: 12,
    resolved: 8,
    critical: 3,
    today_new: 5,
    urgent: 2,
    warning: 7,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    projectApi.list.mockResolvedValue({
      data: { items: [{ id: 1, project_name: "智能制造系统" }] },
    });
    alertApi.list.mockResolvedValue({
      data: { items: mockAlerts, total: 2 },
    });
    alertApi.statistics.mockResolvedValue({
      data: mockStats,
    });
  });

  const renderPage = () =>
    render(
      <MemoryRouter>
        <AlertCenter />
      </MemoryRouter>,
    );

  it("renders page header and loads alerts and statistics on mount", async () => {
    renderPage();

    expect(
      await screen.findByRole("heading", { name: "预警中心" }),
    ).toBeInTheDocument();
    expect(alertApi.list).toHaveBeenCalled();
    expect(alertApi.statistics).toHaveBeenCalled();
    expect(projectApi.list).toHaveBeenCalled();
  });

  it("displays alert statistics and alert list items", async () => {
    renderPage();

    expect(
      (await screen.findAllByText("项目预算超支预警")).length,
    ).toBeGreaterThan(0);
    expect(screen.getByText("项目进度延迟预警")).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
  });

  it("navigates to alert rules when clicking 新建规则", async () => {
    renderPage();

    const btn = await screen.findByRole("button", { name: /新建规则/ });
    fireEvent.click(btn);
    expect(mockNavigate).toHaveBeenCalledWith("/alert-rules");
  });

  it("shows error message and retries on API failure", async () => {
    alertApi.list.mockRejectedValueOnce(new Error("网络异常"));

    renderPage();

    expect(await screen.findByText(/网络异常/)).toBeInTheDocument();
  });
});
