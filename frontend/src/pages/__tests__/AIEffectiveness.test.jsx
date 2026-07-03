/**
 * AIEffectiveness：AI 效果看板契约。
 * 持续优化环节的人工消费入口：采纳率统计 + 报价对账。
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";

import AIEffectiveness from "../AIEffectiveness";
import api from "../../services/api";

vi.mock("../../services/api", () => ({
  default: { get: vi.fn() },
}));

const STATS = {
  items: [
    {
      feature_key: "opportunity_next_action",
      total: 10,
      adopted: 7,
      rejected: 2,
      partial: 1,
      adoption_rate: 0.7,
    },
  ],
};

const CALIBRATION = {
  items: [
    {
      presale_ticket_id: 3,
      opportunity_id: 9,
      contract_id: 5,
      contract_amount: 1000000,
      tiers: { basic: 850000, standard: 1050000, premium: 1400000 },
      deviations: { basic: -0.15, standard: 0.05, premium: 0.4 },
      closest_tier: "standard",
    },
  ],
  summary: {
    matched: 1,
    unmatched: 2,
    mean_abs_deviation: { basic: 0.15, standard: 0.05, premium: 0.4 },
    closest_tier_distribution: { standard: 1 },
  },
};

describe("AIEffectiveness", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.get.mockImplementation((url) => {
      if (url === "/ai-feedback/stats") return Promise.resolve({ data: STATS });
      if (url === "/ai-feedback/quote-calibration")
        return Promise.resolve({ data: CALIBRATION });
      return Promise.reject(new Error(`unexpected ${url}`));
    });
  });

  it("渲染采纳率统计表", async () => {
    render(<AIEffectiveness />);

    expect(await screen.findByText("opportunity_next_action")).toBeInTheDocument();
    expect(screen.getByText("70.0%")).toBeInTheDocument();
  });

  it("渲染报价对账汇总与明细", async () => {
    render(<AIEffectiveness />);

    expect(await screen.findByText(/已成交对账 1 单/)).toBeInTheDocument();
    expect(screen.getByText(/未成交 2 单/)).toBeInTheDocument();
    // standard 档平均偏差 5.0%
    expect(screen.getAllByText(/5\.0%/).length).toBeGreaterThan(0);
    // 明细行：最贴近档
    expect(screen.getAllByText(/standard/).length).toBeGreaterThan(0);
  });

  it("接口都空时显示空态", async () => {
    api.get.mockResolvedValue({ data: { items: [], summary: { matched: 0, unmatched: 0, mean_abs_deviation: {} } } });
    render(<AIEffectiveness />);

    expect(await screen.findByText(/暂无反馈数据/)).toBeInTheDocument();
  });
});
