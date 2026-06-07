import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { MemoryRouter, useSearchParams } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import BiddingCenter from "../BiddingCenter";
import { presaleApi } from "../../services/api";

vi.mock("../../services/api", () => ({
  presaleApi: {
    tenders: {
      list: vi.fn(),
      create: vi.fn(),
    },
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
    useSearchParams.mockReturnValue([new URLSearchParams(), vi.fn()]);
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
