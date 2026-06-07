import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import TechnicalReviewDetail from "../index";

const navigateSpy = vi.hoisted(() => vi.fn());

vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useParams: () => ({ reviewId: "new" }),
    useNavigate: () => navigateSpy,
    useLocation: () => ({
      pathname: "/technical-reviews/new",
      search: "?project_id=42&ticket_id=91&opportunity_id=2",
    }),
  };
});

vi.mock("../hooks", () => ({
  useTechnicalReviewForm: () => ({
    isNew: true,
    loading: false,
    saving: false,
    review: null,
    activeTab: "basic",
    setActiveTab: vi.fn(),
    formData: {
      review_type: "PDR",
      review_name: "",
      project_id: "42",
      scheduled_date: "",
      location: "",
      meeting_type: "ONSITE",
      host_id: "",
      presenter_id: "",
      recorder_id: "",
    },
    updateField: vi.fn(),
    projects: [{ id: 42, project_code: "PRJ-42", project_name: "合同转项目" }],
    users: [],
    participants: [],
    materials: [],
    checklistRecords: [],
    issues: [],
    setParticipantDialog: vi.fn(),
    setMaterialDialog: vi.fn(),
    setChecklistDialog: vi.fn(),
    setIssueDialog: vi.fn(),
    handleSave: vi.fn(),
    fetchReview: vi.fn(),
  }),
}));

describe("TechnicalReviewDetail", () => {
  beforeEach(() => {
    navigateSpy.mockClear();
  });

  it("keeps project and presale context when returning to the review list", () => {
    render(<TechnicalReviewDetail />);

    fireEvent.click(screen.getByRole("button", { name: /返回列表/ }));

    expect(navigateSpy).toHaveBeenCalledWith(
      "/technical-reviews?project_id=42&ticket_id=91&opportunity_id=2",
    );
  });
});
