import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, waitFor } from "@testing-library/react";

const mocks = vi.hoisted(() => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
}));

vi.mock("../services/api", () => ({
  default: {
    get: mocks.apiGet,
    post: mocks.apiPost,
  },
}));

import EngineerCollaboration from "./EngineerCollaboration.jsx";

describe("EngineerCollaboration", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    mocks.apiGet.mockImplementation((url) => {
      if (url.includes("/pending")) {
        return Promise.resolve({ data: { code: 200, data: [] } });
      }
      if (url.includes("/matrix")) {
        return Promise.resolve({ data: { code: 200, data: { matrix: {}, details: [] } } });
      }
      return Promise.resolve({ data: { code: 200, data: { items: [] } } });
    });
  });

  it("does not request received/given ratings with an undefined user id", async () => {
    render(<EngineerCollaboration />);

    await waitFor(() => {
      expect(mocks.apiGet).toHaveBeenCalledWith(
        "/api/v1/engineer-performance/collaboration/pending",
      );
    });

    const calledUrls = mocks.apiGet.mock.calls.map(([url]) => url);
    expect(calledUrls).not.toContain(
      "/api/v1/engineer-performance/collaboration/received/undefined",
    );
    expect(calledUrls).not.toContain(
      "/api/v1/engineer-performance/collaboration/given/undefined",
    );
  });
});
