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
const runPrefix = `QA_DELIVERY_${stamp}`;
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
    projects: [],
    customers: [],
    salesOrders: [],
    salesOrderItems: [],
    deliveryOrders: [],
  },
  cleanup: [],
  console: [],
  pageErrors: [],
  requestFailures: [],
  apiErrors: [],
  dialogs: [],
  screenshots: [],
};

const writeReport = () => {
  const file = path.join(reportDir, `delivery-full-crud-sweep-${stamp}.json`);
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
  const file = path.join(screenshotDir, `delivery-full-${safe}-${stamp}.png`);
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

const selectRadixOption = async (page, placeholder, optionName) => {
  const trigger = page.getByRole("combobox").filter({ hasText: placeholder }).first();
  await trigger.waitFor({ state: "visible", timeout: 10000 });
  await trigger.click();
  await page
    .getByRole("option", { name: new RegExp(optionName.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")) })
    .first()
    .click();
};

const idList = (ids) => (ids.length ? ids.join(",") : "NULL");

const dbExec = (sql) => {
  if (!fs.existsSync(DB_PATH)) return "";
  return execFileSync("sqlite3", [DB_PATH, sql], { encoding: "utf8" }).trim();
};

const cleanupCreated = () => {
  const cleanupSql = [
    `DELETE FROM delivery_orders WHERE id IN (${idList(report.created.deliveryOrders)});`,
    `DELETE FROM sales_order_items WHERE sales_order_id IN (${idList(report.created.salesOrders)});`,
    `DELETE FROM sales_order_items WHERE id IN (${idList(report.created.salesOrderItems)});`,
    `DELETE FROM sales_orders WHERE id IN (${idList(report.created.salesOrders)});`,
    `DELETE FROM projects WHERE id IN (${idList(report.created.projects)}) AND project_code LIKE '${runPrefix}%';`,
    `DELETE FROM customers WHERE id IN (${idList(report.created.customers)}) AND customer_code LIKE '${runPrefix}%';`,
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

let customerId;
let customerName;
let projectId;
let projectCode;
let projectName;
let salesOrderId;
let salesOrderNo;
let deliveryId;
let deliveryNo;
const deliveryDate = "2026-07-18";
const trackingNo = `${runPrefix}_TRACK`;

const createSupportProjectAndSalesOrder = async (page) => {
  customerName = `${runPrefix} 客户`;
  const customer = unwrap(
    await browserApi(page, "POST", "/customers/", {
      customer_code: `${runPrefix}_CUS`,
      customer_name: customerName,
      short_name: "QA发货客户",
      customer_type: "enterprise",
      industry: "自动化测试",
      contact_person: "发货QA",
      contact_phone: "13800000000",
      address: "深圳市南山区 QA 发货测试地址",
    }),
  );
  customerId = customer.id;
  if (!customerId) throw new Error("Customer creation response missing id");
  report.created.customers.push(customerId);

  projectCode = `${runPrefix}_PRJ`.slice(0, 48);
  projectName = `${runPrefix} 发货载体项目`;
  const project = unwrap(
    await browserApi(page, "POST", "/projects/", {
      project_code: projectCode,
      project_name: projectName,
      short_name: `${runPrefix.slice(-8)}发货`,
      customer_id: customerId,
      project_type: "CUSTOM",
      contract_no: `${runPrefix}_CONTRACT`.slice(0, 80),
      contract_date: "2026-07-01",
      planned_start_date: "2026-07-02",
      planned_end_date: "2026-09-18",
      contract_amount: 168000,
      budget_amount: 120000,
      description: `${runPrefix} 发货管理模块真实浏览器验收载体项目`,
    }),
  );
  projectId = project.id;
  if (!projectId) throw new Error("Project creation response missing id");
  report.created.projects.push(projectId);

  salesOrderNo = `${runPrefix}_SO`;
  const salesOrder = unwrap(
    await browserApi(page, "POST", "/business-support-orders/sales-orders", {
      order_no: salesOrderNo,
      customer_id: customerId,
      project_id: projectId,
      order_type: "standard",
      order_amount: 168000,
      currency: "CNY",
      required_date: "2026-07-25",
      promised_date: "2026-07-24",
      sales_person_name: "发货QA销售",
      remark: `${runPrefix} 发货链路临时销售订单`,
      items: [
        {
          item_name: `${runPrefix} 非标测试设备`,
          item_spec: "ICT/FCT-QA",
          qty: 1,
          unit: "套",
          unit_price: 168000,
          amount: 168000,
          remark: "发货QA临时明细",
        },
      ],
    }),
  );
  salesOrderId = salesOrder.id;
  if (!salesOrderId) throw new Error("Sales order creation response missing id");
  report.created.salesOrders.push(salesOrderId);
  for (const item of salesOrder.items || []) {
    report.created.salesOrderItems.push(item.id);
  }
  return { customerId, salesOrderId, salesOrderNo };
};

const verifyNoStandaloneCreateOnGlobalList = async (page) => {
  await gotoRoute(page, "/pmc/delivery-orders", 1000);
  await page.getByText("发货管理").first().waitFor({ state: "visible", timeout: 10000 });
  const createButtonCount = await page
    .getByRole("button", { name: /创建发货单|生成发货计划/ })
    .count();
  if (createButtonCount > 0) {
    throw new Error("Global delivery list exposes standalone create/generate entry");
  }
  await saveScreenshot(page, "delivery-global-no-standalone-create");
  return { route: "/pmc/delivery-orders" };
};

const createDeliveryViaProjectUi = async (page) => {
  await gotoRoute(page, `/projects/${projectId}/delivery`, 1000);
  await page.getByRole("button", { name: /生成发货计划/ }).click();
  await page.waitForURL(
    (url) =>
      new URL(url).pathname === "/pmc/delivery-orders/new" &&
      new URL(url).searchParams.get("project_id") === String(projectId),
    { timeout: 15000 },
  );
  await waitQuiet(page);
  await page.getByText("生成发货计划").first().waitFor({ state: "visible", timeout: 10000 });
  await page.getByText(salesOrderNo).first().waitFor({ state: "visible", timeout: 10000 });

  await page.locator('input[type="date"]').first().fill(deliveryDate);
  await selectRadixOption(page, "选择类型", "物流发货");
  await page.getByPlaceholder("物流公司名称").fill("QA Logistics");
  await page.getByPlaceholder("物流单号").fill(trackingNo);
  await page.getByPlaceholder("金额").fill("168000");
  await page.getByPlaceholder("收货人姓名").fill("发货QA收货人");
  await page.getByPlaceholder("联系电话").fill("13900000000");
  await page.getByPlaceholder("收货地址").fill("深圳市宝安区 QA 收货地址");
  await page.getByPlaceholder("备注信息").fill(`${runPrefix} 从项目交付页生成发货计划`);

  const response = await waitForApi(
    page,
    "POST",
    "/api/v1/business-support-orders/delivery-orders",
    async () => {
      await page.getByRole("button", { name: /^保存$/ }).click();
    },
  );
  const delivery = unwrap(response.json);
  deliveryId = delivery.id;
  deliveryNo = delivery.delivery_no;
  if (!deliveryId || !deliveryNo) throw new Error("Delivery creation response missing id/delivery_no");
  report.created.deliveryOrders.push(deliveryId);

  await page.waitForURL((url) => new URL(url).pathname === "/pmc/delivery-orders", { timeout: 15000 }).catch(() => {});
  await waitQuiet(page);
  await page.getByText("交付计划").first().click();
  await page.getByText(deliveryNo).first().waitFor({ state: "visible", timeout: 15000 });
  await saveScreenshot(page, "delivery-created-from-project-plan");
  return { deliveryId, deliveryNo };
};

const editDeliveryViaUi = async (page) => {
  await gotoRoute(page, `/pmc/delivery-orders?project_id=${projectId}`, 1000);
  await page.getByText("交付计划").first().click();
  const row = page.locator("tr").filter({ hasText: deliveryNo }).first();
  await row.waitFor({ state: "visible", timeout: 10000 });
  await row.locator('button[title="编辑发货计划"]').click();
  await page.getByText("编辑发货计划").first().waitFor({ state: "visible", timeout: 10000 });
  await page.getByPlaceholder("物流公司名称").fill("QA Logistics Updated");
  await page.getByPlaceholder("备注信息").fill(`${runPrefix} UI编辑发货计划`);

  await waitForApi(
    page,
    "PUT",
    `/api/v1/business-support-orders/delivery-orders/${deliveryId}`,
    async () => {
      await page.getByRole("button", { name: /^保存$/ }).click();
    },
  );
  await waitQuiet(page);
  await page.getByText("交付计划").first().click();
  await page.getByText(deliveryNo).first().waitFor({ state: "visible", timeout: 10000 });
  await saveScreenshot(page, "delivery-edited");
  return { deliveryId };
};

const verifyDetailAndWorkflowViaUi = async (page) => {
  await gotoRoute(page, `/pmc/delivery-orders/${deliveryId}`, 1000);
  await page.getByText(`发货计划详情 - ${deliveryNo}`).waitFor({ state: "visible", timeout: 10000 });
  await page.getByText("待审批").first().waitFor({ state: "visible", timeout: 10000 });

  await waitForApi(
    page,
    "POST",
    `/api/v1/business-support-orders/delivery-orders/${deliveryId}/approve`,
    async () => {
      await page.getByRole("button", { name: /审批通过/ }).click();
    },
  );
  await page.getByRole("button", { name: /打印送货单/ }).waitFor({ state: "visible", timeout: 10000 });

  await waitForApi(
    page,
    "POST",
    `/api/v1/business-support-orders/delivery-orders/${deliveryId}/print`,
    async () => {
      await page.getByRole("button", { name: /打印送货单/ }).click();
    },
  );
  await page.getByRole("button", { name: /确认发货/ }).waitFor({ state: "visible", timeout: 10000 });

  await waitForApi(
    page,
    "POST",
    `/api/v1/business-support-orders/delivery-orders/${deliveryId}/ship`,
    async () => {
      await page.getByRole("button", { name: /确认发货/ }).click();
    },
  );
  await page.getByRole("button", { name: /确认签收/ }).waitFor({ state: "visible", timeout: 10000 });
  await saveScreenshot(page, "delivery-shipped-detail");
  return { deliveryId };
};

const verifyTrackingRoute = async (page) => {
  await gotoRoute(page, "/pmc/delivery-orders?status=in_transit", 1000);
  await page.getByText("物流跟踪").first().waitFor({ state: "visible", timeout: 10000 });
  await page.getByText(deliveryNo).first().waitFor({ state: "visible", timeout: 10000 });
  await page.getByText(trackingNo).first().waitFor({ state: "visible", timeout: 10000 });
  await assertNoPageCrashed(page);
  await saveScreenshot(page, "delivery-tracking-route");
  return { route: "/pmc/delivery-orders?status=in_transit" };
};

const receiveDeliveryViaUi = async (page) => {
  await gotoRoute(page, `/pmc/delivery-orders/${deliveryId}`, 1000);
  await page.getByRole("button", { name: /确认签收/ }).waitFor({ state: "visible", timeout: 10000 });
  await waitForApi(
    page,
    "POST",
    `/api/v1/business-support-orders/delivery-orders/${deliveryId}/receive`,
    async () => {
      await page.getByRole("button", { name: /确认签收/ }).click();
    },
  );
  await page.getByText("已签收").first().waitFor({ state: "visible", timeout: 10000 });
  await saveScreenshot(page, "delivery-received-detail");
  return { deliveryId };
};

const verifyDeliveryApiState = async (page) => {
  const delivery = unwrap(await browserApi(page, "GET", `/business-support-orders/delivery-orders/${deliveryId}`));
  if (delivery.approval_status !== "approved") {
    throw new Error(`Delivery approval expected approved, got ${delivery.approval_status}`);
  }
  if (delivery.delivery_status !== "received") {
    throw new Error(`Delivery status expected received, got ${delivery.delivery_status}`);
  }
  if (delivery.logistics_company !== "QA Logistics Updated") {
    throw new Error(`Delivery edit did not persist logistics company: ${delivery.logistics_company}`);
  }
  if (delivery.project_id !== projectId) {
    throw new Error(`Delivery project_id mismatch: ${delivery.project_id} !== ${projectId}`);
  }
  if (delivery.delivery_date !== deliveryDate) {
    throw new Error(`Planned delivery date mismatch: ${delivery.delivery_date} !== ${deliveryDate}`);
  }
  if (!delivery.ship_date) {
    throw new Error("Actual ship_date was not set after confirming shipment");
  }
  return {
    projectId: delivery.project_id,
    plannedDeliveryDate: delivery.delivery_date,
    approvalStatus: delivery.approval_status,
    deliveryStatus: delivery.delivery_status,
    shipDate: delivery.ship_date,
    receiveDate: delivery.receive_date,
  };
};

const verifyMenuRoutes = async (page) => {
  const routes = [
    { route: "/pmc/delivery-plan", text: "交付计划" },
    { route: "/pmc/delivery-orders?status=pending", text: "交付概览" },
    { route: "/pmc/delivery-orders?status=in_transit", text: "物流跟踪" },
  ];
  const visited = [];
  for (const item of routes) {
    await gotoRoute(page, item.route, 800);
    await page.getByText(item.text).first().waitFor({ state: "visible", timeout: 10000 });
    await assertNoPageCrashed(page);
    visited.push(item.route);
  }
  return { visited };
};

const verifyExportButton = async (page) => {
  await gotoRoute(page, "/pmc/delivery-orders", 1000);
  const downloadPromise = page.waitForEvent("download", { timeout: 10000 });
  await page.getByRole("button", { name: /导出报表/ }).click();
  const download = await downloadPromise;
  const suggestedFilename = download.suggestedFilename();
  if (!/发货报表_.*\.csv/.test(suggestedFilename)) {
    throw new Error(`Unexpected export filename: ${suggestedFilename}`);
  }
  await saveScreenshot(page, "delivery-export-clicked");
  return { suggestedFilename };
};

const verifyCleanup = () => {
  cleanupCreated();
  const residualSql = `
    SELECT
      (SELECT COUNT(*) FROM delivery_orders WHERE id IN (${idList(report.created.deliveryOrders)})) AS delivery_count,
      (SELECT COUNT(*) FROM sales_orders WHERE id IN (${idList(report.created.salesOrders)})) AS sales_order_count,
      (SELECT COUNT(*) FROM sales_order_items WHERE sales_order_id IN (${idList(report.created.salesOrders)})) AS sales_order_item_count,
      (SELECT COUNT(*) FROM projects WHERE id IN (${idList(report.created.projects)})) AS project_count,
      (SELECT COUNT(*) FROM customers WHERE customer_code LIKE '${runPrefix}%') AS customer_count;
  `;
  const output = dbExec(residualSql);
  const counts = output.split("|").map((value) => Number(value || 0));
  const residual = {
    deliveryOrders: counts[0] || 0,
    salesOrders: counts[1] || 0,
    salesOrderItems: counts[2] || 0,
    projects: counts[3] || 0,
    customers: counts[4] || 0,
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
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, acceptDownloads: true });
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
    await runStep(page, "create support project and sales order via API", async () => createSupportProjectAndSalesOrder(page));
    await runStep(page, "verify global list has no standalone create", async () => verifyNoStandaloneCreateOnGlobalList(page));
    await runStep(page, "create delivery plan from project via UI", async () => createDeliveryViaProjectUi(page));
    await runStep(page, "edit delivery order via UI", async () => editDeliveryViaUi(page));
    await runStep(page, "approve print and ship delivery via UI", async () => verifyDetailAndWorkflowViaUi(page));
    await runStep(page, "verify in-transit tracking route", async () => verifyTrackingRoute(page));
    await runStep(page, "receive delivery via UI", async () => receiveDeliveryViaUi(page));
    await runStep(page, "verify delivery API state", async () => verifyDeliveryApiState(page));
    await runStep(page, "verify delivery menu routes", async () => verifyMenuRoutes(page));
    await runStep(page, "verify export report button", async () => verifyExportButton(page));
    await runStep(page, "cleanup and verify residuals", () => verifyCleanup());
  } finally {
    await browser.close();
  }

  const failed = report.steps.filter((step) => step.status !== "passed");
  const evidenceFile = writeReport();
  console.log(`[report] ${evidenceFile}`);
  if (failed.length > 0) {
    throw new Error(`Delivery QA failed ${failed.length} step(s): ${failed.map((step) => step.name).join(", ")}`);
  }
  if (report.pageErrors.length || report.requestFailures.length || report.apiErrors.length) {
    throw new Error(
      `Delivery QA collected browser/API errors: page=${report.pageErrors.length}, request=${report.requestFailures.length}, api=${report.apiErrors.length}`,
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
