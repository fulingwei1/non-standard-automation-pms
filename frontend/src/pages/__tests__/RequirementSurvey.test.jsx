import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, useSearchParams } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import RequirementSurvey from "../RequirementSurvey";
import { presaleApi, presaleWorkbenchApi } from "../../services/api";

vi.mock("../../services/api", () => ({
  presaleApi: {
    tickets: {
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
  initialEntry = "/presales/technical-solutions?tab=surveys&opportunity_id=2&ticket_id=501",
) {
  const url = new URL(initialEntry, "http://localhost");
  useSearchParams.mockReturnValue([url.searchParams, vi.fn()]);

  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <RequirementSurvey embedded />
    </MemoryRouter>,
  );
}

describe("RequirementSurvey", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    presaleApi.tickets.list.mockResolvedValue({ data: { items: [], total: 0 } });
    presaleWorkbenchApi.loadContext.mockResolvedValue({
      ticket: null,
      assessment: { requirementDetail: null },
      collaboration: {
        openItems: { items: [], total: 0, blocking_count: 0 },
      },
    });
    presaleApi.tickets.create.mockResolvedValue({
      data: {
        id: 910,
        title: "线索现场需求调研",
        ticket_type: "REQUIREMENT_RESEARCH",
        status: "PENDING",
      },
    });
    vi.spyOn(window, "alert").mockImplementation(() => {});
  });

  it("scopes requirement surveys by opportunity context without over-narrowing by current ticket", async () => {
    renderPage();

    await waitFor(() => {
      expect(presaleApi.tickets.list).toHaveBeenCalledWith(
        expect.objectContaining({
          page: 1,
          page_size: 100,
          opportunity_id: "2",
        }),
      );
    });
    expect(presaleApi.tickets.list.mock.calls[0][0]).not.toHaveProperty("ticket_id");
    expect(presaleWorkbenchApi.loadContext).toHaveBeenCalledWith({
      sourceType: "opportunity",
      sourceId: 2,
      presaleTicketId: 501,
    });
  });

  it("keeps project context without over-narrowing surveys by current ticket", async () => {
    renderPage(
      "/presales/technical-solutions?tab=surveys&opportunity_id=2&ticket_id=501&project_id=42",
    );

    await waitFor(() => {
      expect(presaleApi.tickets.list).toHaveBeenCalledWith(
        expect.objectContaining({
          page: 1,
          page_size: 100,
          opportunity_id: "2",
          project_id: "42",
        }),
      );
    });
    expect(presaleApi.tickets.list.mock.calls[0][0]).not.toHaveProperty("ticket_id");
    expect(presaleWorkbenchApi.loadContext).toHaveBeenCalledWith({
      sourceType: "opportunity",
      sourceId: 2,
      presaleTicketId: 501,
    });
  });

  it("shows structured requirement package from the presale workbench context", async () => {
    presaleWorkbenchApi.loadContext.mockResolvedValueOnce({
      ticket: {
        id: 501,
        customer_name: "华南电子",
        applicant_name: "张销售",
        assignee_name: "李售前",
        opportunity_name: "电池包 EOL 测试线",
      },
      assessment: {
        requirementDetail: {
          id: 301,
          lead_id: 2026,
          requirement_version: "REQ-LEAD-V1",
          target_object_type: "电池包",
          application_scenario: "EOL终测",
          requirement_maturity: 4,
          has_sow: true,
          cycle_time_seconds: 18,
          workstation_count: 2,
          acceptance_basis: "客户 URS",
          requirement_items: "[\"高压绝缘测试\", \"通讯测试\"]",
          technical_spec: "[\"MES上传\", \"扫码追溯\"]",
        },
      },
      collaboration: {
        openItems: {
          items: [{ item_title: "确认上下料方式" }],
          total: 1,
          blocking_count: 1,
        },
      },
    });

    renderPage(
      "/presales/technical-solutions?tab=surveys&lead_id=2026&opportunity_id=2&ticket_id=501",
    );

    await waitFor(() => {
      expect(presaleWorkbenchApi.loadContext).toHaveBeenCalledWith({
        sourceType: "lead",
        sourceId: 2026,
        presaleTicketId: 501,
      });
    });

    expect(await screen.findByText("REQ-LEAD-V1")).toBeInTheDocument();
    expect(screen.getByText("华南电子")).toBeInTheDocument();
    expect(screen.getByText(/被测对象：电池包/)).toBeInTheDocument();
    expect(screen.getByText("1 个待确认问题")).toBeInTheDocument();

    fireEvent.click(screen.getByText("华南电子"));
    expect(screen.getByText("高压绝缘测试")).toBeInTheDocument();
    expect(screen.getByText("MES上传")).toBeInTheDocument();
    expect(screen.getByText("确认上下料方式")).toBeInTheDocument();
    expect(screen.getByText("客户 SOW / URS")).toBeInTheDocument();
  });

  it("opens the editable lead requirement package from opportunity context", async () => {
    presaleWorkbenchApi.loadContext.mockResolvedValueOnce({
      ticket: {
        id: 501,
        customer_name: "华南电子",
        opportunity_name: "电池包 EOL 测试线",
      },
      assessment: {
        requirementDetail: {
          id: 301,
          lead_id: 2026,
          requirement_version: "REQ-LEAD-V1",
          target_object_type: "电池包",
        },
      },
      collaboration: {
        openItems: { items: [], total: 0, blocking_count: 0 },
      },
    });

    renderPage("/presales/technical-solutions?tab=surveys&opportunity_id=2&ticket_id=501");

    expect(await screen.findByText("REQ-LEAD-V1")).toBeInTheDocument();
    fireEvent.click(screen.getByText("华南电子"));

    expect(screen.getByRole("link", { name: /打开需求包/ })).toHaveAttribute(
      "href",
      "/sales/leads/2026/requirement",
    );
  });

  it("keeps lead context without over-narrowing surveys by current ticket", async () => {
    renderPage(
      "/presales/technical-solutions?tab=surveys&lead_id=2026&opportunity_id=2&ticket_id=501",
    );

    await waitFor(() => {
      expect(presaleApi.tickets.list).toHaveBeenCalledWith(
        expect.objectContaining({
          page: 1,
          page_size: 100,
          lead_id: "2026",
          opportunity_id: "2",
        }),
      );
    });
    expect(presaleApi.tickets.list.mock.calls[0][0]).not.toHaveProperty("ticket_id");
    expect(presaleWorkbenchApi.loadContext).toHaveBeenCalledWith({
      sourceType: "lead",
      sourceId: 2026,
      presaleTicketId: 501,
    });
  });

  it("uses exact ticket scope when ticket is the only available context", async () => {
    renderPage("/presales/technical-solutions?tab=surveys&ticket_id=501");

    await waitFor(() => {
      expect(presaleApi.tickets.list).toHaveBeenCalledWith(
        expect.objectContaining({
          page: 1,
          page_size: 100,
          ticket_id: "501",
        }),
      );
    });
    expect(presaleWorkbenchApi.loadContext).not.toHaveBeenCalled();
  });

  it("creates a requirement survey ticket from the unified presales context", async () => {
    renderPage(
      "/presales/technical-solutions?tab=surveys&lead_id=2026&opportunity_id=2&ticket_id=501&project_id=42",
    );

    await waitFor(() => {
      expect(presaleApi.tickets.list).toHaveBeenCalled();
    });

    fireEvent.click(screen.getByRole("button", { name: "新建调研" }));
    fireEvent.change(screen.getByLabelText("调研标题"), {
      target: { value: "线索现场需求调研" },
    });
    fireEvent.change(screen.getByLabelText("客户名称"), {
      target: { value: "华南电子" },
    });
    fireEvent.change(screen.getByLabelText("期望调研日期"), {
      target: { value: "2026-06-20" },
    });
    fireEvent.change(screen.getByLabelText("调研说明"), {
      target: { value: "确认节拍、治具、上下料和验收口径" },
    });
    fireEvent.click(screen.getByRole("button", { name: "创建调研" }));

    await waitFor(() => {
      expect(presaleApi.tickets.create).toHaveBeenCalledWith({
        title: "线索现场需求调研",
        ticket_type: "REQUIREMENT_RESEARCH",
        urgency: "NORMAL",
        customer_name: "华南电子",
        expected_date: "2026-06-20",
        description: "确认节拍、治具、上下料和验收口径",
        lead_id: 2026,
        opportunity_id: 2,
        project_id: 42,
      });
    });
    expect(presaleApi.tickets.list).toHaveBeenCalledTimes(2);
  });
});
