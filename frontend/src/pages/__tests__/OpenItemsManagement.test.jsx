import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, useParams } from "react-router-dom";
import OpenItemsManagement from "../OpenItemsManagement";

const technicalAssessmentApiMock = vi.hoisted(() => ({
  getOpenItems: vi.fn(),
  getOpenItemsForSource: vi.fn(),
  createOpenItemForLead: vi.fn(),
  createOpenItemForOpportunity: vi.fn(),
  createOpenItem: vi.fn(),
  closeOpenItem: vi.fn(),
}));

vi.mock("../../services/api", () => ({
  technicalAssessmentApi: technicalAssessmentApiMock,
}));

const renderWithRouter = () =>
  render(
    <MemoryRouter>
      <OpenItemsManagement />
    </MemoryRouter>
  );

describe("OpenItemsManagement", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useParams.mockReturnValue({ sourceType: "leads", sourceId: "5" });
    technicalAssessmentApiMock.getOpenItems.mockResolvedValue({ data: { items: [] } });
    technicalAssessmentApiMock.getOpenItemsForSource.mockResolvedValue({
      data: {
        items: [
          {
            id: 11,
            item_type: "INTERFACE",
            description: "接口协议待客户确认",
            responsible_party: "客户",
            status: "PENDING",
            blocks_quotation: true,
          },
        ],
      },
    });
  });

  it("loads open items through the normalized source API", async () => {
    renderWithRouter();

    await waitFor(() => {
      expect(technicalAssessmentApiMock.getOpenItemsForSource).toHaveBeenCalledWith(
        "leads",
        5,
      );
    });

    expect(await screen.findByText("接口协议待客户确认")).toBeInTheDocument();
    expect(screen.getByText("阻塞报价")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "线索管理" })).toHaveAttribute(
      "href",
      "/sales/leads",
    );
  });
});
