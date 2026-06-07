import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import TechnicalReviewDetail from "../index";

const navigateSpy = vi.hoisted(() => vi.fn());
const routeState = vi.hoisted(() => ({
  params: { reviewId: "new" },
  location: {
    pathname: "/technical-reviews/new",
    search: "?project_id=42&ticket_id=91&opportunity_id=2",
  },
}));
const hookState = vi.hoisted(() => ({
  current: null,
}));

vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useParams: () => routeState.params,
    useNavigate: () => navigateSpy,
    useLocation: () => routeState.location,
  };
});

vi.mock("../hooks", () => ({
  useTechnicalReviewForm: () => hookState.current,
}));

function buildHookState(overrides = {}) {
  return {
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
    participantDialog: { open: false },
    setParticipantDialog: vi.fn(),
    materialDialog: { open: false },
    setMaterialDialog: vi.fn(),
    checklistDialog: { open: false },
    setChecklistDialog: vi.fn(),
    issueDialog: { open: false },
    setIssueDialog: vi.fn(),
    handleSave: vi.fn(),
    handleAddParticipant: vi.fn(),
    handleAddMaterial: vi.fn(),
    handleCreateChecklistRecord: vi.fn(),
    handleCreateIssue: vi.fn(),
    fetchReview: vi.fn(),
    ...overrides,
  };
}

describe("TechnicalReviewDetail", () => {
  beforeEach(() => {
    navigateSpy.mockClear();
    routeState.params = { reviewId: "new" };
    routeState.location = {
      pathname: "/technical-reviews/new",
      search: "?project_id=42&ticket_id=91&opportunity_id=2",
    };
    hookState.current = buildHookState();
  });

  it("keeps project and presale context when returning to the review list", () => {
    render(<TechnicalReviewDetail />);

    fireEvent.click(screen.getByRole("button", { name: /返回列表/ }));

    expect(navigateSpy).toHaveBeenCalledWith(
      "/technical-reviews?project_id=42&ticket_id=91&opportunity_id=2",
    );
  });

  it("submits a review issue from the issue dialog", async () => {
    const handleCreateIssue = vi.fn().mockResolvedValue(undefined);
    routeState.params = { reviewId: "7" };
    routeState.location = {
      pathname: "/technical-reviews/7",
      search: "?project_id=42&ticket_id=91&opportunity_id=2",
    };
    hookState.current = buildHookState({
      isNew: false,
      activeTab: "issues",
      review: { id: 7, review_name: "合同转项目 PDR" },
      users: [{ id: 3, username: "engineer", real_name: "工程师" }],
      issueDialog: { open: true },
      handleCreateIssue,
    });

    render(<TechnicalReviewDetail />);

    fireEvent.change(screen.getByLabelText("问题等级"), { target: { value: "B" } });
    fireEvent.change(screen.getByLabelText("问题类别"), {
      target: { value: "设计风险" },
    });
    fireEvent.change(screen.getByLabelText("问题描述"), {
      target: { value: "夹具定位方案需要复核" },
    });
    fireEvent.change(screen.getByLabelText("改进建议"), {
      target: { value: "补充定位销校核" },
    });
    fireEvent.change(screen.getByLabelText("责任人"), { target: { value: "3" } });
    fireEvent.change(screen.getByLabelText("整改期限"), {
      target: { value: "2026-06-20" },
    });
    fireEvent.click(screen.getByRole("button", { name: "提交问题" }));

    await waitFor(() => {
      expect(handleCreateIssue).toHaveBeenCalledWith({
        review_id: 7,
        issue_level: "B",
        category: "设计风险",
        description: "夹具定位方案需要复核",
        suggestion: "补充定位销校核",
        assignee_id: 3,
        deadline: "2026-06-20",
      });
    });
  });

  it("submits a participant from the participant dialog", async () => {
    const handleAddParticipant = vi.fn().mockResolvedValue(undefined);
    routeState.params = { reviewId: "7" };
    routeState.location = {
      pathname: "/technical-reviews/7",
      search: "?project_id=42&ticket_id=91&opportunity_id=2",
    };
    hookState.current = buildHookState({
      isNew: false,
      activeTab: "participants",
      review: { id: 7, review_name: "合同转项目 PDR" },
      users: [{ id: 3, username: "engineer", real_name: "工程师" }],
      participantDialog: { open: true },
      handleAddParticipant,
    });

    render(<TechnicalReviewDetail />);

    fireEvent.change(screen.getByLabelText("参与人"), { target: { value: "3" } });
    fireEvent.change(screen.getByLabelText("评审角色"), {
      target: { value: "expert" },
    });
    fireEvent.click(screen.getByRole("button", { name: "添加参与人" }));

    await waitFor(() => {
      expect(handleAddParticipant).toHaveBeenCalledWith({
        review_id: 7,
        user_id: 3,
        role: "expert",
        is_required: true,
      });
    });
  });

  it("submits a review material from the material dialog", async () => {
    const handleAddMaterial = vi.fn().mockResolvedValue(undefined);
    routeState.params = { reviewId: "7" };
    routeState.location = {
      pathname: "/technical-reviews/7",
      search: "?project_id=42&ticket_id=91&opportunity_id=2",
    };
    hookState.current = buildHookState({
      isNew: false,
      activeTab: "materials",
      review: { id: 7, review_name: "合同转项目 PDR" },
      materialDialog: { open: true },
      handleAddMaterial,
    });

    render(<TechnicalReviewDetail />);

    fireEvent.change(screen.getByLabelText("材料类型"), {
      target: { value: "drawing" },
    });
    fireEvent.change(screen.getByLabelText("材料名称"), {
      target: { value: "总装图纸" },
    });
    fireEvent.change(screen.getByLabelText("文件路径"), {
      target: { value: "/reviews/7/assembly.pdf" },
    });
    fireEvent.change(screen.getByLabelText("文件大小"), {
      target: { value: "2048" },
    });
    fireEvent.change(screen.getByLabelText("版本号"), { target: { value: "A1" } });
    fireEvent.click(screen.getByRole("button", { name: "登记材料" }));

    await waitFor(() => {
      expect(handleAddMaterial).toHaveBeenCalledWith({
        review_id: 7,
        material_type: "drawing",
        material_name: "总装图纸",
        file_path: "/reviews/7/assembly.pdf",
        file_size: 2048,
        version: "A1",
        is_required: true,
      });
    });
  });

  it("submits a checklist record from the checklist dialog", async () => {
    const handleCreateChecklistRecord = vi.fn().mockResolvedValue(undefined);
    routeState.params = { reviewId: "7" };
    routeState.location = {
      pathname: "/technical-reviews/7",
      search: "?project_id=42&ticket_id=91&opportunity_id=2",
    };
    hookState.current = buildHookState({
      isNew: false,
      activeTab: "checklist",
      review: { id: 7, review_name: "合同转项目 PDR" },
      users: [{ id: 3, username: "engineer", real_name: "工程师" }],
      checklistDialog: { open: true },
      handleCreateChecklistRecord,
    });

    render(<TechnicalReviewDetail />);

    fireEvent.change(screen.getByLabelText("检查类别"), {
      target: { value: "机械设计" },
    });
    fireEvent.change(screen.getByLabelText("检查项内容"), {
      target: { value: "定位基准是否明确" },
    });
    fireEvent.change(screen.getByLabelText("检查结果"), { target: { value: "FAIL" } });
    fireEvent.change(screen.getByLabelText("问题等级"), { target: { value: "B" } });
    fireEvent.change(screen.getByLabelText("问题描述"), {
      target: { value: "定位销校核缺少计算依据" },
    });
    fireEvent.change(screen.getByLabelText("检查人"), { target: { value: "3" } });
    fireEvent.change(screen.getByLabelText("备注"), {
      target: { value: "评审会上提出" },
    });
    fireEvent.click(screen.getByRole("button", { name: "添加检查项" }));

    await waitFor(() => {
      expect(handleCreateChecklistRecord).toHaveBeenCalledWith({
        review_id: 7,
        checklist_item_id: null,
        category: "机械设计",
        check_item: "定位基准是否明确",
        result: "FAIL",
        issue_level: "B",
        issue_desc: "定位销校核缺少计算依据",
        checker_id: 3,
        remark: "评审会上提出",
      });
    });
  });
});
