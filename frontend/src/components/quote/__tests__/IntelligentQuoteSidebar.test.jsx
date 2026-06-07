import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import IntelligentQuoteSidebar from "../IntelligentQuoteSidebar";
import { intelligentQuoteApi } from "../../../services/api";

vi.mock("../../../services/api", () => ({
  intelligentQuoteApi: {
    getHistoricalPrices: vi.fn(),
  },
}));

describe("IntelligentQuoteSidebar", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("normalizes wrapped historical price response before rendering scenarios", async () => {
    intelligentQuoteApi.getHistoricalPrices.mockResolvedValue({
      data: {
        data: {
          average_price: 300000,
          matched_count: 1,
          historical_prices: [
            {
              project_name: "历史FCT项目",
              similarity: "高",
              final_price: 298000,
            },
          ],
        },
      },
    });

    render(
      <IntelligentQuoteSidebar
        opportunity={{ id: 2, opp_name: "FCT测试线商机" }}
        currentPrice={300000}
        currentCost={175000}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText("历史FCT项目")).toBeInTheDocument();
    });
    expect(screen.getByText("AI最优价格建议")).toBeInTheDocument();
  });
});
