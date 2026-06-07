import { render, waitFor } from "@testing-library/react";
import { MemoryRouter, useSearchParams } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import RequirementSurvey from "../RequirementSurvey";
import { presaleApi } from "../../services/api";

vi.mock("../../services/api", () => ({
  presaleApi: {
    tickets: {
      list: vi.fn(),
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
  });

  it("scopes requirement surveys by sales support ticket context", async () => {
    renderPage();

    await waitFor(() => {
      expect(presaleApi.tickets.list).toHaveBeenCalledWith(
        expect.objectContaining({
          page: 1,
          page_size: 100,
          opportunity_id: "2",
          ticket_id: "501",
        }),
      );
    });
  });

  it("keeps project context when loading surveys from project presales entry", async () => {
    renderPage(
      "/presales/technical-solutions?tab=surveys&opportunity_id=2&ticket_id=501&project_id=42",
    );

    await waitFor(() => {
      expect(presaleApi.tickets.list).toHaveBeenCalledWith(
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
});
