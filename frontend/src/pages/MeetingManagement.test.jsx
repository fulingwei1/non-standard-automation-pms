import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

vi.mock("../services/api", () => ({
  pmoApi: {
    meetings: {
      list: vi.fn().mockResolvedValue({ data: { items: [], total: 0 } }),
      get: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
    },
  },
}));

import MeetingManagement from "./MeetingManagement.jsx";
import { pmoApi } from "../services/api";

describe("MeetingManagement", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    pmoApi.meetings.list.mockResolvedValue({ data: { items: [], total: 0 } });
  });

  it("renders meeting type/status options without treating constants as arrays", async () => {
    render(<MeetingManagement />);

    await waitFor(() => {
      expect(screen.getByText("会议管理")).toBeInTheDocument();
    });
  });

  it("opens edit dialog when meeting_date is loaded as an API string", async () => {
    const user = userEvent.setup();
    pmoApi.meetings.list.mockResolvedValue({
      data: {
        items: [
          {
            id: 7,
            meeting_name: "项目周会",
            meeting_type: "regular",
            meeting_date: "2026-07-01 09:30",
            status: "scheduled",
            participants: [],
          },
        ],
        total: 1,
      },
    });

    render(<MeetingManagement />);

    await user.click(await screen.findByRole("button", { name: /编\s*辑/ }));

    expect(screen.getByText("编辑会议")).toBeInTheDocument();
    expect(screen.getByDisplayValue("项目周会")).toBeInTheDocument();
  });
});
