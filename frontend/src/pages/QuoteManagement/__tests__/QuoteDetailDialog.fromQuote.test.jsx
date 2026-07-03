/**
 * SALES-12 契约：报价详情必须有"转合同"入口。
 * 后端 /sales/contracts/from-quote 齐备而前端零入口，金额/版本 ID 靠手填——北极星断链。
 * 只有 APPROVED/ACCEPTED 报价可转；成功后展示合同编码。
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

import QuoteDetailDialog from "../QuoteDetailDialog";
import { contractApi } from "../../../services/api";

vi.mock("../../../services/api", () => ({
  contractApi: { fromQuote: vi.fn() },
}));

const baseQuote = {
  id: 66,
  quote_code: "QUOTE-X1",
  status: "APPROVED",
};

describe("QuoteDetailDialog 转合同入口", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("APPROVED 报价显示转合同按钮，点击调 from-quote 并展示合同编码", async () => {
    contractApi.fromQuote.mockResolvedValue({
      data: { id: 9, contract_code: "CT-2026-001" },
    });
    render(
      <QuoteDetailDialog
        open
        onOpenChange={() => {}}
        selectedQuote={baseQuote}
        onApprove={() => {}}
        onReject={() => {}}
        onSend={() => {}}
        onEdit={() => {}}
      />
    );

    const button = screen.getByRole("button", { name: /转合同/ });
    fireEvent.click(button);

    await waitFor(() => {
      expect(contractApi.fromQuote).toHaveBeenCalledWith({ quote_id: 66 });
    });
    expect(await screen.findByText(/CT-2026-001/)).toBeInTheDocument();
  });

  it("DRAFT 报价不显示转合同按钮", () => {
    render(
      <QuoteDetailDialog
        open
        onOpenChange={() => {}}
        selectedQuote={{ ...baseQuote, status: "DRAFT" }}
        onApprove={() => {}}
        onReject={() => {}}
        onSend={() => {}}
        onEdit={() => {}}
      />
    );

    expect(screen.queryByRole("button", { name: /转合同/ })).not.toBeInTheDocument();
  });

  it("G3 拦截（400）时把缺口信息展示给用户", async () => {
    contractApi.fromQuote.mockRejectedValue({
      response: { status: 400, data: { detail: "G3阶段门验证失败: 成本拆解缺失" } },
    });
    const alertSpy = vi.spyOn(window, "alert").mockImplementation(() => {});
    render(
      <QuoteDetailDialog
        open
        onOpenChange={() => {}}
        selectedQuote={baseQuote}
        onApprove={() => {}}
        onReject={() => {}}
        onSend={() => {}}
        onEdit={() => {}}
      />
    );

    fireEvent.click(screen.getByRole("button", { name: /转合同/ }));

    await waitFor(() => {
      expect(alertSpy).toHaveBeenCalledWith(expect.stringContaining("G3"));
    });
    alertSpy.mockRestore();
  });
});
