import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import AfterSalesCenter from "../AfterSalesCenter";
import { api } from "../../../services/api";

vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useParams: () => ({ projectId: "42" }),
  };
});

vi.mock("../../../services/api", () => ({
  api: {
    get: vi.fn(),
    put: vi.fn(),
  },
}));

describe("AfterSalesCenter AS-07 contracts", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.get.mockImplementation((url) => {
      if (url === "/after-sales/projects/42/feedback") {
        return Promise.resolve([]);
      }
      if (url === "/after-sales/projects/42/maintenance") {
        return Promise.resolve([]);
      }
      if (url === "/service/tickets") {
        return Promise.resolve({
          data: {
            items: [
              {
                id: 7,
                ticket_no: "AS07-ST-001",
                problem_type: "TECHNICAL",
                problem_desc: "统一服务工单",
                urgency: "HIGH",
                status: "PENDING",
                created_at: "2026-07-04T09:00:00",
              },
            ],
          },
        });
      }
      throw new Error(`Unexpected GET ${url}`);
    });
    api.put.mockResolvedValue({});
  });

  it("loads project tickets from the central service ticket API and can move them forward", async () => {
    render(<AfterSalesCenter />);

    await userEvent.click(await screen.findByRole("tab", { name: "支持工单" }));

    expect(await screen.findByText("AS07-ST-001")).toBeInTheDocument();
    expect(api.get).toHaveBeenCalledWith("/service/tickets", {
      params: { project_id: "42" },
    });
    expect(api.get).not.toHaveBeenCalledWith("/after-sales/projects/42/support-tickets");

    await userEvent.click(screen.getByRole("button", { name: "开始处理" }));

    await waitFor(() => {
      expect(api.put).toHaveBeenCalledWith("/service/tickets/7/status", null, {
        params: { status: "IN_PROGRESS" },
      });
    });
  });
});
