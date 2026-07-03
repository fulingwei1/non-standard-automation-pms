import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import IssueDetail from "../IssueDetail";
import { issueApi } from "../../../services/api/issues";

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return actual;
});

vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }) => (
      <div {...props}>{children}</div>
    ),
  },
}));

vi.mock("../../../components/layout", () => ({
  PageHeader: ({ actions, subtitle, title }) => (
    <header>
      <h1>{title}</h1>
      <p>{subtitle}</p>
      {actions}
    </header>
  ),
}));

vi.mock("../../../services/api/issues", () => ({
  issueApi: {
    get: vi.fn(),
    getFollowUps: vi.fn(),
  },
}));

describe("IssueDetail", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders backend uppercase issue severity and status as business labels", async () => {
    issueApi.get.mockResolvedValue({
      data: {
        id: 47,
        issue_no: "IS-TR-047",
        title: "技术评审问题：夹具定位偏移",
        description: "PDR评审发现夹具定位基准存在偏移风险",
        category: "TECHNICAL",
        severity: "MAJOR",
        status: "CLOSED",
        assignee_name: "王工",
        reporter_name: "张三",
        created_at: "2026-06-21T10:00:00",
        updated_at: "2026-06-22T10:00:00",
        project_name: "FCT项目",
      },
    });
    issueApi.getFollowUps.mockResolvedValue({ data: { items: [] } });

    render(
      <MemoryRouter initialEntries={["/issues/47"]}>
        <Routes>
          <Route path="/issues/:id" element={<IssueDetail />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByText("技术评审问题：夹具定位偏移")).toBeInTheDocument();
    expect(screen.getByText("主要")).toBeInTheDocument();
    expect(screen.getByText("已关闭")).toBeInTheDocument();
    expect(screen.queryByText("待处理")).not.toBeInTheDocument();
    expect(screen.getByText("张三")).toBeInTheDocument();
  });
});
