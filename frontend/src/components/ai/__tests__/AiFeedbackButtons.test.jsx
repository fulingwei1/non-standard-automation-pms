/**
 * AiFeedbackButtons：AI 产出反馈按钮（采纳/驳回）契约。
 * 反馈闭环前端入口：任何 AI 建议卡片挂上即接入 /ai-feedback。
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

import AiFeedbackButtons from "../AiFeedbackButtons";
import api from "../../../services/api";

vi.mock("../../../services/api", () => ({
  default: { post: vi.fn() },
}));

describe("AiFeedbackButtons", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("采纳：直接提交 ADOPTED 并显示已记录", async () => {
    api.post.mockResolvedValue({ data: { feedback_id: 1 } });
    render(
      <AiFeedbackButtons featureKey="opportunity_next_action" refType="opportunity" refId={9} />
    );

    fireEvent.click(screen.getByRole("button", { name: /采纳/ }));

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith("/ai-feedback", {
        feature_key: "opportunity_next_action",
        verdict: "ADOPTED",
        ref_type: "opportunity",
        ref_id: 9,
        reason: null,
      });
    });
    expect(await screen.findByText(/已记录/)).toBeInTheDocument();
  });

  it("驳回：要求填写原因后提交 REJECTED", async () => {
    api.post.mockResolvedValue({ data: { feedback_id: 2 } });
    const promptSpy = vi.spyOn(window, "prompt").mockReturnValue("建议不贴合行业");
    render(<AiFeedbackButtons featureKey="opportunity_next_action" refId={9} />);

    fireEvent.click(screen.getByRole("button", { name: /驳回/ }));

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith("/ai-feedback", {
        feature_key: "opportunity_next_action",
        verdict: "REJECTED",
        ref_type: null,
        ref_id: 9,
        reason: "建议不贴合行业",
      });
    });
    promptSpy.mockRestore();
  });

  it("驳回时取消原因输入则不提交", async () => {
    const promptSpy = vi.spyOn(window, "prompt").mockReturnValue(null);
    render(<AiFeedbackButtons featureKey="x" />);

    fireEvent.click(screen.getByRole("button", { name: /驳回/ }));

    expect(api.post).not.toHaveBeenCalled();
    promptSpy.mockRestore();
  });
});
