import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { useParams } from "react-router-dom";
import AIClarificationChat from "../AIClarificationChat";

const technicalAssessmentApiMock = vi.hoisted(() => ({
  getAIClarifications: vi.fn(),
  getAIClarificationsForSource: vi.fn(),
  createAIClarificationForLead: vi.fn(),
  createAIClarificationForOpportunity: vi.fn(),
  createAIClarification: vi.fn(),
  updateAIClarification: vi.fn(),
}));

vi.mock("../../services/api", () => ({
  technicalAssessmentApi: technicalAssessmentApiMock,
}));

describe("AIClarificationChat", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useParams.mockReturnValue({ sourceType: "opportunities", sourceId: "9" });
    technicalAssessmentApiMock.getAIClarifications.mockResolvedValue({ data: { items: [] } });
    technicalAssessmentApiMock.getAIClarificationsForSource.mockResolvedValue({
      data: {
        items: [
          {
            id: 21,
            round: 1,
            questions: '["接口协议是否已确定？"]',
            answers: null,
          },
        ],
      },
    });
  });

  it("loads clarifications through the normalized source API", async () => {
    render(<AIClarificationChat />);

    await waitFor(() => {
      expect(technicalAssessmentApiMock.getAIClarificationsForSource).toHaveBeenCalledWith(
        "opportunities",
        9,
      );
    });

    expect(await screen.findByText(/接口协议是否已确定/)).toBeInTheDocument();
  });

  it("keeps the new-question textarea empty until the user types", async () => {
    render(<AIClarificationChat />);

    const textarea = await screen.findByPlaceholderText(/请输入问题/);

    expect(textarea).toHaveValue("");
    expect(screen.getByRole("button", { name: /创建澄清/ })).toBeDisabled();
  });

  it("does not crash when a stored clarification has invalid JSON", async () => {
    technicalAssessmentApiMock.getAIClarifications.mockResolvedValueOnce({
      data: {
        items: [
          {
            id: 22,
            round: 2,
            questions: "not-json",
            answers: "{bad-json",
          },
        ],
      },
    });
    technicalAssessmentApiMock.getAIClarificationsForSource.mockResolvedValueOnce({
      data: {
        items: [
          {
            id: 22,
            round: 2,
            questions: "not-json",
            answers: "{bad-json",
          },
        ],
      },
    });

    render(<AIClarificationChat />);

    expect(await screen.findByText(/第 2 轮澄清/)).toBeInTheDocument();
    expect(screen.getByText("待回复")).toBeInTheDocument();
  });
});
