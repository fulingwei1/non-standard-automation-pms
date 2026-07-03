/**
 * PresaleAIWorkbench：售前 AI 工作台契约。
 * 北极星链路前端闭环：分析 → 确认回填 → 方案/三档报价（requirement_analysis_id 贯通，需求只录一次）。
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

import PresaleAIWorkbench from "../PresaleAIWorkbench";
import { presaleAIService } from "../../services/presaleAIService";

vi.mock("../../services/presaleAIService", () => ({
  presaleAIService: {
    analyzeRequirement: vi.fn(),
    confirmAnalysis: vi.fn(),
    submitGenerateSolution: vi.fn(),
    submitThreeTierQuotation: vi.fn(),
    getJob: vi.fn(),
  },
}));

const ANALYSIS = {
  id: 31,
  presale_ticket_id: 501,
  confidence_score: 0.85,
  structured_requirement: {
    project_type: "FCT功能测试系统",
    core_objectives: ["整机功能测试自动化"],
  },
  clarification_questions: [],
};

function fillAndAnalyze() {
  fireEvent.change(screen.getByLabelText(/售前工单/), { target: { value: "501" } });
  fireEvent.change(screen.getByLabelText(/原始需求/), {
    target: { value: "整机FCT功能测试系统，15秒节拍，MES对接与扫码追溯" },
  });
  fireEvent.click(screen.getByRole("button", { name: /AI 需求分析/ }));
}

describe("PresaleAIWorkbench", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    presaleAIService.analyzeRequirement.mockResolvedValue(ANALYSIS);
    presaleAIService.confirmAnalysis.mockResolvedValue({
      analysis_id: 31,
      backfilled: true,
      filled_fields: ["acceptance_criteria"],
      opportunity_id: 9,
    });
    presaleAIService.submitGenerateSolution.mockResolvedValue({ job_id: 7, status: "PENDING" });
    presaleAIService.submitThreeTierQuotation.mockResolvedValue({ job_id: 8, status: "PENDING" });
    presaleAIService.getJob.mockResolvedValue({
      job_id: 8,
      status: "SUCCESS",
      result: {
        basic: { total: 850000, quotation_number: "Q-B" },
        standard: { total: 1050000, quotation_number: "Q-S" },
        premium: { total: 1400000, quotation_number: "Q-P" },
      },
    });
  });

  it("分析后展示结构化结果与置信度，并出现下游动作按钮", async () => {
    render(<PresaleAIWorkbench />);
    fillAndAnalyze();

    expect(await screen.findByText(/FCT功能测试系统/)).toBeInTheDocument();
    expect(screen.getByText(/85/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /确认并回填商机/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /生成方案/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /三档报价/ })).toBeInTheDocument();
    expect(presaleAIService.analyzeRequirement).toHaveBeenCalledWith({
      presale_ticket_id: 501,
      raw_requirement: "整机FCT功能测试系统，15秒节拍，MES对接与扫码追溯",
    });
  });

  it("确认回填后显示回填字段", async () => {
    render(<PresaleAIWorkbench />);
    fillAndAnalyze();
    fireEvent.click(await screen.findByRole("button", { name: /确认并回填商机/ }));

    expect(await screen.findByText(/已回填商机/)).toBeInTheDocument();
    expect(presaleAIService.confirmAnalysis).toHaveBeenCalledWith(31);
  });

  it("三档报价携带 requirement_analysis_id 提交并轮询到结果", async () => {
    render(<PresaleAIWorkbench />);
    fillAndAnalyze();
    fireEvent.click(await screen.findByRole("button", { name: /三档报价/ }));

    await waitFor(() => {
      expect(presaleAIService.submitThreeTierQuotation).toHaveBeenCalledWith({
        presale_ticket_id: 501,
        requirement_analysis_id: 31,
      });
    });
    expect(await screen.findByText(/¥850,000/)).toBeInTheDocument();
    expect(screen.getByText(/¥1,400,000/)).toBeInTheDocument();
  });

  it("生成方案携带 requirement_analysis_id（不重贴需求）", async () => {
    presaleAIService.getJob.mockResolvedValue({
      job_id: 7,
      status: "SUCCESS",
      result: { solution_id: 88, confidence_score: 0.8, solution: { description: "方案摘要" } },
    });
    render(<PresaleAIWorkbench />);
    fillAndAnalyze();
    fireEvent.click(await screen.findByRole("button", { name: /生成方案/ }));

    await waitFor(() => {
      expect(presaleAIService.submitGenerateSolution).toHaveBeenCalledWith({
        presale_ticket_id: 501,
        requirement_analysis_id: 31,
        generate_architecture: false,
        generate_bom: false,
      });
    });
    expect(await screen.findByText(/方案摘要/)).toBeInTheDocument();
  });
});
