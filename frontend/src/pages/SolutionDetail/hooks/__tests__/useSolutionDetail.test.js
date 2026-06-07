import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useParams } from "react-router-dom";
import { presaleApi } from "../../../../services/api";
import { useSolutionDetail } from "../useSolutionDetail";

vi.mock("react-router-dom", () => ({
  useParams: vi.fn(),
}));

vi.mock("../../../../services/api", () => ({
  presaleApi: {
    solutions: {
      get: vi.fn(),
      getCost: vi.fn(),
      getVersions: vi.fn(),
      review: vi.fn(),
    },
  },
}));

describe("useSolutionDetail", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useParams.mockReturnValue({ id: "88" });
    presaleApi.solutions.getVersions.mockResolvedValue({ data: { code: 200, data: [] } });
  });

  it("unwraps backend solution detail and cost estimate responses", async () => {
    presaleApi.solutions.get.mockResolvedValue({
      data: {
        code: 200,
        data: {
          id: 88,
          solution_no: "SOL-20260607-001",
          name: "华南电子FCT方案",
          solution_type: "FCT",
          industry: "电子制造",
          test_type: "FCT",
          requirement_summary: "三工位FCT测试线",
          solution_overview: "采用模块化测试平台",
          technical_spec: "PXI + ICT fixture",
          estimated_cost: 120000,
          suggested_price: 180000,
          status: "APPROVED",
          version: "V1.0",
          author_name: "陈敏",
          ticket_id: 501,
          lead_id: 2026,
          project_id: 42,
          opportunity_id: 66,
          opportunity_name: "华南电子二期",
          sales_person_name: "宋魁",
          created_at: "2026-06-07T10:00:00",
          updated_at: "2026-06-07T11:00:00",
        },
      },
    });
    presaleApi.solutions.getCost.mockResolvedValue({
      data: {
        code: 200,
        data: {
          solution_id: 88,
          total_cost: 120000,
          suggested_price: 180000,
          breakdown: [
            {
              id: 1,
              category: "硬件",
              item_name: "PXI机箱",
              unit: "套",
              quantity: 1,
              unit_price: 80000,
              amount: 80000,
            },
          ],
        },
      },
    });

    const { result } = renderHook(() => useSolutionDetail());

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(presaleApi.solutions.get).toHaveBeenCalledWith("88");
    expect(presaleApi.solutions.getCost).toHaveBeenCalledWith("88");
    expect(result.current.solution).toMatchObject({
      id: 88,
      code: "SOL-20260607-001",
      name: "华南电子FCT方案",
      status: "approved",
      amount: 18,
      ticketId: 501,
      leadId: 2026,
      projectId: 42,
      opportunityId: 66,
      opportunity: "华南电子二期",
      salesPerson: "宋魁",
      creator: "陈敏",
      description: "采用模块化测试平台",
      requirementSummary: "三工位FCT测试线",
      solutionOverview: "采用模块化测试平台",
      technicalSpec: "PXI + ICT fixture",
      techSpecs: {
        productInfo: {},
        capacity: { uph: 0, cycleTime: 0, dailyOutput: 0, channels: 0 },
        testItems: [],
        testStandards: [],
        environment: {},
        rawText: "PXI + ICT fixture",
      },
    });
    expect(result.current.costEstimate).toMatchObject({
      solution_id: 88,
      total_cost: 120000,
      suggested_price: 180000,
      breakdown: [{ item_name: "PXI机箱", amount: 80000 }],
    });
  });

  it("loads backend solution versions into the history tab contract", async () => {
    presaleApi.solutions.get.mockResolvedValue({
      data: {
        code: 200,
        data: {
          id: 88,
          solution_no: "SOL-20260607-001",
          name: "华南电子FCT方案",
          status: "APPROVED",
          version: "V1.0",
          author_name: "陈敏",
          solution_overview: "采用模块化测试平台",
          created_at: "2026-06-07T10:00:00",
        },
      },
    });
    presaleApi.solutions.getCost.mockResolvedValue({ data: { code: 200, data: null } });
    presaleApi.solutions.getVersions.mockResolvedValue({
      data: {
        code: 200,
        data: [
          {
            id: 77,
            version: "V0.9",
            author_name: "李工",
            review_comment: "初版评审意见",
            created_at: "2026-06-01T09:00:00",
            updated_at: "2026-06-01T09:30:00",
            status: "APPROVED",
          },
          {
            id: 88,
            version: "V1.0",
            author_name: "陈敏",
            solution_overview: "采用模块化测试平台",
            created_at: "2026-06-07T10:00:00",
            updated_at: "2026-06-07T11:00:00",
            status: "APPROVED",
          },
        ],
      },
    });

    const { result } = renderHook(() => useSolutionDetail());

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(presaleApi.solutions.getVersions).toHaveBeenCalledWith("88");
    expect(result.current.solution.versionHistory).toEqual([
      {
        id: 77,
        version: "V0.9",
        date: "2026-06-01T09:30:00",
        author: "李工",
        changes: "初版评审意见",
        status: "approved",
        current: false,
      },
      {
        id: 88,
        version: "V1.0",
        date: "2026-06-07T11:00:00",
        author: "陈敏",
        changes: "采用模块化测试平台",
        status: "approved",
        current: true,
      },
    ]);
  });

  it("submits a draft solution for review and refreshes detail state", async () => {
    presaleApi.solutions.get
      .mockResolvedValueOnce({
        data: {
          code: 200,
          data: {
            id: 88,
            solution_no: "SOL-20260607-001",
            name: "华南电子FCT方案",
            status: "DRAFT",
            version: "V1.0",
            author_name: "陈敏",
            solution_overview: "采用模块化测试平台",
          },
        },
      })
      .mockResolvedValueOnce({
        data: {
          code: 200,
          data: {
            id: 88,
            solution_no: "SOL-20260607-001",
            name: "华南电子FCT方案",
            status: "REVIEW",
            review_status: "REVIEW",
            review_comment: "提交评审",
            version: "V1.0",
            author_name: "陈敏",
            solution_overview: "采用模块化测试平台",
          },
        },
      });
    presaleApi.solutions.getCost.mockResolvedValue({ data: { code: 200, data: null } });
    presaleApi.solutions.review.mockResolvedValue({
      data: {
        code: 200,
        data: {
          id: 88,
          status: "REVIEW",
          review_status: "REVIEW",
          review_comment: "提交评审",
        },
      },
    });

    const { result } = renderHook(() => useSolutionDetail());

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.solution.status).toBe("draft");

    await act(async () => {
      await result.current.submitForReview("提交评审");
    });

    expect(presaleApi.solutions.review).toHaveBeenCalledWith("88", {
      review_status: "REVIEW",
      review_comment: "提交评审",
    });
    await waitFor(() => expect(result.current.solution.status).toBe("review"));
    expect(result.current.submittingReview).toBe(false);
  });
});
