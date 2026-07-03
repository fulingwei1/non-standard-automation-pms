import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import MonthlySummary from "../MonthlySummary";

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

vi.mock("../../hooks/useMonthlySummary", () => ({
  useMonthlySummary: () => ({
    currentPeriod: {
      year: 2026,
      month: 6,
      startDate: "2026-06-01",
      endDate: "2026-06-30",
    },
    formData: {
      workContent: "",
      selfEvaluation: "",
      highlights: "",
      problems: "",
      nextMonthPlan: "",
    },
    isDraft: true,
    isSaving: false,
    isSubmitting: false,
    showHistory: false,
    setShowHistory: vi.fn(),
    isLoading: false,
    history: [],
    error: "",
    handleInputChange: vi.fn(),
    loadHistory: vi.fn(),
    handleSaveDraft: vi.fn(),
    handleSubmit: vi.fn(),
  }),
}));

describe("MonthlySummary", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("renders auth user data that uses real_name instead of name", () => {
    localStorage.setItem(
      "user",
      JSON.stringify({
        id: 15,
        username: "admin",
        real_name: "系统管理员",
        department: "系统",
        position: "系统管理员",
      }),
    );

    render(
      <MemoryRouter>
        <MonthlySummary />
      </MemoryRouter>,
    );

    expect(screen.getByText("系统管理员")).toBeInTheDocument();
    expect(screen.getByText("系统 · 系统管理员")).toBeInTheDocument();
  });
});
