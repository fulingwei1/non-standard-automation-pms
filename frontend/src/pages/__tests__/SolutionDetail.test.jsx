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
          "/solutions/88?ticket_id=501&opportunity_id=2&project_id=42",
        ]}
      >
        <SolutionDetail />
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByRole("button", { name: "返回方案列表" }));

    expect(navigateMock).toHaveBeenCalledWith(
      "/presales/technical-solutions?tab=solutions&type=support&ticket_id=501&opportunity_id=2&project_id=42",
    );
  });
});
