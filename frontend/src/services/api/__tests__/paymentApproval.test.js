import { describe, expect, it, beforeEach, afterEach } from "vitest";
import { setupApiTest, teardownApiTest } from "./_test-setup.js";

describe("paymentApprovalApi route contracts", () => {
  let mock;
  let paymentApprovalApi;

  beforeEach(async () => {
    const setup = await setupApiTest();
    mock = setup.mock;
    ({ paymentApprovalApi } = await import("../paymentApproval.js"));
  });

  afterEach(() => {
    teardownApiTest(mock);
  });

  it("lists pending approvals through the unified approval pending route", async () => {
    mock.onGet("/api/v1/approvals/pending/mine").reply(200, {
      items: [],
      total: 0,
    });

    await paymentApprovalApi.list({ tab: "pending", page_size: 50 });

    expect(mock.history.get[0].url).toBe("/approvals/pending/mine");
    expect(mock.history.get[0].params).toEqual({ page_size: 50 });
  });

  it("lists processed approvals through the unified processed route", async () => {
    mock.onGet("/api/v1/approvals/pending/processed").reply(200, {
      items: [],
      total: 0,
    });

    await paymentApprovalApi.list({ tab: "processed", page_size: 20 });

    expect(mock.history.get[0].url).toBe("/approvals/pending/processed");
    expect(mock.history.get[0].params).toEqual({ page_size: 20 });
  });

  it("approves and rejects through unified approval task routes", async () => {
    mock.onPost("/api/v1/approvals/tasks/7/approve").reply(200, { task_id: 7 });
    mock.onPost("/api/v1/approvals/tasks/8/reject").reply(200, { task_id: 8 });

    await paymentApprovalApi.approve(7, { comment: "同意" });
    await paymentApprovalApi.reject(8, { reason: "资料不完整" });

    expect(mock.history.post[0].url).toBe("/approvals/tasks/7/approve");
    expect(JSON.parse(mock.history.post[0].data)).toEqual({ comment: "同意" });
    expect(mock.history.post[1].url).toBe("/approvals/tasks/8/reject");
    expect(JSON.parse(mock.history.post[1].data)).toEqual({ comment: "资料不完整" });
  });
});
