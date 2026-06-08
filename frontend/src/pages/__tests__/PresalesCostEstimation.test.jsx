import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import PresalesCostEstimation from "../PresalesCostEstimation";
import { presaleApi, presaleWorkbenchApi } from "../../services/api";
import { toast } from "../../components/ui/toast";

const routeState = vi.hoisted(() => ({
  search: "tab=cost&type=support&opportunity_id=2&ticket_id=501&project_id=42",
}));
const navigateSpy = vi.hoisted(() => vi.fn());

vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useNavigate: () => navigateSpy,
    useSearchParams: () => [new URLSearchParams(routeState.search), vi.fn()],
  };
});

vi.mock("../../services/api", () => ({
  presaleApi: {
    solutions: {
      get: vi.fn(),
      list: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
    },
  },
  presaleWorkbenchApi: {
    loadContext: vi.fn(),
  },
}));

vi.mock("../../components/ui/toast", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

vi.mock("../../components/presales/CostEstimateForm", () => ({
  default: ({ bidding, onSave, onCancel }) => (
    <div>
      <div>当前方案：{bidding.name}</div>
      <button
        type="button"
        onClick={() =>
          onSave({
            status: "draft",
            costData: {
              estimated_cost: 120000,
              suggested_price: 168000,
              cost_breakdown: {
                mechanical: 55000,
                electrical: 32000,
                software: 18000,
                standard: 12000,
                labor: 26000,
                other: 7000,
                notes: "含夹具、PLC、电控和调试人工",
              },
            },
          })
        }
      >
        保存成本
      </button>
      <button type="button" onClick={onCancel}>
        取消成本
      </button>
    </div>
  ),
}));

function renderPage(
  initialEntry = "/presales/technical-solutions?tab=cost&type=support&opportunity_id=2&ticket_id=501&project_id=42",
) {
  const url = new URL(initialEntry, "http://localhost");
  routeState.search = url.search.replace(/^\?/, "");

  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <PresalesCostEstimation embedded />
    </MemoryRouter>,
  );
}

describe("PresalesCostEstimation", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    presaleApi.solutions.list.mockResolvedValue({
      data: {
        items: [
          {
            id: 88,
            name: "ERP 改造售前技术方案",
            suggested_price: 1680000,
          },
        ],
        total: 1,
      },
    });
    presaleApi.solutions.get.mockResolvedValue({
      data: {
        id: 88,
        name: "ERP 改造售前技术方案",
        suggested_price: 1680000,
      },
    });
    presaleApi.solutions.create.mockResolvedValue({
      data: {
        id: 89,
        name: "线索成本估算方案",
      },
    });
    presaleApi.solutions.update.mockResolvedValue({ data: { id: 88 } });
    presaleWorkbenchApi.loadContext.mockResolvedValue({
      source: { type: "opportunity", id: 2 },
      solutions: { items: [], total: 0 },
      costing: { baseline: null },
    });
  });

  it("prefers presale workbench costing baseline before falling back to solution list", async () => {
    presaleWorkbenchApi.loadContext.mockResolvedValueOnce({
      source: { type: "opportunity", id: 2 },
      solutions: {
        items: [
          {
            id: 88,
            name: "ERP 改造售前技术方案",
            estimated_cost: 1200000,
            suggested_price: 1680000,
          },
        ],
        total: 1,
      },
      costing: {
        baseline: {
          source: "solution",
          solution_id: 88,
          solution_no: "SOL-001",
          solution_name: "ERP 改造售前技术方案",
          estimated_cost: 1200000,
          suggested_price: 1680000,
        },
      },
    });

    renderPage();

    await waitFor(() => {
      expect(presaleWorkbenchApi.loadContext).toHaveBeenCalledWith({
        sourceType: "opportunity",
        sourceId: 2,
        presaleTicketId: 501,
      });
    });
    expect(presaleApi.solutions.list).not.toHaveBeenCalled();
    expect(await screen.findByText("当前方案：ERP 改造售前技术方案")).toBeInTheDocument();
    expect(screen.getByText("当前预算参考：¥168万")).toBeInTheDocument();
  });

  it("loads linked solution context from sales support and project ids", async () => {
    renderPage();

    await waitFor(() => {
      expect(presaleApi.solutions.list).toHaveBeenCalledWith({
        page: 1,
        page_size: 1,
        opportunity_id: "2",
        ticket_id: "501",
        project_id: "42",
      });
    });
    expect(await screen.findByText("当前方案：ERP 改造售前技术方案")).toBeInTheDocument();
  });

  it("keeps lead context when loading linked solution for cost estimation", async () => {
    renderPage(
      "/presales/technical-solutions?tab=cost&type=support&lead_id=2026&opportunity_id=2&ticket_id=501&project_id=42",
    );

    await waitFor(() => {
      expect(presaleApi.solutions.list).toHaveBeenCalledWith({
        page: 1,
        page_size: 1,
        lead_id: "2026",
        opportunity_id: "2",
        ticket_id: "501",
        project_id: "42",
      });
    });
    expect(await screen.findByText("当前方案：ERP 改造售前技术方案")).toBeInTheDocument();
  });

  it("saves cost estimate back to the linked solution", async () => {
    renderPage();

    expect(await screen.findByText("当前方案：ERP 改造售前技术方案")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "保存成本" }));

    await waitFor(() => {
      expect(presaleApi.solutions.update).toHaveBeenCalledWith(88, {
        estimated_cost: 120000,
        suggested_price: 168000,
        cost_breakdown: {
          mechanical: 55000,
          electrical: 32000,
          software: 18000,
          standard: 12000,
          labor: 26000,
          other: 7000,
          notes: "含夹具、PLC、电控和调试人工",
        },
      });
    });
    expect(toast.success).toHaveBeenCalledWith("成本估算草稿已保存");
  });

  it("creates a linked solution when saving cost estimation without an existing solution", async () => {
    presaleApi.solutions.list.mockResolvedValueOnce({
      data: {
        items: [],
        total: 0,
      },
    });

    renderPage(
      "/presales/technical-solutions?tab=cost&type=support&lead_id=2026&opportunity_id=2&ticket_id=501&project_id=42&name=%E7%BA%BF%E7%B4%A2%E6%88%90%E6%9C%AC%E4%BC%B0%E7%AE%97%E6%96%B9%E6%A1%88",
    );

    expect(await screen.findByText("当前方案：线索成本估算方案")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "保存成本" }));

    await waitFor(() => {
      expect(presaleApi.solutions.create).toHaveBeenCalledWith({
        name: "线索成本估算方案",
        solution_type: "CUSTOM",
        lead_id: 2026,
        opportunity_id: 2,
        ticket_id: 501,
        project_id: 42,
        estimated_cost: 120000,
        suggested_price: 168000,
        cost_breakdown: {
          mechanical: 55000,
          electrical: 32000,
          software: 18000,
          standard: 12000,
          labor: 26000,
          other: 7000,
          notes: "含夹具、PLC、电控和调试人工",
        },
      });
    });
    expect(presaleApi.solutions.update).not.toHaveBeenCalled();
    expect(toast.success).toHaveBeenCalledWith("成本估算草稿已保存");
  });

  it("creates a cost solution from tender support context and keeps tender trace", async () => {
    presaleApi.solutions.list.mockResolvedValueOnce({
      data: {
        items: [],
        total: 0,
      },
    });

    renderPage(
      "/presales/technical-solutions?tab=cost&type=support&tender_id=301&lead_id=2026&opportunity_id=2&ticket_id=501&project_id=42&amount=500&name=%E6%99%BA%E8%83%BD%E5%88%B6%E9%80%A0%E7%B3%BB%E7%BB%9F",
    );

    expect(await screen.findByText("当前方案：智能制造系统")).toBeInTheDocument();
    expect(screen.getByText("当前预算参考：¥500万")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "保存成本" }));

    await waitFor(() => {
      expect(presaleApi.solutions.create).toHaveBeenCalledWith({
        name: "智能制造系统",
        solution_type: "CUSTOM",
        lead_id: 2026,
        opportunity_id: 2,
        ticket_id: 501,
        project_id: 42,
        estimated_cost: 120000,
        suggested_price: 168000,
        cost_breakdown: {
          mechanical: 55000,
          electrical: 32000,
          software: 18000,
          standard: 12000,
          labor: 26000,
          other: 7000,
          notes: "含夹具、PLC、电控和调试人工",
          presale_context: {
            tender_id: 301,
            ticket_id: 501,
            lead_id: 2026,
            opportunity_id: 2,
            project_id: 42,
          },
        },
      });
    });
    expect(toast.success).toHaveBeenCalledWith("成本估算草稿已保存");
  });

  it("loads linked solution by project context when opened from project presales entry", async () => {
    renderPage("/presales/technical-solutions?tab=cost&project_id=42");

    await waitFor(() => {
      expect(presaleApi.solutions.list).toHaveBeenCalledWith({
        page: 1,
        page_size: 1,
        project_id: "42",
      });
    });
    expect(await screen.findByText("当前方案：ERP 改造售前技术方案")).toBeInTheDocument();
  });

  it("loads the exact solution when opened with solution_id", async () => {
    renderPage(
      "/presales/technical-solutions?tab=cost&solution_id=88&ticket_id=501&opportunity_id=2&project_id=42",
    );

    await waitFor(() => {
      expect(presaleApi.solutions.get).toHaveBeenCalledWith(88);
    });
    expect(presaleApi.solutions.list).not.toHaveBeenCalled();
    expect(await screen.findByText("当前方案：ERP 改造售前技术方案")).toBeInTheDocument();
    expect(screen.getByText("当前预算参考：¥168万")).toBeInTheDocument();
  });

  it("keeps solution and project context when cancelling embedded estimation", async () => {
    renderPage(
      "/presales/technical-solutions?tab=cost&solution_id=88&ticket_id=501&opportunity_id=2&project_id=42",
    );

    expect(await screen.findByText("当前方案：ERP 改造售前技术方案")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "取消成本" }));

    expect(navigateSpy).toHaveBeenCalledWith(
      "/presales/technical-solutions?tab=cost&solution_id=88&ticket_id=501&opportunity_id=2&project_id=42",
    );
  });
});
