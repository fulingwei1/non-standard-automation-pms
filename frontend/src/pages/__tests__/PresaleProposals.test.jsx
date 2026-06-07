import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import PresaleProposals from "../PresaleProposals";
import { presaleApi } from "../../services/api";

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
      "/presales/technical-solutions?tab=solutions&type=support&opportunity_id=2&ticket_id=501&project_id=42",
    );

    await screen.findByText("已通过售前技术方案");
    fireEvent.click(screen.getByRole("button", { name: "生成报价" }));

    expect(navigateMock).toHaveBeenCalledWith(
      "/sales/quotes/create?opportunity_id=2&customer_id=1&solution_id=88&ticket_id=501&project_id=42",
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
