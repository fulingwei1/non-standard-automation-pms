import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import LeadDetail from "../LeadDetail";
import { leadApi, customerApi } from "../../services/api";

const navigateMock = vi.hoisted(() => vi.fn());

vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useNavigate: () => navigateMock,
    useParams: () => ({ id: "21" }),
  };
});

vi.mock("../../services/api", () => ({
  leadApi: {
    get: vi.fn(),
    getFollowUps: vi.fn(),
    createFollowUp: vi.fn(),
    convert: vi.fn(),
  },
  customerApi: {
    list: vi.fn(),
  },
}));

vi.mock("@/lib/confirmAction", () => ({
  confirmAction: vi.fn(),
}));

describe("LeadDetail presales entry actions", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    navigateMock.mockClear();
    leadApi.get.mockResolvedValue({
      data: {
        id: 21,
        lead_code: "XS-021",
        customer_name: "华东线索A",
        status: "QUALIFIED",
        contact_name: "王总",
        contact_phone: "13800000000",
        demand_summary: "FCT测试线需求",
        created_at: "2026-06-07T10:00:00",
      },
    });
    leadApi.getFollowUps.mockResolvedValue({ data: [] });
    customerApi.list.mockResolvedValue({ data: { items: [] } });
  });

  it("offers lead requirement, technical assessment, and presales center deep links", async () => {
    render(<LeadDetail />);

    expect(await screen.findByText("线索详情 - XS-021")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "需求包" }));
    expect(navigateMock).toHaveBeenCalledWith("/sales/leads/21/requirement");

    fireEvent.click(screen.getByRole("button", { name: "技术评估" }));
    expect(navigateMock).toHaveBeenCalledWith("/sales/assessments/lead/21");

    fireEvent.click(screen.getByRole("button", { name: "售前中心" }));
    expect(navigateMock).toHaveBeenCalledWith(
      "/presales/technical-solutions?tab=reviews&type=support&status=pending&lead_id=21",
    );

    await waitFor(() => {
      expect(leadApi.getFollowUps).toHaveBeenCalledWith("21");
      expect(customerApi.list).toHaveBeenCalledWith({ page_size: 1000 });
    });
  });
});
