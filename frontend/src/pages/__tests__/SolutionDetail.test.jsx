import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import SolutionDetail from "../SolutionDetail";
import { useSolutionDetail } from "../SolutionDetail/hooks";

const navigateMock = vi.hoisted(() => vi.fn());

vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useNavigate: () => navigateMock,
  };
});

vi.mock("../SolutionDetail/hooks", () => ({
  useSolutionDetail: vi.fn(),
}));

vi.mock("framer-motion", () => ({
  motion: new Proxy(
    {},
    {
      get: (_, tag) => {
        const Tag = typeof tag === "string" ? tag : "div";
        return ({ children, ...props }) => {
          const motionProps = new Set([
            "initial",
            "animate",
            "exit",
            "variants",
            "transition",
            "whileHover",
            "whileTap",
            "layout",
          ]);
          const domProps = Object.fromEntries(
            Object.entries(props).filter(([key]) => !motionProps.has(key)),
          );
          return <Tag {...domProps}>{children}</Tag>;
        };
      },
    },
  ),
  AnimatePresence: ({ children }) => children,
}));

describe("SolutionDetail", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useSolutionDetail.mockReturnValue({
      activeTab: "overview",
      setActiveTab: vi.fn(),
      solution: null,
      loading: false,
      error: "方案不存在",
      costEstimate: null,
      submittingReview: false,
      reviewError: null,
      submitForReview: vi.fn(),
    });
  });

  it("keeps sales and project context when returning from a failed detail load", () => {
    render(
      <MemoryRouter
        initialEntries={[
          "/solutions/88?ticket_id=501&lead_id=2026&opportunity_id=2&project_id=42",
        ]}
      >
        <SolutionDetail />
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByRole("button", { name: "返回方案列表" }));

    expect(navigateMock).toHaveBeenCalledWith(
      "/presales/technical-solutions?tab=solutions&type=support&ticket_id=501&lead_id=2026&opportunity_id=2&project_id=42",
    );
  });

  it("keeps lead context when opening cost estimation from a solution detail", () => {
    useSolutionDetail.mockReturnValue({
      activeTab: "cost",
      setActiveTab: vi.fn(),
      solution: {
        id: 88,
        code: "SOL-20260607-001",
        name: "线索阶段方案",
        status: "draft",
        version: "V1.0",
        ticketId: 501,
        leadId: 2026,
        opportunityId: 2,
        projectId: 42,
      },
      loading: false,
      error: null,
      costEstimate: null,
      submittingReview: false,
      reviewError: null,
      submitForReview: vi.fn(),
    });

    render(
      <MemoryRouter>
        <SolutionDetail />
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByRole("button", { name: /去做成本估算/ }));

    expect(navigateMock).toHaveBeenCalledWith(
      "/presales/technical-solutions?tab=cost&solution_id=88&ticket_id=501&lead_id=2026&opportunity_id=2&project_id=42",
    );
  });

  it("uses URL context when opening cost estimation for a legacy solution without context fields", () => {
    useSolutionDetail.mockReturnValue({
      activeTab: "cost",
      setActiveTab: vi.fn(),
      solution: {
        id: 88,
        code: "SOL-20260607-001",
        name: "旧方案",
        status: "draft",
        version: "V1.0",
      },
      loading: false,
      error: null,
      costEstimate: null,
      submittingReview: false,
      reviewError: null,
      submitForReview: vi.fn(),
    });

    render(
      <MemoryRouter
        initialEntries={[
          "/solutions/88?ticket_id=501&lead_id=2026&opportunity_id=2&project_id=42",
        ]}
      >
        <SolutionDetail />
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByRole("button", { name: /去做成本估算/ }));

    expect(navigateMock).toHaveBeenCalledWith(
      "/presales/technical-solutions?tab=cost&solution_id=88&ticket_id=501&lead_id=2026&opportunity_id=2&project_id=42",
    );
  });

  it("uses URL context when returning from a legacy solution without context fields", () => {
    useSolutionDetail.mockReturnValue({
      activeTab: "overview",
      setActiveTab: vi.fn(),
      solution: {
        id: 88,
        code: "SOL-20260607-001",
        name: "旧方案",
        status: "draft",
        version: "V1.0",
      },
      loading: false,
      error: null,
      costEstimate: null,
      submittingReview: false,
      reviewError: null,
      submitForReview: vi.fn(),
    });

    render(
      <MemoryRouter
        initialEntries={[
          "/solutions/88?ticket_id=501&lead_id=2026&opportunity_id=2&project_id=42",
        ]}
      >
        <SolutionDetail />
      </MemoryRouter>,
    );

    fireEvent.click(screen.getAllByRole("button")[0]);

    expect(navigateMock).toHaveBeenCalledWith(
      "/presales/technical-solutions?tab=solutions&type=support&ticket_id=501&lead_id=2026&opportunity_id=2&project_id=42",
    );
  });

  it("opens PMO initiation handoff from an approved technical solution", () => {
    useSolutionDetail.mockReturnValue({
      activeTab: "overview",
      setActiveTab: vi.fn(),
      solution: {
        id: 88,
        code: "SOL-20260607-001",
        name: "华南电子FCT方案",
        customer: "华南电子",
        opportunity: "华南电子二期",
        status: "approved",
        version: "V1.0",
        ticketId: 501,
        leadId: 2026,
        opportunityId: 2,
        projectId: 42,
        suggestedPrice: 280000,
        requirementSummary: "三工位FCT测试线",
        estimatedHours: 120,
      },
      loading: false,
      error: null,
      costEstimate: null,
      submittingReview: false,
      reviewError: null,
      submitForReview: vi.fn(),
    });

    render(
      <MemoryRouter>
        <SolutionDetail />
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByRole("button", { name: "发起立项" }));

    const target = new URL(navigateMock.mock.calls.at(-1)[0], "http://localhost");
    expect(target.pathname).toBe("/pmo/initiations");
    expect(target.searchParams.get("handoff")).toBe("presale");
    expect(target.searchParams.get("solution_id")).toBe("88");
    expect(target.searchParams.get("ticket_id")).toBe("501");
    expect(target.searchParams.get("lead_id")).toBe("2026");
    expect(target.searchParams.get("opportunity_id")).toBe("2");
    expect(target.searchParams.get("project_id")).toBe("42");
    expect(target.searchParams.get("project_name")).toBe("华南电子FCT方案");
    expect(target.searchParams.get("opportunity_name")).toBe("华南电子二期");
    expect(target.searchParams.get("customer_name")).toBe("华南电子");
    expect(target.searchParams.get("estimated_amount")).toBe("280000");
    expect(target.searchParams.get("requirement_summary")).toBe("三工位FCT测试线");
    expect(target.searchParams.get("estimated_hours")).toBe("120");
  });
});
