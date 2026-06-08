import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { MemoryRouter, useNavigate, useSearchParams } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import BiddingCenter from "../BiddingCenter";
import { presaleApi, presaleWorkbenchApi } from "../../services/api";

const navigateMock = vi.hoisted(() => vi.fn());

vi.mock("../../services/api", () => ({
  presaleApi: {
    tenders: {
      list: vi.fn(),
      create: vi.fn(),
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
        return ({ children, ...props }) => <Tag {...props}>{children}</Tag>;
      },
    },
  ),
  AnimatePresence: ({ children }) => children,
}));

const tenders = [
  {
    id: 1,
    tender_no: "BID-2026-001",
    tender_name: "智能制造系统",
    customer_name: "上海智能制造有限公司",
    status: "PREPARING",
    deadline: "2030-03-15T00:00:00Z",
    budget_amount: 5000000,
    responsible_name: "张三",
    sales_person_name: "李四",
    progress: 45,
    tech_requirements: "高速装配与视觉检测",
  },
  {
    id: 2,
    tender_no: "BID-2026-002",
    tender_name: "ERP系统升级",
    customer_name: "北京科技公司",
    result: "WON",
    deadline: "2030-04-20T00:00:00Z",
    budget_amount: 3000000,
    responsible_name: "王五",
    sales_person_name: "赵六",
    progress: 100,
    tech_requirements: "生产计划与库存集成",
  },
];

function renderPage(props = {}) {
  return render(
    <MemoryRouter>
      <BiddingCenter {...props} />
    </MemoryRouter>,
  );
}

describe("BiddingCenter", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useNavigate.mockReturnValue(navigateMock);
    useSearchParams.mockReturnValue([new URLSearchParams(), vi.fn()]);
    presaleWorkbenchApi.loadContext.mockResolvedValue({
      source: { type: "opportunity", id: 2 },
      tenders: { items: [], total: 0 },
    });
    presaleApi.tenders.list.mockResolvedValue({ data: { items: tenders } });
    presaleApi.tenders.create.mockResolvedValue({
      data: {
        id: 3,
        tender_no: "BID-2026-003",
        tender_name: "售前支持投标",
        result: "PENDING",
      },
    });
  });

  it("prefers presale workbench context tenders before falling back to tender list", async () => {
    useSearchParams.mockReturnValue([
      new URLSearchParams("tab=bids&type=support&opportunity_id=2&ticket_id=501"),
      vi.fn(),
    ]);
    presaleWorkbenchApi.loadContext.mockResolvedValueOnce({
      source: { type: "opportunity", id: 2 },
      tenders: {
        items: [
          {
            id: 88,
            tender_no: "TENDER-001",
            tender_name: "聚合上下文投标",
            customer_name: "华南电子",
            result: "WON",
            deadline: "2030-05-20T00:00:00Z",
            our_bid_amount: 420000,
            ticket_id: 501,
            opportunity_id: 2,
          },
        ],
        total: 1,
      },
    });

    renderPage({ embedded: true });

    await waitFor(() => {
      expect(presaleWorkbenchApi.loadContext).toHaveBeenCalledWith({
        sourceType: "opportunity",
        sourceId: 2,
        presaleTicketId: 501,
      });
    });
    expect(presaleApi.tenders.list).not.toHaveBeenCalled();
    expect(await screen.findByText("聚合上下文投标")).toBeInTheDocument();
    expect(screen.getByText("华南电子")).toBeInTheDocument();
    expect(screen.getAllByText("¥42万").length).toBeGreaterThan(0);
    expect(screen.getAllByText("已中标").length).toBeGreaterThan(0);
  });

  it("loads tenders into the current kanban view", async () => {
    renderPage();

    expect(screen.getByRole("heading", { name: "投标中心" })).toBeInTheDocument();
    expect(await screen.findByText("智能制造系统")).toBeInTheDocument();
    expect(screen.getByText("ERP系统升级")).toBeInTheDocument();
    expect(screen.getByText("¥500万")).toBeInTheDocument();
    expect(screen.getAllByText("准备中").length).toBeGreaterThan(0);
    expect(screen.getAllByText("已中标").length).toBeGreaterThan(0);
    expect(presaleApi.tenders.list).toHaveBeenCalledWith({ page: 1, page_size: 100 });
  });

  it("keeps the bidding search input empty before the user types", async () => {
    renderPage({ embedded: true });

    await screen.findByText("智能制造系统");

    expect(screen.getByPlaceholderText("搜索项目名称、客户、编号...")).toHaveValue("");
  });

  it("hides the standalone page header when embedded", async () => {
    renderPage({ embedded: true });

    expect(screen.queryByRole("heading", { name: "投标中心" })).not.toBeInTheDocument();
    expect(await screen.findByText("智能制造系统")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "新建投标" })).toBeInTheDocument();
  });

  it("reloads with keyword and filters visible cards", async () => {
    renderPage();

    expect(await screen.findByText("智能制造系统")).toBeInTheDocument();

    fireEvent.change(screen.getByPlaceholderText("搜索项目名称、客户、编号..."), {
      target: { value: "ERP" },
    });

    await waitFor(() => {
      expect(presaleApi.tenders.list).toHaveBeenLastCalledWith({
        page: 1,
        page_size: 100,
        keyword: "ERP",
      });
    });

    expect(screen.queryByText("智能制造系统")).not.toBeInTheDocument();
    expect(screen.getByText("ERP系统升级")).toBeInTheDocument();
  });

  it("scopes tender list by sales support ticket context", async () => {
    useSearchParams.mockReturnValue([
      new URLSearchParams("tab=bids&type=support&opportunity_id=2&ticket_id=501"),
      vi.fn(),
    ]);

    renderPage({ embedded: true });

    await waitFor(() => {
      expect(presaleApi.tenders.list).toHaveBeenCalledWith(
        expect.objectContaining({
          page: 1,
          page_size: 100,
          opportunity_id: "2",
          ticket_id: "501",
        }),
      );
    });
  });

  it("keeps lead context when listing tenders from lead-stage presales entry", async () => {
    useSearchParams.mockReturnValue([
      new URLSearchParams("tab=bids&type=support&lead_id=2026&ticket_id=501"),
      vi.fn(),
    ]);

    renderPage({ embedded: true });

    await waitFor(() => {
      expect(presaleApi.tenders.list).toHaveBeenCalledWith(
        expect.objectContaining({
          page: 1,
          page_size: 100,
          lead_id: "2026",
          ticket_id: "501",
        }),
      );
    });
  });

  it("keeps project context when listing tenders from project presales entry", async () => {
    useSearchParams.mockReturnValue([
      new URLSearchParams("tab=bids&type=support&opportunity_id=2&ticket_id=501&project_id=42"),
      vi.fn(),
    ]);

    renderPage({ embedded: true });

    await waitFor(() => {
      expect(presaleApi.tenders.list).toHaveBeenCalledWith(
        expect.objectContaining({
          page: 1,
          page_size: 100,
          opportunity_id: "2",
          ticket_id: "501",
          project_id: "42",
        }),
      );
    });
  });

  it("creates a tender from the current sales support context", async () => {
    vi.spyOn(window, "alert").mockImplementation(() => {});
    useSearchParams.mockReturnValue([
      new URLSearchParams("tab=bids&type=support&opportunity_id=2&ticket_id=501&project_id=42"),
      vi.fn(),
    ]);

    renderPage({ embedded: true });

    await screen.findByText("智能制造系统");
    fireEvent.click(screen.getByRole("button", { name: "新建投标" }));
    fireEvent.change(screen.getByLabelText("投标项目名称"), {
      target: { value: "售前支持投标" },
    });
    fireEvent.change(screen.getByLabelText("招标单位"), {
      target: { value: "重点客户" },
    });
    fireEvent.click(screen.getByRole("button", { name: "创建投标" }));

    await waitFor(() => {
      expect(presaleApi.tenders.create).toHaveBeenCalledWith({
        tender_name: "售前支持投标",
        customer_name: "重点客户",
        opportunity_id: 2,
        ticket_id: 501,
        project_id: 42,
      });
    });
    expect(presaleApi.tenders.list).toHaveBeenCalledTimes(2);
  });

  it("keeps lead context when creating a tender from lead-stage presales entry", async () => {
    vi.spyOn(window, "alert").mockImplementation(() => {});
    useSearchParams.mockReturnValue([
      new URLSearchParams("tab=bids&type=support&lead_id=2026"),
      vi.fn(),
    ]);

    renderPage({ embedded: true });

    await screen.findByText("智能制造系统");
    fireEvent.click(screen.getByRole("button", { name: "新建投标" }));
    fireEvent.change(screen.getByLabelText("投标项目名称"), {
      target: { value: "线索阶段投标支持" },
    });
    fireEvent.change(screen.getByLabelText("招标单位"), {
      target: { value: "线索客户" },
    });
    fireEvent.click(screen.getByRole("button", { name: "创建投标" }));

    await waitFor(() => {
      expect(presaleApi.tenders.create).toHaveBeenCalledWith({
        tender_name: "线索阶段投标支持",
        customer_name: "线索客户",
        lead_id: 2026,
      });
    });
  });

  it("opens cost estimation from a bidding card with sales support context", async () => {
    useSearchParams.mockReturnValue([
      new URLSearchParams("tab=bids&type=support&lead_id=2026&opportunity_id=2&ticket_id=501&project_id=42&solution_id=88"),
      vi.fn(),
    ]);
    presaleApi.tenders.list.mockResolvedValueOnce({
      data: {
        items: [
          {
            ...tenders[0],
            ticket_id: 501,
            lead_id: 2026,
            opportunity_id: 2,
            project_id: 42,
          },
        ],
      },
    });

    renderPage({ embedded: true });

    fireEvent.click(await screen.findByText("智能制造系统"));
    fireEvent.click(screen.getByRole("button", { name: "申请成本支持" }));

    const targetUrl = navigateMock.mock.calls[0][0];
    const target = new URL(targetUrl, "http://localhost");
    expect(target.pathname).toBe("/presales/technical-solutions");
    expect(target.searchParams.get("tab")).toBe("cost");
    expect(target.searchParams.get("type")).toBe("support");
    expect(target.searchParams.get("tender_id")).toBe("1");
    expect(target.searchParams.get("ticket_id")).toBe("501");
    expect(target.searchParams.get("lead_id")).toBe("2026");
    expect(target.searchParams.get("opportunity_id")).toBe("2");
    expect(target.searchParams.get("project_id")).toBe("42");
    expect(target.searchParams.get("solution_id")).toBe("88");
    expect(target.searchParams.get("amount")).toBe("500");
    expect(target.searchParams.get("name")).toBe("智能制造系统");
  });

  it("opens the linked technical solution from a bidding detail with presale context", async () => {
    useSearchParams.mockReturnValue([
      new URLSearchParams("tab=bids&type=support&lead_id=2026&opportunity_id=2&ticket_id=501&project_id=42"),
      vi.fn(),
    ]);
    presaleApi.tenders.list.mockResolvedValueOnce({
      data: {
        items: [
          {
            ...tenders[0],
            ticket_id: 501,
            lead_id: 2026,
            opportunity_id: 2,
            project_id: 42,
            solution_id: 88,
            solution_name: "FCT售前技术方案",
          },
        ],
      },
    });

    renderPage({ embedded: true });

    fireEvent.click(await screen.findByText("智能制造系统"));
    fireEvent.click(screen.getByRole("button", { name: "打开关联方案" }));

    expect(navigateMock).toHaveBeenCalledWith(
      "/solutions/88?tender_id=1&ticket_id=501&lead_id=2026&opportunity_id=2&project_id=42",
    );
  });

  it("shows backend load errors", async () => {
    const consoleErrorSpy = vi.spyOn(console, "error").mockImplementation(() => {});

    try {
      presaleApi.tenders.list.mockRejectedValueOnce({
        response: { data: { detail: "加载投标项目失败" } },
      });

      renderPage();

      expect(await screen.findByText("加载投标项目失败")).toBeInTheDocument();
    } finally {
      consoleErrorSpy.mockRestore();
    }
  });
});
