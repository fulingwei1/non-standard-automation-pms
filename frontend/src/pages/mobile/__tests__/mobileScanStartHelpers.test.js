import {
  OFFLINE_START_QUEUE_KEY,
  enqueueOfflineStartWorkReport,
  flushOfflineStartWorkReports,
  getCameraScanUnavailableMessage,
  isLikelyOfflineStartError,
  readOfflineStartQueue,
} from "../mobileScanStartHelpers";

describe("mobile scan start helpers", () => {
  let storage;

  beforeEach(() => {
    const store = {};
    storage = {
      getItem: vi.fn((key) => store[key] ?? null),
      setItem: vi.fn((key, value) => {
        store[key] = String(value);
      }),
      removeItem: vi.fn((key) => {
        delete store[key];
      }),
    };
  });

  it("queues offline start reports with enough replay context", () => {
    const item = enqueueOfflineStartWorkReport(
      { id: 42, work_order_no: "WO-42", task_name: "装配" },
      "离线开工",
      storage,
      () => new Date("2026-07-04T08:00:00.000Z"),
    );

    const queue = readOfflineStartQueue(storage);
    expect(queue).toHaveLength(1);
    expect(queue[0]).toMatchObject({
      work_order_id: 42,
      work_order_no: "WO-42",
      task_name: "装配",
      report_note: "离线开工",
      queued_at: "2026-07-04T08:00:00.000Z",
    });
    expect(item.client_id).toContain("offline-start-42");
    expect(storage.setItem).toHaveBeenCalledWith(
      OFFLINE_START_QUEUE_KEY,
      expect.any(String),
    );
  });

  it("flushes queued starts and preserves failed items", async () => {
    enqueueOfflineStartWorkReport(
      { id: 1, work_order_no: "WO-1", task_name: "装配" },
      "",
      storage,
      () => new Date("2026-07-04T08:00:00.000Z"),
    );
    enqueueOfflineStartWorkReport(
      { id: 2, work_order_no: "WO-2", task_name: "接线" },
      "",
      storage,
      () => new Date("2026-07-04T08:01:00.000Z"),
    );
    const startApi = vi
      .fn()
      .mockResolvedValueOnce({ data: { ok: true } })
      .mockRejectedValueOnce(new Error("network"));

    const result = await flushOfflineStartWorkReports(startApi, storage);

    expect(result).toEqual({ attempted: 2, synced: 1, remaining: 1 });
    expect(startApi).toHaveBeenCalledWith(
      expect.objectContaining({
        work_order_id: 1,
        offline_client_id: expect.stringContaining("offline-start-1"),
      }),
    );
    expect(readOfflineStartQueue(storage)).toMatchObject([{ work_order_id: 2 }]);
  });

  it("detects offline start errors without relying on status text", () => {
    expect(isLikelyOfflineStartError({ code: "ERR_NETWORK" }, { onLine: true })).toBe(true);
    expect(isLikelyOfflineStartError(new Error("failed"), { onLine: false })).toBe(true);
    expect(isLikelyOfflineStartError({ response: { status: 500 } }, { onLine: true })).toBe(false);
  });

  it("returns an iOS-specific fallback when BarcodeDetector is unavailable", () => {
    const message = getCameraScanUnavailableMessage(
      {},
      { userAgent: "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X)" },
    );

    expect(message).toContain("iOS");
    expect(message).toContain("手动输入");
  });
});
