/**
 * IssueManagement 组件测试
 * 覆盖：页面渲染、数据加载、空态与错误态、新建问题弹窗
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import IssueManagement from "../IssueManagement";
import { issueApi } from "../../services/api";

vi.mock("../../services/api", () => ({
  issueApi: {
    getIssues: vi.fn(),
    getStats: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    assign: vi.fn(),
    resolve: vi.fn(),
    verify: vi.fn(),
    close: vi.fn(),
    cancel: vi.fn(),
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

describe("IssueManagement", () => {
  const mockIssues = [
    {
      id: 1,
      issue_no: "ISS-2024-001",
      title: "系统登录失败",
      description: "用户无法正常登录系统",
      project_name: "智能制造系统",
      severity: "MAJOR",
      priority: "HIGH",
      status: "OPEN",
      category: "PROJECT",
      issue_type: "DEFECT",
      reporter_name: "张三",
      assignee_name: "李四",
      created_at: "2024-02-15",
      due_date: "2024-02-20",
    },
    {
      id: 2,
      issue_no: "ISS-2024-002",
      title: "数据同步延迟",
      description: "同步超过30秒",
      project_name: "ERP系统升级",
      severity: "MINOR",
      priority: "MEDIUM",
      status: "IN_PROGRESS",
      category: "TECHNICAL",
      issue_type: "BUG",
      reporter_name: "王五",
      assignee_name: "赵六",
      created_at: "2024-02-10",
      due_date: "2024-02-25",
    },
  ];

  const mockStats = {
    total: 2,
    open: 1,
    processing: 1,
    resolved: 0,
    closed: 0,
    blocking: 0,
    overdue: 0,
    by_status: { OPEN: 1, IN_PROGRESS: 1 },
    by_severity: { MAJOR: 1, MINOR: 1 },
  };

  beforeEach(() => {
    vi.clearAllMocks();
    issueApi.getIssues.mockResolvedValue({
      data: { items: mockIssues, total: 2 },
    });
    issueApi.getStats.mockResolvedValue({
      data: mockStats,
    });
    issueApi.create.mockResolvedValue({
      data: { id: 3, title: "新测试问题" },
    });
  });

  const renderPage = (props = {}) =>
    render(
      <MemoryRouter>
        <IssueManagement {...props} />
      </MemoryRouter>,
    );

  it("renders page header and loads issues and stats on mount", async () => {
    renderPage();

    expect(
      screen.getByRole("heading", { name: "问题异常" }),
    ).toBeInTheDocument();

    await waitFor(() => {
      expect(issueApi.getIssues).toHaveBeenCalledWith({});
      expect(issueApi.getStats).toHaveBeenCalledWith({ timeRange: "week" });
    });

    expect(await screen.findByText("系统登录失败")).toBeInTheDocument();
    expect(screen.getByText("数据同步延迟")).toBeInTheDocument();
  });

  it("hides PageHeader when embedded is true", async () => {
    renderPage({ embedded: true });

    await waitFor(() => {
      expect(issueApi.getIssues).toHaveBeenCalled();
    });

    expect(
      screen.queryByRole("heading", { name: "问题异常" }),
    ).not.toBeInTheDocument();
  });

  it("shows empty hint when no issues exist", async () => {
    issueApi.getIssues.mockResolvedValueOnce({ data: { items: [], total: 0 } });

    renderPage();

    expect(
      await screen.findByText("数据库暂无问题数据"),
    ).toBeInTheDocument();
  });

  it("shows error banner when loading issues or stats fails", async () => {
    issueApi.getIssues.mockRejectedValueOnce(new Error("服务器错误"));
    issueApi.getStats.mockRejectedValueOnce(new Error("统计失败"));

    renderPage();

    expect(
      await screen.findByText(/问题列表加载失败：API错误: 服务器错误/),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/统计数据加载失败：API错误: 统计失败/),
    ).toBeInTheDocument();
  });

  it("opens create dialog and submits a new issue", async () => {
    renderPage();

    const createBtn = screen.getAllByRole("button", { name: /新建问题/ })[0];
    fireEvent.click(createBtn);

    fireEvent.change(screen.getByLabelText("问题标题 *"), {
      target: { value: "新增设备异常" },
    });
    fireEvent.change(screen.getByLabelText("问题描述 *"), {
      target: { value: "传感器无响应" },
    });

    fireEvent.click(screen.getByRole("button", { name: "创建问题" }));

    await waitFor(() => {
      expect(issueApi.create).toHaveBeenCalledWith(
        expect.objectContaining({
          title: "新增设备异常",
          description: "传感器无响应",
        }),
      );
    });
  });
});
