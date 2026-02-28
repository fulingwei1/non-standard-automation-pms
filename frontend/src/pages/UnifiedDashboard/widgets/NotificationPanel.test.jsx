import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

vi.mock("../../../services/api", () => ({
  notificationApi: {
    list: vi.fn(),
  },
}));

import NotificationPanel from "./NotificationPanel.jsx";
import { notificationApi } from "../../../services/api";

function renderPanel(props = {}) {
  return render(
    <MemoryRouter>
      <NotificationPanel {...props} />
    </MemoryRouter>,
  );
}

describe("NotificationPanel widget", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders notifications from API response and hides the fallback list", async () => {
    const apiItems = [
      {
        id: 101,
        type: "alert",
        title: "API 消息",
        message: "来自接口的通知",
        time: "刚刚",
        read: false,
      },
    ];

    notificationApi.list.mockResolvedValueOnce({ data: { items: apiItems } });

    renderPanel();

    expect(await screen.findByText("API 消息")).toBeInTheDocument();
    expect(screen.getByText("来自接口的通知")).toBeInTheDocument();
    expect(screen.getByText("刚刚")).toBeInTheDocument();

    await waitFor(() => {
      expect(notificationApi.list).toHaveBeenCalledTimes(1);
    });

    expect(
      screen.queryByText("项目 PJ250101-001 进度延期预警"),
    ).not.toBeInTheDocument();
  });

  it("falls back to default notifications when API fails", async () => {
    notificationApi.list.mockRejectedValueOnce(new Error("Unauthorized"));

    renderPanel();

    await waitFor(() => {
      expect(notificationApi.list).toHaveBeenCalledTimes(1);
    });

    expect(
      await screen.findByText("项目 PJ250101-001 进度延期预警"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("当前进度落后计划 3 天"),
    ).toBeInTheDocument();
  });
});
