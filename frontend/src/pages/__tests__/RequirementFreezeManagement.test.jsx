import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { useParams } from "react-router-dom";
import RequirementFreezeManagement from "../RequirementFreezeManagement";

const technicalAssessmentApiMock = vi.hoisted(() => ({
  getRequirementFreezes: vi.fn(),
  createRequirementFreeze: vi.fn(),
}));

vi.mock("../../services/api", () => ({
  technicalAssessmentApi: technicalAssessmentApiMock,
}));

describe("RequirementFreezeManagement", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useParams.mockReturnValue({ sourceType: "lead", sourceId: "5" });
    technicalAssessmentApiMock.getRequirementFreezes.mockResolvedValue({
      data: [
        {
          id: 9,
          freeze_type: "SOLUTION",
          version_number: "v1.0",
          requires_ecr: true,
          description: "方案已确认",
          freeze_time: "2026-06-01T08:30:00",
          frozen_by_name: "张三",
        },
      ],
    });
  });

  it("loads and renders requirement freeze records for the current source", async () => {
    render(<RequirementFreezeManagement />);

    await waitFor(() => {
      expect(technicalAssessmentApiMock.getRequirementFreezes).toHaveBeenCalledWith("lead", 5);
    });

    expect(await screen.findByText("方案冻结")).toBeInTheDocument();
    expect(screen.getByText("版本: v1.0")).toBeInTheDocument();
    expect(screen.getByText("需ECR/ECN")).toBeInTheDocument();
    expect(screen.getByText("方案已确认")).toBeInTheDocument();
    expect(screen.getByText("冻结人: 张三")).toBeInTheDocument();
  });
});
