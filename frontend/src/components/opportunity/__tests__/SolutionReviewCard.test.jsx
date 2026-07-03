/**
 * SolutionReviewCard：AI 方案评审卡片 + 风险处置入口契约。
 * HIGH 风险未处置会被 G2 闸门拦截，卡片必须给出处置动作（人工关键判断留痕）。
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

import SolutionReviewCard from "../SolutionReviewCard";
import api from "../../../services/api";

vi.mock("../../../services/api", () => ({
  default: { post: vi.fn() },
}));

const REVIEWS = [
  { aspect: "节拍可达性", risk_level: "HIGH", finding: "15秒节拍超时", suggestion: "并行工位" },
  { aspect: "接口兼容", risk_level: "MEDIUM", finding: "MES 版本未确认", suggestion: "向客户确认" },
];

describe("SolutionReviewCard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("有 HIGH 风险时显示 G2 拦截提示与处置按钮", () => {
    render(<SolutionReviewCard opportunityId={9} reviews={REVIEWS} />);

    expect(screen.getByText(/高风险未处置将被 G2 闸门拦截/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /已消除风险/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /带险推进/ })).toBeInTheDocument();
  });

  it("无 HIGH 风险时不显示处置区", () => {
    render(<SolutionReviewCard opportunityId={9} reviews={[REVIEWS[1]]} />);

    expect(screen.queryByText(/G2 闸门拦截/)).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /带险推进/ })).not.toBeInTheDocument();
  });

  it("带险推进：填理由后调处置端点并显示已处置", async () => {
    api.post.mockResolvedValue({ data: { data: { resolution: { action: "ACCEPT_RISK" } } } });
    const promptSpy = vi.spyOn(window, "prompt").mockReturnValue("客户接受并行工位方案");
    render(<SolutionReviewCard opportunityId={9} reviews={REVIEWS} />);

    fireEvent.click(screen.getByRole("button", { name: /带险推进/ }));

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith(
        "/sales/opportunities/9/solution-review/resolution",
        { action: "ACCEPT_RISK", note: "客户接受并行工位方案" }
      );
    });
    expect(await screen.findByText(/已处置/)).toBeInTheDocument();
    promptSpy.mockRestore();
  });

  it("取消理由输入则不提交", () => {
    const promptSpy = vi.spyOn(window, "prompt").mockReturnValue(null);
    render(<SolutionReviewCard opportunityId={9} reviews={REVIEWS} />);

    fireEvent.click(screen.getByRole("button", { name: /已消除风险/ }));

    expect(api.post).not.toHaveBeenCalled();
    promptSpy.mockRestore();
  });
});
