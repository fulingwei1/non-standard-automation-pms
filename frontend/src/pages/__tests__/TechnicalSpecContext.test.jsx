import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import TechnicalSpecManagement from "../TechnicalSpecManagement";
import SpecMatchCheck from "../SpecMatchCheck";
import api from "../../services/api";

const routeState = vi.hoisted(() => ({
  search: "project_id=42",
}));

vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useSearchParams: () => [new URLSearchParams(routeState.search), vi.fn()],
  };
});

vi.mock("../../services/api", () => {
  const apiMock = {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  };

  return {
    default: apiMock,
    api: apiMock,
  };
});

function renderWithRoute(ui, search = "project_id=42") {
  routeState.search = search;

  return render(<MemoryRouter>{ui}</MemoryRouter>);
}

describe("Technical specification project context", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(window, "alert").mockImplementation(() => {});
    api.get.mockResolvedValue({ data: { items: [], total: 0 } });
    api.post.mockResolvedValue({ data: { id: 1 } });
  });

  it("scopes technical specification requirements by project context and defaults new rows to that project", async () => {
    renderWithRoute(<TechnicalSpecManagement />);

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith("/technical-spec/requirements", {
        params: {
          page: 1,
          page_size: 100,
          project_id: "42",
        },
      });
    });

    expect(screen.getByPlaceholderText("搜索物料名称、规格...")).toHaveValue("");

    fireEvent.click(screen.getByRole("button", { name: /新增规格要求/ }));

    expect(screen.getByPlaceholderText("请输入项目ID")).toHaveValue(42);
  });

  it("scopes spec match records by project context and checks the same project with a valid default type", async () => {
    renderWithRoute(<SpecMatchCheck />);

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith("/technical-spec/match/records", {
        params: {
          page: 1,
          page_size: 100,
          project_id: 42,
        },
      });
    });

    fireEvent.click(screen.getByRole("button", { name: /执行检查/ }));

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith("/technical-spec/match/check", {
        project_id: 42,
        match_type: "BOM",
        match_target_id: undefined,
      });
    });
  });
});
