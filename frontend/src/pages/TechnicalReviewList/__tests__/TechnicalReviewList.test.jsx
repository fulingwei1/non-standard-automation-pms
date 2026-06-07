import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import TechnicalReviewList from "../index";

const navigateSpy = vi.hoisted(() => vi.fn());

vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useNavigate: () => navigateSpy,
    useLocation: () => ({
      pathname: "/technical-reviews",
      search: "?project_id=42&ticket_id=91&opportunity_id=2",
    }),
  };
});

vi.mock("../hooks", () => ({
  useTechnicalReviewList: () => ({
    loading: false,
    reviews: [
      {
        id: 7,
        review_no: "TR-PDR-007",
        review_name: "合同转项目 PDR",
        review_type: "PDR",
        status: "DRAFT",
        conclusion: null,
        project_no: "PRJ-42",
        scheduled_date: "2026-06-07T09:00:00",
        issue_count_a: 0,
        issue_count_b: 1,
        issue_count_c: 0,
        issue_count_d: 0,
      },
    ],
    total: 1,
    page: 1,
    setPage: vi.fn(),
    pageSize: 20,
    searchKeyword: "",
    setSearchKeyword: vi.fn(),
    projectId: "42",
    setProjectId: vi.fn(),
    status: null,
    setStatus: vi.fn(),
    reviewType: null,
    setReviewType: vi.fn(),
    projectList: [
      { id: 42, project_code: "PRJ-42", project_name: "合同转项目" },
    ],
    deleteDialog: { open: false, review: null },
    setDeleteDialog: vi.fn(),
    handleDelete: vi.fn(),
    handleSearch: vi.fn(),
    handleReset: vi.fn(),
  }),
}));

describe("TechnicalReviewList", () => {
  beforeEach(() => {
    navigateSpy.mockClear();
  });

  it("keeps project and presale context when entering technical review records", () => {
    render(<TechnicalReviewList />);

    fireEvent.click(screen.getByRole("button", { name: /创建技术评审/ }));
    expect(navigateSpy).toHaveBeenLastCalledWith(
      "/technical-reviews/new?project_id=42&ticket_id=91&opportunity_id=2",
    );

    fireEvent.click(screen.getByRole("button", { name: "查看 合同转项目 PDR" }));
    expect(navigateSpy).toHaveBeenLastCalledWith(
      "/technical-reviews/7?project_id=42&ticket_id=91&opportunity_id=2",
    );

    fireEvent.click(screen.getByRole("button", { name: "编辑 合同转项目 PDR" }));
    expect(navigateSpy).toHaveBeenLastCalledWith(
      "/technical-reviews/7/edit?project_id=42&ticket_id=91&opportunity_id=2",
    );
  });
});
