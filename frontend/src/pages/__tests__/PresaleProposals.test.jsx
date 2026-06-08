import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import PresaleProposals from "../PresaleProposals";
import { presaleApi, presaleWorkbenchApi } from "../../services/api";

const routeState = vi.hoisted(() => ({
  search: "tab=solutions&type=support&opportunity_id=2&ticket_id=501",
}));
const navigateMock = vi.hoisted(() => vi.fn());

vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useNavigate: () => navigateMock,
    useSearchParams: () => [new URLSearchParams(routeState.search), vi.fn()],
  };
});

vi.mock("../../services/api", () => ({
  presaleApi: {
    solutions: {
      list: vi.fn(),
      create: vi.fn(),
      getVersions: vi.fn(),
      review: vi.fn(),
    },
  },
  presaleWorkbenchApi: {
    loadContext: vi.fn(),
  },
}));

vi.mock("framer-motion", () => ({
  motion: new Proxy(
    {},
    {
      get: (_, tag) => {
        const Tag = typeof tag === "string" ? tag : "div";
        return ({ children, ...props }) => {
          const motionProps = new Set([
            "initial",
            "animate",
            "exit",
            "variants",
            "transition",
            "whileHover",
            "whileTap",
            "layout",
          ]);
          const domProps = Object.fromEntries(
            Object.entries(props).filter(([key]) => !motionProps.has(key)),
          );
          return <Tag {...domProps}>{children}</Tag>;
        };
      },
    },
  ),
  AnimatePresence: ({ children }) => children,
}));

function renderPage(
  initialEntry = "/presales/technical-solutions?tab=solutions&type=support&opportunity_id=2&ticket_id=501",
) {
  const url = new URL(initialEntry, "http://localhost");
  routeState.search = url.search.replace(/^\?/, "");

  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <PresaleProposals embedded />
    </MemoryRouter>,
  );
}

describe("PresaleProposals", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    navigateMock.mockClear();
    presaleWorkbenchApi.loadContext.mockResolvedValue({
      source: { type: "opportunity", id: 2 },
      solutions: { items: [], total: 0 },
    });
    presaleApi.solutions.list.mockResolvedValue({ data: { items: [], total: 0 } });
    presaleApi.solutions.create.mockResolvedValue({
      data: {
        id: 900,
        name: "ERP 改造售前技术方案",
        status: "DRAFT",
      },
    });
    presaleApi.solutions.getVersions.mockResolvedValue({ data: { items: [], total: 0 } });
    presaleApi.solutions.review.mockResolvedValue({ data: { id: 900 } });
  });

  it("prefers presale workbench context solutions before falling back to solution list", async () => {
    presaleWorkbenchApi.loadContext.mockResolvedValueOnce({
      source: { type: "opportunity", id: 2 },
      solutions: {
        items: [
          {
            id: 88,
            solution_no: "SOL-88",
            name: "聚合上下文售前方案",
            status: "APPROVED",
            ticket_id: 501,
            opportunity_id: 2,
            estimated_cost: 180000,
            suggested_price: 280000,
          },
        ],
        total: 1,
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
    expect(await screen.findByText("聚合上下文售前方案")).toBeInTheDocument();
    expect(screen.getByText("SOL-88 · 未分类行业")).toBeInTheDocument();
  });

  it("shows cost baseline and quote status from presale workbench context", async () => {
    presaleWorkbenchApi.loadContext.mockResolvedValueOnce({
      source: { type: "opportunity", id: 2 },
      solutions: {
        items: [
          {
            id: 88,
            solution_no: "SOL-88",
            name: "聚合上下文售前方案",
            status: "APPROVED",
            ticket_id: 501,
            opportunity_id: 2,
            estimated_cost: 260000,
            suggested_price: 420000,
          },
        ],
        total: 1,
      },
      costing: {
        baseline: {
          solution_id: 88,
          solution_no: "SOL-88",
          solution_name: "聚合上下文售前方案",
          estimated_cost: 260000,
          suggested_price: 420000,
          gross_margin_rate: 0.380952,
        },
      },
      quotes: {
        items: [
          {
            id: 41,
            quote_code: "Q-001",
            status: "DRAFT",
            current_version: {
              total_price: 420000,
              gross_margin: 38.1,
            },
          },
        ],
        total: 1,
      },
    });

    renderPage();

    expect(await screen.findByText("售前方案闭环状态")).toBeInTheDocument();
    expect(screen.getByText("成本基线")).toBeInTheDocument();
    expect(screen.getByText("报价单")).toBeInTheDocument();
    expect(screen.getByText("Q-001")).toBeInTheDocument();
    expect(screen.getByText("已生成 1 张报价")).toBeInTheDocument();
    expect(screen.getAllByText("聚合上下文售前方案").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/26\.0 万/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/42\.0 万/).length).toBeGreaterThan(0);
    expect(screen.getByText("38.1%")).toBeInTheDocument();
  });

  it("scopes solution list by sales support ticket context", async () => {
    renderPage();

    await waitFor(() => {
      expect(presaleApi.solutions.list).toHaveBeenCalledWith(
        expect.objectContaining({
          page: 1,
          page_size: 100,
          opportunity_id: "2",
          ticket_id: "501",
        }),
      );
    });
  });

  it("links generated solutions to the current opportunity and support ticket", async () => {
    renderPage();

    fireEvent.click(screen.getByText("方案生成"));
    fireEvent.change(screen.getByPlaceholderText("例如：新能源PACK线FCT测试方案"), {
      target: { value: "ERP 改造售前技术方案" },
    });
    fireEvent.click(screen.getByRole("button", { name: "生成并保存方案" }));

    await waitFor(() => {
      expect(presaleApi.solutions.create).toHaveBeenCalledWith(
        expect.objectContaining({
          name: "ERP 改造售前技术方案",
          opportunity_id: 2,
          ticket_id: 501,
        }),
      );
    });
  });

  it("submits a draft solution for review from the solution list", async () => {
    presaleApi.solutions.list.mockResolvedValue({
      data: {
        items: [
          {
            id: 88,
            solution_no: "SOL-88",
            name: "待提交售前技术方案",
            status: "DRAFT",
            ticket_id: 501,
            opportunity_id: 2,
          },
        ],
        total: 1,
      },
    });

    renderPage();

    await screen.findByText("待提交售前技术方案");
    fireEvent.click(screen.getByRole("button", { name: "提交评审" }));

    await waitFor(() => {
      expect(presaleApi.solutions.review).toHaveBeenCalledWith(88, {
        review_status: "REVIEW",
        review_comment: "提交方案评审",
      });
    });
  });

  it("keeps draft solutions out of the review approval queue", async () => {
    presaleApi.solutions.list.mockResolvedValue({
      data: {
        items: [
          {
            id: 88,
            solution_no: "SOL-88",
            name: "草稿售前方案",
            status: "DRAFT",
          },
          {
            id: 89,
            solution_no: "SOL-89",
            name: "已提交评审方案",
            status: "REVIEW",
          },
        ],
        total: 2,
      },
    });

    renderPage();

    await screen.findByText("草稿售前方案");
    fireEvent.click(screen.getByRole("button", { name: /方案评审/ }));

    expect(await screen.findByText("已提交评审方案")).toBeInTheDocument();
    expect(screen.queryByText("草稿售前方案")).not.toBeInTheDocument();
  });

  it("prefills generated solution from requirement and technical assessment context", async () => {
    presaleWorkbenchApi.loadContext.mockResolvedValueOnce({
      source: { type: "opportunity", id: 2 },
      ticket: {
        id: 501,
        product_name: "电池包",
        opportunity_name: "EOL终测",
      },
      assessment: {
        current: {
          id: 701,
          total_score: 86,
          decision: "可行",
        },
        requirementDetail: {
          id: 301,
          requirement_version: "REQ-LEAD-V1",
          target_object_type: "电池包",
          application_scenario: "EOL终测",
          industry: "新能源",
          cycle_time_seconds: 18,
          workstation_count: 2,
          acceptance_basis: "客户 URS",
          requirement_items: ["电性能测试", "扫码追溯", "安全联锁"],
          technical_spec: ["MES 对接", "换型治具"],
        },
      },
      solutions: { items: [], total: 0 },
    });

    renderPage(
      "/presales/technical-solutions?tab=solutions&type=support&lead_id=2026&opportunity_id=2&ticket_id=501&project_id=42",
    );

    fireEvent.click(await screen.findByText("方案生成"));

    expect(await screen.findByDisplayValue("电池包-EOL终测售前技术方案")).toBeInTheDocument();
    const requirementTextarea = screen.getByPlaceholderText(
      "填写产线痛点、交付目标、关键性能指标，AI会自动生成方案结构",
    );
    expect(requirementTextarea.value).toContain("被测对象：电池包");
    expect(requirementTextarea.value).toContain("节拍目标：18s");
    expect(requirementTextarea.value).toContain("工位数量：2");
    expect(requirementTextarea.value).toContain("验收口径：客户 URS");
    expect(requirementTextarea.value).toContain("技术评估：86分，可行");

    fireEvent.click(screen.getByRole("button", { name: "生成并保存方案" }));

    await waitFor(() => {
      expect(presaleApi.solutions.create).toHaveBeenCalled();
    });
    const payload = presaleApi.solutions.create.mock.calls.at(-1)[0];
    expect(payload).toEqual(
      expect.objectContaining({
        name: "电池包-EOL终测售前技术方案",
        lead_id: 2026,
        opportunity_id: 2,
        ticket_id: 501,
        project_id: 42,
      }),
    );
    expect(payload).not.toHaveProperty("context_data");
    expect(payload.requirement_summary).toContain("关键需求：电性能测试、扫码追溯、安全联锁");
    expect(payload.technical_spec).toContain("需求版本：REQ-LEAD-V1");
    expect(payload.technical_spec).toContain("技术评估ID：701");
    expect(payload.technical_spec).toContain("技术评估：86分，可行");
  });

  it("keeps project context when listing and generating solutions from project presales entry", async () => {
    renderPage(
      "/presales/technical-solutions?tab=solutions&type=support&opportunity_id=2&ticket_id=501&project_id=42",
    );

    await waitFor(() => {
      expect(presaleApi.solutions.list).toHaveBeenCalledWith(
        expect.objectContaining({
          page: 1,
          page_size: 100,
          opportunity_id: "2",
          ticket_id: "501",
          project_id: "42",
        }),
      );
    });

    fireEvent.click(screen.getByText("方案生成"));
    fireEvent.change(screen.getByPlaceholderText("例如：新能源PACK线FCT测试方案"), {
      target: { value: "项目现场交付补充方案" },
    });
    fireEvent.click(screen.getByRole("button", { name: "生成并保存方案" }));

    await waitFor(() => {
      expect(presaleApi.solutions.create).toHaveBeenCalledWith(
        expect.objectContaining({
          name: "项目现场交付补充方案",
          opportunity_id: 2,
          ticket_id: 501,
          project_id: 42,
        }),
      );
    });
  });

  it("keeps lead context when listing solutions from a converted lead support flow", async () => {
    renderPage(
      "/presales/technical-solutions?tab=solutions&type=support&lead_id=2026&opportunity_id=2&ticket_id=501&project_id=42",
    );

    await waitFor(() => {
      expect(presaleApi.solutions.list).toHaveBeenCalledWith(
        expect.objectContaining({
          page: 1,
          page_size: 100,
          lead_id: "2026",
          opportunity_id: "2",
          ticket_id: "501",
          project_id: "42",
        }),
      );
    });
  });

  it("links generated lead-stage solutions back to the current lead", async () => {
    renderPage(
      "/presales/technical-solutions?tab=solutions&type=support&lead_id=2026",
    );

    fireEvent.click(screen.getByText("方案生成"));
    fireEvent.change(screen.getByPlaceholderText("例如：新能源PACK线FCT测试方案"), {
      target: { value: "线索阶段售前技术方案" },
    });
    fireEvent.click(screen.getByRole("button", { name: "生成并保存方案" }));

    await waitFor(() => {
      expect(presaleApi.solutions.create).toHaveBeenCalledWith(
        expect.objectContaining({
          name: "线索阶段售前技术方案",
          lead_id: 2026,
        }),
      );
    });
  });

  it("keeps sales and project context when opening a solution detail", async () => {
    presaleApi.solutions.list.mockResolvedValue({
      data: {
        items: [
          {
            id: 88,
            solution_no: "SOL-88",
            name: "项目现场交付补充方案",
            status: "DRAFT",
            ticket_id: 501,
            opportunity_id: 2,
            project_id: 42,
          },
        ],
        total: 1,
      },
    });

    renderPage(
      "/presales/technical-solutions?tab=solutions&type=support&opportunity_id=2&ticket_id=501&project_id=42",
    );

    await screen.findByText("项目现场交付补充方案");
    fireEvent.click(screen.getByRole("button", { name: "查看详情" }));

    expect(navigateMock).toHaveBeenCalledWith(
      "/solutions/88?ticket_id=501&opportunity_id=2&project_id=42",
    );
  });

  it("opens quote creation from an approved solution with sales context", async () => {
    presaleApi.solutions.list.mockResolvedValue({
      data: {
        items: [
          {
            id: 88,
            solution_no: "SOL-88",
            name: "已通过售前技术方案",
            status: "APPROVED",
            customer_id: 1,
            lead_id: 2026,
            ticket_id: 501,
            opportunity_id: 2,
            project_id: 42,
            estimated_cost: 180000,
            suggested_price: 280000,
          },
        ],
        total: 1,
      },
    });

    renderPage(
      "/presales/technical-solutions?tab=solutions&type=support&lead_id=2026&opportunity_id=2&ticket_id=501&project_id=42",
    );

    await screen.findByText("已通过售前技术方案");
    fireEvent.click(screen.getByRole("button", { name: "生成报价" }));

    expect(navigateMock).toHaveBeenCalledWith(
      "/sales/quotes/create?opportunity_id=2&customer_id=1&solution_id=88&ticket_id=501&lead_id=2026&project_id=42",
    );
  });

  it("treats approved review status as quote-ready even when legacy status is stale", async () => {
    presaleApi.solutions.list.mockResolvedValue({
      data: {
        items: [
          {
            id: 89,
            solution_no: "SOL-89",
            name: "历史状态售前技术方案",
            status: "DRAFT",
            review_status: "APPROVED",
            customer_id: 1,
            ticket_id: 501,
            opportunity_id: 2,
            project_id: 42,
            estimated_cost: 190000,
            suggested_price: 300000,
          },
        ],
        total: 1,
      },
    });

    renderPage(
      "/presales/technical-solutions?tab=solutions&type=support&opportunity_id=2&ticket_id=501&project_id=42",
    );

    await screen.findByText("历史状态售前技术方案");
    expect(screen.getAllByText("已通过").length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole("button", { name: "生成报价" }));

    expect(navigateMock).toHaveBeenCalledWith(
      "/sales/quotes/create?opportunity_id=2&customer_id=1&solution_id=89&ticket_id=501&project_id=42",
    );
  });

  it("keeps lead context when opening a linked solution detail", async () => {
    presaleApi.solutions.list.mockResolvedValue({
      data: {
        items: [
          {
            id: 88,
            solution_no: "SOL-88",
            name: "线索转商机售前方案",
            status: "DRAFT",
            ticket_id: 501,
            opportunity_id: 2,
            project_id: 42,
          },
        ],
        total: 1,
      },
    });

    renderPage(
      "/presales/technical-solutions?tab=solutions&type=support&lead_id=2026&opportunity_id=2&ticket_id=501&project_id=42",
    );

    await screen.findByText("线索转商机售前方案");
    fireEvent.click(screen.getByRole("button", { name: "查看详情" }));

    expect(navigateMock).toHaveBeenCalledWith(
      "/solutions/88?ticket_id=501&lead_id=2026&opportunity_id=2&project_id=42",
    );
  });

  it("keeps context when opening the newly generated solution detail", async () => {
    renderPage(
      "/presales/technical-solutions?tab=solutions&type=support&opportunity_id=2&ticket_id=501&project_id=42",
    );

    fireEvent.click(screen.getByText("方案生成"));
    fireEvent.change(screen.getByPlaceholderText("例如：新能源PACK线FCT测试方案"), {
      target: { value: "项目现场交付补充方案" },
    });
    fireEvent.click(screen.getByRole("button", { name: "生成并保存方案" }));

    await screen.findByText("最近生成方案");
    fireEvent.click(screen.getByRole("button", { name: /打开方案详情/ }));

    expect(navigateMock).toHaveBeenCalledWith(
      "/solutions/900?ticket_id=501&opportunity_id=2&project_id=42",
    );
  });
});
