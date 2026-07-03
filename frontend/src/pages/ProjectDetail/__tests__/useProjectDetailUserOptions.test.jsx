import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi, beforeEach } from "vitest";

import { useProjectDetail } from "../useProjectDetail";
import { memberApi, userApi } from "../../../services/api";

vi.mock("../../../services/api", () => ({
  projectApi: {
    get: vi.fn().mockResolvedValue({ data: { id: 1, project_name: "项目" } }),
  },
  machineApi: {
    list: vi.fn().mockResolvedValue({ data: { items: [] } }),
  },
  stageApi: {
    list: vi.fn().mockResolvedValue({ data: { items: [] } }),
  },
  milestoneApi: {
    list: vi.fn().mockResolvedValue({ data: { items: [] } }),
  },
  memberApi: {
    list: vi.fn().mockResolvedValue({ data: { items: [{ id: 10, user_id: 2 }] } }),
    add: vi.fn().mockResolvedValue({ data: { id: 11 } }),
  },
  userApi: {
    list: vi.fn().mockResolvedValue({ data: { items: [] } }),
    options: vi.fn().mockResolvedValue({
      data: {
        items: [
          { id: 2, username: "existing", real_name: "已在项目" },
          { id: 3, username: "candidate", real_name: "可选成员" },
        ],
      },
    }),
  },
  costApi: {
    list: vi.fn().mockResolvedValue({ data: { items: [] } }),
  },
  documentApi: {
    list: vi.fn().mockResolvedValue({ data: { items: [] } }),
  },
}));

vi.mock("../../../components/ui", () => ({
  toast: {
    warning: vi.fn(),
    success: vi.fn(),
    error: vi.fn(),
  },
}));

function Probe() {
  const { handleOpenAddMember, members, availableUsers } = useProjectDetail();

  return (
    <div>
      <div data-testid="member-count">{members.length}</div>
      <button onClick={handleOpenAddMember}>open-users</button>
      <ul>
        {availableUsers.map((user) => (
          <li key={user.id}>{user.real_name || user.username}</li>
        ))}
      </ul>
    </div>
  );
}

describe("useProjectDetail user choices", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("loads add-member choices from user options instead of the management list", async () => {
    render(
      <MemoryRouter initialEntries={["/projects/1"]}>
        <Routes>
          <Route path="/projects/:id" element={<Probe />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId("member-count")).toHaveTextContent("1");
    });

    fireEvent.click(screen.getByText("open-users"));

    await waitFor(() => {
      expect(userApi.options).toHaveBeenCalledWith({
        page: 1,
        page_size: 200,
        is_active: true,
      });
    });
    expect(userApi.list).not.toHaveBeenCalled();
    expect(await screen.findByText("可选成员")).toBeInTheDocument();
    expect(screen.queryByText("已在项目")).not.toBeInTheDocument();
    expect(memberApi.list).toHaveBeenCalledWith({ project_id: "1" });
  });
});
