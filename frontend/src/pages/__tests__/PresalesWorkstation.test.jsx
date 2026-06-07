import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import PresalesWorkstation from "../PresalesWorkstation";

const apiMocks = vi.hoisted(() => ({
  presaleApi: {
    tickets: {
      list: vi.fn(),
      get: vi.fn(),
      update: vi.fn(),
      updateProgress: vi.fn(),
    },
    solutions: {
      list: vi.fn(),
      update: vi.fn(),
      create: vi.fn(),
    },
    tenders: {
      list: vi.fn(),
    },
  },
  opportunityApi: {
    list: vi.fn(),
  },
}));

vi.mock("../../services/api", () => apiMocks);

describe("PresalesWorkstation", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("does not replace failed live tickets with demo tasks", async () => {
    apiMocks.presaleApi.tickets.list.mockRejectedValue(new Error("Network Error"));

    render(
      <MemoryRouter>
        <PresalesWorkstation />
      </MemoryRouter>,
    );

    expect(await screen.findByText(/Network Error/)).toBeInTheDocument();
    expect(screen.queryByText("新能源电池测试方案")).not.toBeInTheDocument();
    expect(screen.queryByText("汽车电子成本核算")).not.toBeInTheDocument();
  });
});
