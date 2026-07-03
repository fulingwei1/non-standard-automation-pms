import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { createRequire } from "node:module";

const require = createRequire(new URL("../../frontend/package.json", import.meta.url));
const { chromium } = require("playwright");

const ROOT = process.env.QA_ROOT || "http://127.0.0.1:5173";
const USERNAME = process.env.QA_USER || "admin";
const PASSWORD = process.env.QA_PASSWORD || "admin123";
const DB_PATH = process.env.QA_DB_PATH || "data/app.db";
const headless = process.env.QA_HEADLESS !== "0";
const stamp = new Date().toISOString().replace(/[-:TZ.]/g, "").slice(0, 14);
const runPrefix = `QA_PROC_${stamp}`;
const reportDir = path.resolve(".gstack/qa-reports");
const screenshotDir = path.join(reportDir, "screenshots");
fs.mkdirSync(screenshotDir, { recursive: true });

const report = {
  stamp,
  runPrefix,
  root: ROOT,
  headless,
  dbPath: DB_PATH,
  steps: [],
  created: {
    suppliers: [],
    purchaseRequests: [],
    purchaseOrders: [],
    purchaseOrderItems: [],
    goodsReceipts: [],
    goodsReceiptItems: [],
  },
  findings: [],
  cleanup: [],
  console: [],
  pageErrors: [],
  requestFailures: [],
  apiErrors: [],
  dialogs: [],
  screenshots: [],
};

const writeReport = () => {
  const file = path.join(reportDir, `procurement-full-crud-sweep-${stamp}.json`);
  fs.writeFileSync(file, JSON.stringify(report, null, 2));
  return file;
};

const parseJson = (text) => {
  try {
    return text ? JSON.parse(text) : null;
  } catch {
    return null;
  }
};

const unwrap = (payload) => payload?.data?.data ?? payload?.data ?? payload ?? {};

const listItems = (payload) => {
  const data = unwrap(payload);
  if (Array.isArray(data)) return data;
  return data?.items || [];
};

const saveScreenshot = async (page, label) => {
  const safe = label.replace(/[^a-z0-9\u4e00-\u9fa5_-]+/gi, "_").slice(0, 100);
  const file = path.join(screenshotDir, `procurement-full-${safe}-${stamp}.png`);
  await page.screenshot({ path: file, fullPage: true }).catch(() => {});
  report.screenshots.push(file);
  return file;
};

const isIgnorableExternalResourceFailure = (url) =>
  url.startsWith("https://rsms.me/inter/font-files/");

const waitQuiet = async (page, settleMs = 650) => {
  await page.waitForLoadState("networkidle", { timeout: 3000 }).catch(() => {});
  await page.waitForTimeout(settleMs);
};

const isLoginPage = async (page) => {
  if (new URL(page.url()).pathname === "/login") return true;
  const loginInput = page.locator('input[placeholder="请输入用户名"]').first();
  return (await loginInput.count()) > 0 && (await loginInput.isVisible().catch(() => false));
};

const ensureAuthenticated = async (page) => {
  await page.goto(`${ROOT}/login`, { waitUntil: "domcontentloaded", timeout: 20000 });
  await waitQuiet(page);
  if (!(await isLoginPage(page))) return;

  await page.locator('input[placeholder="请输入用户名"]').fill(USERNAME);
  await page.locator('input[placeholder="请输入密码"]').fill(PASSWORD);
  await page.getByRole("button", { name: /^登录$/ }).click({ timeout: 8000 });
  await page.waitForURL((url) => new URL(url).pathname !== "/login", { timeout: 20000 }).catch(() => {});
  await waitQuiet(page);

  if (await isLoginPage(page)) {
    throw new Error("UI login did not leave /login");
  }
};

const gotoRoute = async (page, route, settleMs = 800) => {
  await page.goto(`${ROOT}${route}`, { waitUntil: "domcontentloaded", timeout: 20000 });
  await waitQuiet(page, settleMs);
  if (await isLoginPage(page)) {
    await ensureAuthenticated(page);
    await page.goto(`${ROOT}${route}`, { waitUntil: "domcontentloaded", timeout: 20000 });
    await waitQuiet(page, settleMs);
  }
};

const browserApi = async (page, method, apiPath, body) => {
  const result = await page.evaluate(
    async ({ method: requestMethod, apiPath: requestPath, body: requestBody }) => {
      const token = window.localStorage.getItem("token");
      const headers = { "Content-Type": "application/json" };
      if (token && !token.startsWith("demo_token_")) {
        headers.Authorization = `Bearer ${token}`;
      }
      const response = await fetch(`/api/v1${requestPath}`, {
        method: requestMethod,
        headers,
        body: requestBody === undefined ? undefined : JSON.stringify(requestBody),
      });
      const text = await response.text();
      let json = null;
      try {
        json = text ? JSON.parse(text) : null;
      } catch {
        json = null;
      }
      return { ok: response.ok, status: response.status, json, text };
    },
    { method, apiPath, body },
  );

  if (!result.ok) {
    throw new Error(`${method} ${apiPath} -> ${result.status}: ${result.text?.slice(0, 600)}`);
  }
  return result.json;
};

const waitForApi = async (page, method, pattern, action) => {
  const responsePromise = page
    .waitForResponse(
      (response) =>
        response.url().includes(pattern) &&
        response.request().method().toUpperCase() === method.toUpperCase(),
      { timeout: 25000 },
    )
    .then((response) => ({ response }), (error) => ({ error }));
  await action();
  const { response, error } = await responsePromise;
  if (error) throw error;
  const body = await response.text().catch(() => "");
  if (!response.ok()) {
    throw new Error(`${method} ${pattern} -> ${response.status()}: ${body.slice(0, 600)}`);
  }
  return { status: response.status(), body, json: parseJson(body) };
};

const runStep = async (page, name, fn) => {
  const step = { name, startedAt: new Date().toISOString(), status: "running" };
  report.steps.push(step);
  console.log(`[step] ${name}`);
  const before = {
    apiErrors: report.apiErrors.length,
    pageErrors: report.pageErrors.length,
    requestFailures: report.requestFailures.length,
    console: report.console.length,
  };
  try {
    const result = await fn(step);
    step.status = "passed";
    step.result = result;
  } catch (error) {
    step.status = "failed";
    step.error = error?.stack || error?.message || String(error);
    step.screenshot = await saveScreenshot(page, `failed-${name}`);
  } finally {
    step.finishedAt = new Date().toISOString();
    step.newErrors = {
      apiErrors: report.apiErrors.length - before.apiErrors,
      pageErrors: report.pageErrors.length - before.pageErrors,
      requestFailures: report.requestFailures.length - before.requestFailures,
      console: report.console.length - before.console,
    };
    writeReport();
  }
};

const selectRadixByPlaceholder = async (page, scope, placeholder, optionName) => {
  let trigger = scope.getByRole("combobox").filter({ hasText: placeholder }).first();
  if ((await trigger.count()) === 0) {
    trigger = scope.getByText(placeholder).first();
  }
  await trigger.waitFor({ state: "visible", timeout: 10000 });
  await trigger.click();
  await page.getByRole("option", { name: new RegExp(optionName.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")) }).first().click();
};

const cardByText = (page, text, buttonTitle) =>
  page
    .getByText(text, { exact: false })
    .first()
    .locator(`xpath=ancestor::*[contains(@class,'border') and .//button[@title='${buttonTitle}']][1]`);

const clickConfirmDialog = async (page) => {
  const dialog = page.getByRole("dialog", { name: /请确认|确认/ }).last();
  await dialog.waitFor({ state: "visible", timeout: 10000 });
  await dialog.getByRole("button", { name: /^确认$/ }).click();
};

const idList = (ids) => (ids.length ? ids.join(",") : "NULL");

const dbExec = (sql) => {
  if (!fs.existsSync(DB_PATH)) return "";
  return execFileSync("sqlite3", [DB_PATH, sql], { encoding: "utf8" }).trim();
};

const cleanupCreated = () => {
  const cleanupSql = [
    `DELETE FROM goods_receipt_items WHERE receipt_id IN (${idList(report.created.goodsReceipts)});`,
    `DELETE FROM goods_receipt_items WHERE id IN (${idList(report.created.goodsReceiptItems)});`,
    `DELETE FROM goods_receipts WHERE id IN (${idList(report.created.goodsReceipts)});`,
    `DELETE FROM purchase_order_items WHERE order_id IN (${idList(report.created.purchaseOrders)});`,
    `DELETE FROM purchase_order_items WHERE id IN (${idList(report.created.purchaseOrderItems)});`,
    `DELETE FROM purchase_orders WHERE id IN (${idList(report.created.purchaseOrders)});`,
    `DELETE FROM purchase_request_items WHERE request_id IN (${idList(report.created.purchaseRequests)});`,
    `DELETE FROM purchase_requests WHERE id IN (${idList(report.created.purchaseRequests)});`,
    `DELETE FROM vendors WHERE id IN (${idList(report.created.suppliers)}) AND supplier_code LIKE '${runPrefix}%';`,
  ].join("\n");
  const output = dbExec(cleanupSql);
  report.cleanup.push({ sql: cleanupSql, output, at: new Date().toISOString() });
  writeReport();
};

const assertNoPageCrashed = async (page) => {
  const bodyText = await page.locator("body").innerText({ timeout: 10000 }).catch(() => "");
  if (!bodyText.trim()) {
    throw new Error(`Blank page at ${page.url()}`);
  }
  if (/Cannot read properties|ReferenceError|TypeError|Internal Server Error/i.test(bodyText)) {
    throw new Error(`Crash-like text visible at ${page.url()}: ${bodyText.slice(0, 300)}`);
  }
};

let supplierId;
let supplierName;
let requestId;
let requestNo;
let orderId;
let orderNo;
let receiptId;
const materialCode = `${runPrefix}_MAT_001`;
const requestMaterialCode = `${runPrefix}_REQ_MAT`;

const createSupplierViaUi = async (page) => {
  supplierName = `${runPrefix} 供应商`;
  await gotoRoute(page, "/suppliers", 1000);
  await page.getByText("供应商管理").first().waitFor({ state: "visible", timeout: 10000 });
  await page.getByRole("button", { name: /新增供应商/ }).first().click();
  const dialog = page.getByRole("dialog", { name: /新建供应商/ });
  await dialog.waitFor({ state: "visible", timeout: 10000 });
  await dialog.getByPlaceholder("请输入供应商编码").fill(`${runPrefix}_SUP`);
  await dialog.getByPlaceholder("请输入供应商名称").fill(supplierName);
  await dialog.getByPlaceholder("请输入供应商简称").fill("QA采购供应商");
  await dialog.getByPlaceholder("如：电子元器件、机械件等").fill("MATERIAL");
  await dialog.getByPlaceholder("请输入联系人姓名").fill("采购QA");
  await dialog.getByPlaceholder("请输入联系电话").fill("13800000000");
  await dialog.getByPlaceholder("请输入联系邮箱").fill("qa-proc@example.com");
  await dialog.getByPlaceholder("请输入供应商地址").fill("QA采购测试地址");

  const response = await waitForApi(page, "POST", "/api/v1/suppliers", async () => {
    await dialog.getByRole("button", { name: /创建供应商/ }).click();
  });
  const supplier = unwrap(response.json);
  supplierId = supplier.id;
  if (!supplierId) {
    const list = listItems(await browserApi(page, "GET", `/suppliers/?keyword=${encodeURIComponent(runPrefix)}`));
    supplierId = list.find((item) => item.supplier_name === supplierName)?.id;
  }
  if (!supplierId) throw new Error("Supplier creation response/list did not provide supplier id");
  report.created.suppliers.push(supplierId);

  await page.getByText(supplierName).first().waitFor({ state: "visible", timeout: 15000 });
  await saveScreenshot(page, "supplier-created");
  return { supplierId, supplierName };
};

const createPurchaseRequestViaUi = async (page) => {
  await gotoRoute(page, "/purchase-requests/new", 1000);
  await page.getByText("新建采购申请").first().waitFor({ state: "visible", timeout: 10000 });
  await selectRadixByPlaceholder(page, page, "选择供应商", supplierName);
  await page.locator('input[type="date"]').first().fill("2026-07-20");
  await page.getByPlaceholder("填写申请原因...").fill(`${runPrefix} 采购申请原因：真实浏览器全链路测试。`);
  await page.getByPlaceholder("备注信息（可选）...").fill(`${runPrefix} 采购申请备注`);
  await page.getByRole("button", { name: /添加物料/ }).click();
  await page.getByPlaceholder("物料编码").fill(requestMaterialCode);
  await page.getByPlaceholder("物料名称 *").fill(`${runPrefix} 申请物料`);
  const itemNumbers = page.locator('input[type="number"]');
  await itemNumbers.nth(0).fill("2");
  await itemNumbers.nth(1).fill("18.5");
  const dates = page.locator('input[type="date"]');
  if ((await dates.count()) > 1) {
    await dates.nth(1).fill("2026-07-20");
  }

  const response = await waitForApi(page, "POST", "/api/v1/purchase-orders/requests", async () => {
    await page.getByRole("button", { name: /保存草稿/ }).click();
  });
  const request = unwrap(response.json);
  requestId = request.id;
  requestNo = request.request_no;
  if (!requestId) throw new Error("Purchase request creation response missing id");
  report.created.purchaseRequests.push(requestId);

  await page.waitForURL((url) => new URL(url).pathname === "/purchase-requests", { timeout: 15000 }).catch(() => {});
  await waitQuiet(page);
  await page.getByText(requestNo).first().waitFor({ state: "visible", timeout: 15000 });
  await saveScreenshot(page, "purchase-request-created");
  return { requestId, requestNo };
};

const submitAndApprovePurchaseRequestViaUi = async (page) => {
  await gotoRoute(page, "/purchase-requests", 1000);
  await page.getByText(requestNo).first().waitFor({ state: "visible", timeout: 10000 });
  await waitForApi(page, "PUT", `/api/v1/purchase-orders/requests/${requestId}/submit`, async () => {
    await cardByText(page, requestNo, "提交").locator('button[title="提交"]').click();
  });
  await waitQuiet(page, 800);
  await page.getByText(requestNo).first().waitFor({ state: "visible", timeout: 10000 });
  await waitForApi(page, "PUT", `/api/v1/purchase-orders/requests/${requestId}/approve`, async () => {
    await cardByText(page, requestNo, "审批通过").locator('button[title="审批通过"]').click();
    await clickConfirmDialog(page);
    const approveDialog = page.getByRole("dialog", { name: /审批采购申请/ });
    await approveDialog.waitFor({ state: "visible", timeout: 10000 });
    await approveDialog.getByPlaceholder("请输入审批意见...").fill(`${runPrefix} QA审批通过`);
    await approveDialog.getByRole("button", { name: /^审批通过$/ }).click();
  });
  const detail = unwrap(await browserApi(page, "GET", `/purchase-orders/requests/${requestId}`));
  if (detail.status !== "APPROVED") {
    throw new Error(`Purchase request expected APPROVED, got ${detail.status}`);
  }
  await saveScreenshot(page, "purchase-request-approved");
  return { status: detail.status };
};

const createPurchaseOrderViaUi = async (page) => {
  await gotoRoute(page, "/purchases", 1000);
  await page.getByText("采购订单管理").first().waitFor({ state: "visible", timeout: 10000 });
  await page.getByRole("button", { name: /新建订单|创建第一个采购订单/ }).first().click();
  const dialog = page.getByRole("dialog", { name: /新建采购订单|创建采购订单/ });
  await dialog.waitFor({ state: "visible", timeout: 10000 });
  await selectRadixByPlaceholder(page, dialog, "选择供应商", supplierName);
  await dialog.locator('input[type="date"]').first().fill("2026-07-15");
  await dialog.getByPlaceholder("订单备注信息...").fill(`${runPrefix} 采购订单备注`);
  await dialog.getByRole("button", { name: /添加明细/ }).click();
  await dialog.getByPlaceholder("如 MAT-QA-001").fill(materialCode);
  await dialog.getByPlaceholder("请输入物料名称").fill(`${runPrefix} 订单物料`);
  await dialog.getByPlaceholder("规格型号").fill("QA-SPEC-001");
  const lineNumbers = dialog.locator('input[type="number"]');
  await lineNumbers.nth(0).fill("3");
  await lineNumbers.nth(1).fill("128.5");

  const response = await waitForApi(page, "POST", "/api/v1/purchase-orders/", async () => {
    await dialog.getByRole("button", { name: /创建订单/ }).click();
  });
  const order = unwrap(response.json);
  orderId = order.id;
  orderNo = order.order_no;
  if (!orderId || !orderNo) throw new Error("Purchase order creation response missing id/order_no");
  report.created.purchaseOrders.push(orderId);
  for (const item of order.items || []) {
    report.created.purchaseOrderItems.push(item.id);
  }

  await page.getByText(orderNo).first().waitFor({ state: "visible", timeout: 15000 });
  await saveScreenshot(page, "purchase-order-created");
  return { orderId, orderNo };
};

const submitAndApprovePurchaseOrder = async (page) => {
  await gotoRoute(page, "/purchases", 1000);
  await page.getByText(orderNo).first().waitFor({ state: "visible", timeout: 10000 });
  await waitForApi(page, "PUT", `/api/v1/purchase-orders/${orderId}/submit`, async () => {
    await cardByText(page, orderNo, "提交审批").locator('button[title="提交审批"]').click();
  });
  const submitted = unwrap(await browserApi(page, "GET", `/purchase-orders/${orderId}`));
  if (submitted.status !== "SUBMITTED") {
    throw new Error(`Purchase order expected SUBMITTED after UI submit, got ${submitted.status}`);
  }

  await page.getByText(orderNo).first().waitFor({ state: "visible", timeout: 10000 });
  await cardByText(page, orderNo, "审批驳回")
    .locator('button[title="审批驳回"]')
    .waitFor({ state: "visible", timeout: 10000 });
  await waitForApi(page, "PUT", `/api/v1/purchase-orders/${orderId}/approve`, async () => {
    await cardByText(page, orderNo, "审批通过").locator('button[title="审批通过"]').click();
    const dialog = page.getByRole("dialog", { name: /审批采购订单/ });
    await dialog.waitFor({ state: "visible", timeout: 10000 });
    await dialog.getByPlaceholder(/填写通过意见/).fill(`${runPrefix} QA审批通过`);
    await dialog.getByRole("button", { name: /^审批通过$/ }).click();
  });
  const approved = unwrap(await browserApi(page, "GET", `/purchase-orders/${orderId}`));
  if (approved.status !== "APPROVED") {
    throw new Error(`Purchase order expected APPROVED, got ${approved.status}`);
  }
  await saveScreenshot(page, "purchase-order-approved");
  return { status: approved.status };
};

const createReceiptViaUi = async (page) => {
  await gotoRoute(page, `/purchases/receipts/new?order_id=${orderId}`, 1000);
  await page.getByText("新建收货单").first().waitFor({ state: "visible", timeout: 10000 });
  await page.getByText(orderNo).first().waitFor({ state: "visible", timeout: 10000 });
  await page.getByPlaceholder("送货单号（可选）").fill(`${runPrefix}_DN`);
  await page.getByPlaceholder("物流公司（可选）").fill("QA Logistics");
  await page.getByPlaceholder("物流单号（可选）").fill(`${runPrefix}_TRACK`);
  await page.getByPlaceholder("备注信息（可选）").fill(`${runPrefix} 收货备注`);
  const availableItem = page
    .getByText(materialCode, { exact: true })
    .locator("xpath=ancestor::div[contains(@class,'cursor-pointer')][1]");
  await availableItem.waitFor({ state: "visible", timeout: 10000 });
  await availableItem.click();
  await page.getByText("收货明细").first().waitFor({ state: "visible", timeout: 10000 });

  const response = await waitForApi(page, "POST", "/api/v1/purchase-orders/goods-receipts/", async () => {
    await page.getByRole("button", { name: /^创建收货单$/ }).click();
  });
  const receipt = unwrap(response.json);
  receiptId = receipt.id;
  if (!receiptId) throw new Error("Goods receipt creation response missing id");
  report.created.goodsReceipts.push(receiptId);

  await page.waitForURL((url) => new URL(url).pathname === `/purchases/receipts/${receiptId}`, { timeout: 15000 });
  await waitQuiet(page);
  await page.getByText("收货单信息").first().waitFor({ state: "visible", timeout: 10000 });
  await saveScreenshot(page, "goods-receipt-created");
  return { receiptId };
};

const receiveAndInspectViaUi = async (page) => {
  await gotoRoute(page, `/purchases/receipts/${receiptId}`, 1000);
  await page.getByText("收货单信息").first().waitFor({ state: "visible", timeout: 10000 });
  await waitForApi(page, "PUT", `/api/v1/purchase-orders/goods-receipts/${receiptId}/receive`, async () => {
    await page.getByRole("button", { name: /确认收货/ }).click();
  });
  await waitQuiet(page, 800);
  const row = page.locator("tr").filter({ hasText: materialCode }).first();
  await row.waitFor({ state: "visible", timeout: 10000 });
  await row.locator("button").last().click();
  const dialog = page.getByRole("dialog", { name: /^质检$/ });
  await dialog.waitFor({ state: "visible", timeout: 10000 });
  const inputs = dialog.locator('input[type="number"]');
  await inputs.nth(1).fill("3");
  await waitForApi(page, "PUT", `/api/v1/purchase-orders/goods-receipts/${receiptId}/items/`, async () => {
    await dialog.getByRole("button", { name: /^保存$/ }).click();
  });
  await waitQuiet(page, 800);
  const receiptItems = await browserApi(page, "GET", `/purchase-orders/goods-receipts/${receiptId}/items`);
  for (const item of receiptItems || []) {
    report.created.goodsReceiptItems.push(item.id);
  }
  const inspectedItem = (receiptItems || []).find((item) => item.material_code === materialCode);
  if (!inspectedItem || inspectedItem.inspect_result !== "QUALIFIED") {
    throw new Error(`Receipt item expected QUALIFIED, got ${inspectedItem?.inspect_result}`);
  }
  await saveScreenshot(page, "goods-receipt-inspected");
  return { inspectResult: inspectedItem.inspect_result };
};

const verifyApiState = async (page) => {
  const suppliers = listItems(await browserApi(page, "GET", `/suppliers/?keyword=${encodeURIComponent(runPrefix)}`));
  const request = unwrap(await browserApi(page, "GET", `/purchase-orders/requests/${requestId}`));
  const order = unwrap(await browserApi(page, "GET", `/purchase-orders/${orderId}`));
  const receipt = await browserApi(page, "GET", `/purchase-orders/goods-receipts/${receiptId}`);
  const receiptItems = await browserApi(page, "GET", `/purchase-orders/goods-receipts/${receiptId}/items`);

  if (!suppliers.some((supplier) => supplier.id === supplierId)) {
    throw new Error("Created supplier not found through /suppliers keyword search");
  }
  if (request.status !== "APPROVED") {
    throw new Error(`Purchase request status expected APPROVED, got ${request.status}`);
  }
  if (order.status !== "APPROVED" && order.status !== "RECEIVED") {
    throw new Error(`Purchase order status expected APPROVED/RECEIVED, got ${order.status}`);
  }
  if (receipt.status !== "RECEIVED") {
    throw new Error(`Goods receipt status expected RECEIVED, got ${receipt.status}`);
  }
  const item = (receiptItems || []).find((entry) => entry.material_code === materialCode);
  if (!item || item.inspect_result !== "QUALIFIED" || Number(item.qualified_qty) !== 3) {
    throw new Error("Goods receipt item did not persist qualified inspection result");
  }

  return {
    supplierId,
    requestStatus: request.status,
    orderStatus: order.status,
    receiptStatus: receipt.status,
    qualifiedQty: item.qualified_qty,
  };
};

const verifyReadOnlyCenters = async (page) => {
  const routes = [
    { route: "/procurement/execution-center", texts: ["采购订单", "采购申请", "收货管理"] },
    { route: "/procurement/material-center", texts: ["BOM管理", "物料管理", "物料需求"] },
    { route: "/procurement/analysis-center", texts: ["齐套缺料", "价格趋势", "采购分析"] },
  ];
  const visited = [];
  for (const item of routes) {
    await gotoRoute(page, item.route, 1000);
    await assertNoPageCrashed(page);
    for (const text of item.texts) {
      const tab = page.locator("button").filter({ hasText: text }).first();
      await tab.waitFor({ state: "visible", timeout: 10000 });
      await tab.click();
      await waitQuiet(page, 500);
      await assertNoPageCrashed(page);
    }
    visited.push(item.route);
  }
  return { visited };
};

const verifyCleanup = () => {
  cleanupCreated();
  const residualSql = `
    SELECT
      (SELECT COUNT(*) FROM vendors WHERE supplier_code LIKE '${runPrefix}%') AS vendors_count,
      (SELECT COUNT(*) FROM purchase_requests WHERE id IN (${idList(report.created.purchaseRequests)})) AS request_count,
      (SELECT COUNT(*) FROM purchase_orders WHERE id IN (${idList(report.created.purchaseOrders)})) AS order_count,
      (SELECT COUNT(*) FROM goods_receipts WHERE id IN (${idList(report.created.goodsReceipts)})) AS receipt_count;
  `;
  const output = dbExec(residualSql);
  const counts = output.split("|").map((value) => Number(value || 0));
  const residual = {
    vendors: counts[0] || 0,
    purchaseRequests: counts[1] || 0,
    purchaseOrders: counts[2] || 0,
    goodsReceipts: counts[3] || 0,
  };
  report.cleanup.push({ residual, at: new Date().toISOString() });
  writeReport();
  if (Object.values(residual).some((count) => count !== 0)) {
    throw new Error(`Cleanup residuals remain: ${JSON.stringify(residual)}`);
  }
  return residual;
};

async function main() {
  const browser = await chromium.launch({ headless, slowMo: headless ? 0 : 60 });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  const page = await context.newPage();

  page.on("console", (msg) => {
    const type = msg.type();
    const text = msg.text();
    if (/Failed to load resource: net::ERR_QUIC_PROTOCOL_ERROR/.test(text)) {
      return;
    }
    if (type === "error" || /DialogContent requires a DialogDescription|Cannot read properties|ReferenceError|TypeError/.test(text)) {
      report.console.push({ type, text, url: page.url(), at: new Date().toISOString() });
    }
  });
  page.on("pageerror", (error) => {
    report.pageErrors.push({ message: error.message, stack: error.stack, url: page.url(), at: new Date().toISOString() });
  });
  page.on("requestfailed", (request) => {
    if (isIgnorableExternalResourceFailure(request.url())) {
      return;
    }
    report.requestFailures.push({
      url: request.url(),
      method: request.method(),
      failure: request.failure()?.errorText,
      at: new Date().toISOString(),
    });
  });
  page.on("response", async (response) => {
    if (response.url().includes("/api/v1/") && response.status() >= 400) {
      report.apiErrors.push({
        url: response.url(),
        method: response.request().method(),
        status: response.status(),
        text: (await response.text().catch(() => "")).slice(0, 600),
        at: new Date().toISOString(),
      });
    }
  });
  page.on("dialog", async (dialog) => {
    report.dialogs.push({ type: dialog.type(), message: dialog.message(), at: new Date().toISOString() });
    await dialog.accept().catch(() => {});
  });

  try {
    await runStep(page, "login", async () => {
      await ensureAuthenticated(page);
      await saveScreenshot(page, "login-ok");
      return { user: USERNAME };
    });
    await runStep(page, "create supplier via UI", async () => createSupplierViaUi(page));
    await runStep(page, "create purchase request via UI", async () => createPurchaseRequestViaUi(page));
    await runStep(page, "submit and approve purchase request via UI", async () => submitAndApprovePurchaseRequestViaUi(page));
    await runStep(page, "create purchase order via UI", async () => createPurchaseOrderViaUi(page));
    await runStep(page, "submit purchase order and approve via UI", async () => submitAndApprovePurchaseOrder(page));
    await runStep(page, "create goods receipt via UI", async () => createReceiptViaUi(page));
    await runStep(page, "receive and inspect goods receipt via UI", async () => receiveAndInspectViaUi(page));
    await runStep(page, "verify procurement API state", async () => verifyApiState(page));
    await runStep(page, "verify procurement center routes", async () => verifyReadOnlyCenters(page));
    await runStep(page, "cleanup and verify residuals", () => verifyCleanup());
  } finally {
    await browser.close();
  }

  const failed = report.steps.filter((step) => step.status !== "passed");
  const evidenceFile = writeReport();
  console.log(`[report] ${evidenceFile}`);
  if (failed.length > 0) {
    throw new Error(`Procurement QA failed ${failed.length} step(s): ${failed.map((step) => step.name).join(", ")}`);
  }
  if (report.pageErrors.length || report.requestFailures.length || report.apiErrors.length) {
    throw new Error(
      `Procurement QA collected browser/API errors: page=${report.pageErrors.length}, request=${report.requestFailures.length}, api=${report.apiErrors.length}`,
    );
  }
}

main().catch((error) => {
  const evidenceFile = writeReport();
  console.error(error);
  console.error(`[report] ${evidenceFile}`);
  try {
    cleanupCreated();
  } catch (cleanupError) {
    console.error("[cleanup failed]", cleanupError);
  }
  process.exit(1);
});
