import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, useParams } from "react-router-dom";
import RequirementFreezeManagement from "../RequirementFreezeManagement";

const technicalAssessmentApiMock = vi.hoisted(() => ({
  getRequirementFreezes: vi.fn(),
  createRequirementFreeze: vi.fn(),
}));

vi.mock("../../services/api", () => ({
  technicalAssessmentApi: technicalAssessmentApiMock,
}));

const renderWithRouter = () =>
  render(
    <MemoryRouter>
      <RequirementFreezeManagement />
    </MemoryRouter>
  );

describe("RequirementFreezeManagement", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useParams.mockReturnValue({ sourceType: "leads", sourceId: "5" });
    technicalAssessmentApiMock.getRequirementFreezes.mockResolvedValue({
      formatted: {
        items: [
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
      },
    });
  });

  it("loads and renders requirement freeze records for the current source", async () => {
    renderWithRouter();

    await waitFor(() => {
      expect(technicalAssessmentApiMock.getRequirementFreezes).toHaveBeenCalledWith("leads", 5);
    });

    expect(await screen.findByText("方案冻结")).toBeInTheDocument();
    expect(screen.getByText("版本: v1.0")).toBeInTheDocument();
    expect(screen.getByText("需ECR/ECN")).toBeInTheDocument();
    expect(screen.getByText("方案已确认")).toBeInTheDocument();
    expect(screen.getByText("冻结人: 张三")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "线索管理" })).toHaveAttribute(
      "href",
      "/sales/leads",
    );
  });
});
