import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, waitFor } from "@testing-library/react";
import { MemoryRouter, useSearchParams } from "react-router-dom";
import Acceptance from "../index";
import { acceptanceApi, projectApi } from "../../../services/api";

vi.mock("../../../services/api", () => ({
  acceptanceApi: {
    orders: {
      list: vi.fn(),
      get: vi.fn(),
      create: vi.fn(),
      getItems: vi.fn(),
    },
    issues: {
      list: vi.fn(),
    },
  },
  projectApi: {
    list: vi.fn(),
  },
}));

vi.mock("framer-motion", () => ({
  motion: new Proxy(
    {},
    {
      get:
        (_, tag) =>
        ({ children, ...props }) => {
          const ignored = new Set([
            "initial",
            "animate",
            "exit",
            "variants",
            "transition",
            "whileHover",
            "whileTap",
            "layout",
          ]);
          const filtered = Object.fromEntries(
            Object.entries(props).filter(([key]) => !ignored.has(key)),
          );
          const Tag = typeof tag === "string" ? tag : "div";
          return <Tag {...filtered}>{children}</Tag>;
        },
    },
  ),
}));

vi.mock("../../../components/layout", () => ({
  PageHeader: ({ title, actions }) => (
    <div>
      <h1>{title}</h1>
      {actions}
    </div>
  ),
}));

vi.mock("../AcceptanceCard", () => ({
  default: ({ acceptance }) => <div>{acceptance.projectName || acceptance.id}</div>,
}));

vi.mock("../AcceptanceDetailDialog", () => ({
  default: () => null,
}));

describe("Acceptance project context", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useSearchParams.mockReturnValue([
      new URLSearchParams("project_id=42&contract_id=9"),
      vi.fn(),
    ]);
    acceptanceApi.orders.list.mockResolvedValue({ data: { items: [] } });
    acceptanceApi.issues.list.mockResolvedValue({ data: { items: [] } });
    acceptanceApi.orders.getItems.mockResolvedValue({ data: { items: [] } });
    projectApi.list.mockResolvedValue({ data: { items: [] } });
  });

  it("passes project context from query params to acceptance and project loading", async () => {
    render(
      <MemoryRouter>
        <Acceptance />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(acceptanceApi.orders.list).toHaveBeenCalledWith(
        expect.objectContaining({
          project_id: "42",
        }),
      );
    });

    await waitFor(() => {
      expect(projectApi.list).toHaveBeenCalledWith({
        page_size: 1000,
        project_id: "42",
      });
    });
  });
});
