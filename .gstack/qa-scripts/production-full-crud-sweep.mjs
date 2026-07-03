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
const runPrefix = `QA_PROD_${stamp}`;
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
    workshops: [],
    workers: [],
    productionPlans: [],
    workOrders: [],
    workReports: [],
    productionExceptions: [],
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
  const file = path.join(reportDir, `production-full-crud-sweep-${stamp}.json`);
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
  const file = path.join(screenshotDir, `production-full-${safe}-${stamp}.png`);
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

const rowByText = (page, text) => page.locator("tr").filter({ hasText: text }).first();

const escapeRegExp = (value) => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

const selectRadixByPlaceholder = async (page, scope, placeholder, optionName) => {
  let trigger = scope.getByRole("combobox").filter({ hasText: placeholder }).first();
  if ((await trigger.count()) === 0) {
    trigger = scope.getByText(placeholder).first();
  }
  await trigger.waitFor({ state: "visible", timeout: 10000 });
  await trigger.click();
  await page.getByRole("option", { name: new RegExp(escapeRegExp(optionName)) }).first().click();
};

const clickConfirmDialog = async (page) => {
  const dialog = page.getByRole("dialog", { name: /请确认|确认/ }).last();
  await dialog.waitFor({ state: "visible", timeout: 10000 });
  await dialog.getByRole("button", { name: /^确认$/ }).click();
};

const sql = (statement) => {
  if (!fs.existsSync(DB_PATH)) return "";
  return execFileSync("sqlite3", [DB_PATH, statement], { encoding: "utf8" }).trim();
};

const idsOf = (items) => items.map((item) => item.id).filter(Boolean);
const idList = (ids) => (ids.length ? ids.join(",") : "NULL");

const fkReferences = (targetTable) => {
  const query = `
    SELECT m.name || '|' || p."from"
    FROM sqlite_master AS m, pragma_foreign_key_list(m.name) AS p
    WHERE m.type = 'table' AND p."table" = '${targetTable}';
  `;
  const output = sql(query);
  if (!output) return [];
  return output
    .split("\n")
    .filter(Boolean)
    .map((line) => {
      const [table, column] = line.split("|");
      return { table, column };
    });
};

const cleanupCreated = () => {
  const projectIds = idsOf(report.created.projects);
  const workshopIds = idsOf(report.created.workshops);
  const workerIds = idsOf(report.created.workers);
  const planIds = idsOf(report.created.productionPlans);
  const orderIds = idsOf(report.created.workOrders);
  const reportIds = idsOf(report.created.workReports);
  const exceptionIds = idsOf(report.created.productionExceptions);
  const statements = ["PRAGMA foreign_keys=OFF;"];

  if (reportIds.length || orderIds.length || workerIds.length) {
    statements.push(
      `DELETE FROM work_report WHERE id IN (${idList(reportIds)}) OR work_order_id IN (${idList(orderIds)}) OR worker_id IN (${idList(workerIds)});`,
    );
  }
  if (exceptionIds.length || orderIds.length || projectIds.length || workshopIds.length) {
    statements.push(
      `DELETE FROM production_exception WHERE id IN (${idList(exceptionIds)}) OR work_order_id IN (${idList(orderIds)}) OR project_id IN (${idList(projectIds)}) OR workshop_id IN (${idList(workshopIds)});`,
    );
  }
  if (orderIds.length) {
    const orderList = orderIds.join(",");
    for (const { table, column } of fkReferences("work_order")) {
      if (table === "work_order" || table === "work_report" || table === "production_exception") continue;
      statements.push(`DELETE FROM "${table}" WHERE "${column}" IN (${orderList});`);
    }
    statements.push(`DELETE FROM work_order WHERE id IN (${orderList});`);
  }
  if (planIds.length) {
    statements.push(`DELETE FROM production_plan WHERE id IN (${planIds.join(",")});`);
  }
  if (workerIds.length) {
    const workerList = workerIds.join(",");
    for (const { table, column } of fkReferences("worker")) {
      if (["worker", "work_order", "work_report"].includes(table)) continue;
      statements.push(`DELETE FROM "${table}" WHERE "${column}" IN (${workerList});`);
    }
    statements.push(`DELETE FROM worker WHERE id IN (${workerList});`);
  }
  if (workshopIds.length) {
    const workshopList = workshopIds.join(",");
    for (const { table, column } of fkReferences("workshop")) {
      if (["workshop", "worker", "work_order", "production_plan", "production_exception"].includes(table)) continue;
      statements.push(`DELETE FROM "${table}" WHERE "${column}" IN (${workshopList});`);
    }
    statements.push(`DELETE FROM workshop WHERE id IN (${workshopList});`);
  }
  if (projectIds.length) {
    const projectList = projectIds.join(",");
    for (const { table, column } of fkReferences("projects")) {
      if (["projects", "work_order", "production_plan", "production_exception"].includes(table)) continue;
      statements.push(`DELETE FROM "${table}" WHERE "${column}" IN (${projectList});`);
    }
    statements.push(`DELETE FROM projects WHERE id IN (${projectList});`);
  }
  statements.push("PRAGMA foreign_keys=ON;");

  const output = sql(statements.join("\n"));
  report.cleanup.push({ sql: statements.join("\n"), output, at: new Date().toISOString() });
  writeReport();
};

const verifyCleanup = () => {
  cleanupCreated();
  const output = sql(`
    SELECT
      (SELECT COUNT(*) FROM projects WHERE project_code LIKE '${runPrefix}%'),
      (SELECT COUNT(*) FROM workshop WHERE workshop_code LIKE '${runPrefix}%'),
      (SELECT COUNT(*) FROM worker WHERE worker_no LIKE '${runPrefix}%'),
      (SELECT COUNT(*) FROM production_plan WHERE id IN (${idList(idsOf(report.created.productionPlans))})),
      (SELECT COUNT(*) FROM work_order WHERE id IN (${idList(idsOf(report.created.workOrders))})),
      (SELECT COUNT(*) FROM work_report WHERE id IN (${idList(idsOf(report.created.workReports))})),
      (SELECT COUNT(*) FROM production_exception WHERE id IN (${idList(idsOf(report.created.productionExceptions))}));
  `);
  const counts = output.split("|").map((value) => Number(value || 0));
  const residual = {
    projects: counts[0] || 0,
    workshops: counts[1] || 0,
    workers: counts[2] || 0,
    productionPlans: counts[3] || 0,
    workOrders: counts[4] || 0,
    workReports: counts[5] || 0,
    productionExceptions: counts[6] || 0,
  };
  report.cleanup.push({ residual, at: new Date().toISOString() });
  writeReport();
  if (Object.values(residual).some((count) => count !== 0)) {
    throw new Error(`Cleanup residuals remain: ${JSON.stringify(residual)}`);
  }
  return residual;
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

let projectId;
let projectName;
let workshopId;
let workshopName;
let workerId;
let workerName;
let planId;
let planName;
let workOrderId;
let workOrderNo;
const createdReportIds = [];
let exceptionId;
let exceptionTitle;

const createSupportProjectViaApi = async (page) => {
  projectName = `${runPrefix}_生产载体项目`;
  const project = unwrap(
    await browserApi(page, "POST", "/projects/", {
      project_code: `${runPrefix}_PRJ`.slice(0, 48),
      project_name: projectName,
      short_name: `${runPrefix.slice(-8)}生产`,
      project_type: "CUSTOM",
      contract_no: `${runPrefix}_CONTRACT`.slice(0, 80),
      contract_date: "2026-07-01",
      planned_start_date: "2026-07-02",
      planned_end_date: "2026-09-18",
      contract_amount: 360000,
      budget_amount: 250000,
      description: `${runPrefix} 生产管理模块真实浏览器验收载体项目`,
    }),
  );
  if (!project.id) {
    throw new Error(`项目创建未返回 id: ${JSON.stringify(project).slice(0, 400)}`);
  }
  projectId = project.id;
  report.created.projects.push({
    id: project.id,
    project_code: project.project_code,
    project_name: project.project_name,
  });
  return { projectId, projectName };
};

const createAndEditWorkshopViaUi = async (page) => {
  workshopName = `${runPrefix}_装配车间`;
  await gotoRoute(page, "/workshops", 1000);
  await page.getByText("车间管理").first().waitFor({ state: "visible", timeout: 10000 });
  await page.getByRole("button", { name: /新建车间/ }).click();
  const dialog = page.getByRole("dialog", { name: /新建车间/ });
  await dialog.waitFor({ state: "visible", timeout: 10000 });
  await dialog.getByPlaceholder("请输入车间编码").fill(`${runPrefix}_WS`);
  await dialog.getByPlaceholder("请输入车间名称").fill(workshopName);
  await dialog.getByPlaceholder("车间位置").fill("QA生产车间A区");
  await dialog.locator('input[type="number"]').fill("128");
  await dialog.locator("textarea").fill(`${runPrefix} 生产QA车间`);

  const response = await waitForApi(page, "POST", "/api/v1/production/workshops", async () => {
    await dialog.getByRole("button", { name: /^创建$/ }).click();
  });
  const workshop = unwrap(response.json);
  workshopId = workshop.id;
  if (!workshopId) throw new Error("Workshop creation response missing id");
  report.created.workshops.push({ id: workshopId, workshop_code: workshop.workshop_code, workshop_name: workshopName });
  await page.getByText(workshopName).first().waitFor({ state: "visible", timeout: 15000 });

  const row = rowByText(page, workshopName);
  await row.locator("button").nth(1).click();
  const editDialog = page.getByRole("dialog", { name: /编辑车间/ });
  await editDialog.waitFor({ state: "visible", timeout: 10000 });
  await editDialog.getByPlaceholder("车间位置").fill("QA生产车间B区");
  await waitForApi(page, "PUT", `/api/v1/production/workshops/${workshopId}`, async () => {
    await editDialog.getByRole("button", { name: /^保存$/ }).click();
  });
  await saveScreenshot(page, "workshop-created-edited");
  return { workshopId, workshopName };
};

const createAndEditWorkerViaUi = async (page) => {
  workerName = `${runPrefix}_工人`;
  await gotoRoute(page, "/workers", 1000);
  await page.getByText("工人管理").first().waitFor({ state: "visible", timeout: 10000 });
  await page.getByRole("button", { name: /新建工人/ }).click();
  const dialog = page.getByRole("dialog", { name: /新建工人/ });
  await dialog.waitFor({ state: "visible", timeout: 10000 });
  await dialog.getByPlaceholder("请输入工人编码").fill(`${runPrefix}_WK`);
  await dialog.getByPlaceholder("请输入姓名").fill(workerName);
  await dialog.getByPlaceholder("联系电话").fill("13900000000");
  await dialog.getByPlaceholder("邮箱地址").fill("qa-production@example.com");
  await dialog.locator('input[type="date"]').fill("2026-07-01");

  const response = await waitForApi(page, "POST", "/api/v1/production/workers", async () => {
    await dialog.getByRole("button", { name: /^创建$/ }).click();
  });
  const worker = unwrap(response.json);
  workerId = worker.id;
  if (!workerId) throw new Error("Worker creation response missing id");
  report.created.workers.push({ id: workerId, worker_code: worker.worker_code, worker_name: workerName });
  await page.getByText(workerName).first().waitFor({ state: "visible", timeout: 15000 });

  const row = rowByText(page, workerName);
  await row.locator("button").nth(1).click();
  const editDialog = page.getByRole("dialog", { name: /编辑工人/ });
  await editDialog.waitFor({ state: "visible", timeout: 10000 });
  await editDialog.getByPlaceholder("联系电话").fill("13900000001");
  await waitForApi(page, "PUT", `/api/v1/production/workers/${workerId}`, async () => {
    await editDialog.getByRole("button", { name: /^保存$/ }).click();
  });
  await saveScreenshot(page, "worker-created-edited");
  return { workerId, workerName };
};

const createAndApproveProductionPlanViaUi = async (page) => {
  planName = `${runPrefix}_生产计划`;
  await gotoRoute(page, "/production-plans", 1000);
  await page.getByText("生产计划管理").first().waitFor({ state: "visible", timeout: 10000 });
  await page.getByRole("button", { name: /新建计划/ }).click();
  const dialog = page.getByRole("dialog", { name: /新建生产计划/ });
  await dialog.waitFor({ state: "visible", timeout: 10000 });
  await dialog.getByPlaceholder("请输入计划名称").fill(planName);
  await selectRadixByPlaceholder(page, dialog, "选择项目", projectName);
  const dateInputs = dialog.locator('input[type="date"]');
  await dateInputs.nth(0).fill("2026-07-06");
  await dateInputs.nth(1).fill("2026-07-20");
  await dialog.locator("textarea").fill(`${runPrefix} 生产计划描述`);

  const response = await waitForApi(page, "POST", "/api/v1/production/production-plans", async () => {
    await dialog.getByRole("button", { name: /^创建$/ }).click();
  });
  const plan = unwrap(response.json);
  planId = plan.id;
  if (!planId) throw new Error("Production plan creation response missing id");
  report.created.productionPlans.push({ id: planId, plan_no: plan.plan_no, plan_name: planName });
  await page.getByText(planName).first().waitFor({ state: "visible", timeout: 15000 });

  await waitForApi(page, "PUT", `/api/v1/production/production-plans/${planId}/submit`, async () => {
    await rowByText(page, planName).locator('button[title="提交审批"]').click();
    await clickConfirmDialog(page);
  });
  let detail = unwrap(await browserApi(page, "GET", `/production/production-plans/${planId}`));
  if (detail.status !== "SUBMITTED") throw new Error(`Plan expected SUBMITTED, got ${detail.status}`);

  await page.getByText(planName).first().waitFor({ state: "visible", timeout: 10000 });
  await rowByText(page, planName).locator('button[title="审批驳回"]').waitFor({ state: "visible", timeout: 10000 });
  await waitForApi(page, "PUT", `/api/v1/production/production-plans/${planId}/approve`, async () => {
    await rowByText(page, planName).locator('button[title="审批通过"]').click();
    await clickConfirmDialog(page);
  });
  detail = unwrap(await browserApi(page, "GET", `/production/production-plans/${planId}`));
  if (detail.status !== "APPROVED") throw new Error(`Plan expected APPROVED, got ${detail.status}`);

  await waitForApi(page, "PUT", `/api/v1/production/production-plans/${planId}/publish`, async () => {
    await rowByText(page, planName).locator('button[title="发布计划"]').click();
    await clickConfirmDialog(page);
  });
  detail = unwrap(await browserApi(page, "GET", `/production/production-plans/${planId}`));
  if (detail.status !== "PUBLISHED") throw new Error(`Plan expected PUBLISHED, got ${detail.status}`);
  await saveScreenshot(page, "production-plan-published");
  return { planId, status: detail.status };
};

const createAndAssignWorkOrderViaUi = async (page) => {
  const taskName = `${runPrefix}_装配工单`;
  await gotoRoute(page, "/work-orders", 1000);
  await page.getByText("工单管理").first().waitFor({ state: "visible", timeout: 10000 });
  await page.getByRole("button", { name: /新建工单/ }).click();
  const dialog = page.getByRole("dialog", { name: /新建工单/ });
  await dialog.waitFor({ state: "visible", timeout: 10000 });
  await dialog.getByPlaceholder("请输入任务名称").fill(taskName);
  await selectRadixByPlaceholder(page, dialog, "选择项目", projectName);
  await dialog.getByPlaceholder("物料名称").fill(`${runPrefix}_治具组件`);
  await dialog.getByPlaceholder("规格").fill("QA-PROD-SPEC");
  const numberInputs = dialog.locator('input[type="number"]');
  await numberInputs.nth(0).fill("5");
  await numberInputs.nth(1).fill("6");
  const dateInputs = dialog.locator('input[type="date"]');
  await dateInputs.nth(0).fill("2026-07-07");
  await dateInputs.nth(1).fill("2026-07-12");
  await dialog.getByPlaceholder("工作内容描述...").fill(`${runPrefix} 真实浏览器装配工单`);

  const response = await waitForApi(page, "POST", "/api/v1/production/work-orders", async () => {
    await dialog.getByRole("button", { name: /^创建$/ }).click();
  });
  const order = unwrap(response.json);
  workOrderId = order.id;
  workOrderNo = order.work_order_no;
  if (!workOrderId || !workOrderNo) throw new Error("Work order creation response missing id/no");
  report.created.workOrders.push({ id: workOrderId, work_order_no: workOrderNo, task_name: taskName });
  await page.getByText(taskName).first().waitFor({ state: "visible", timeout: 15000 });

  const row = rowByText(page, taskName);
  await row.locator("button").nth(1).click();
  const assignDialog = page.getByRole("dialog", { name: /派工/ });
  await assignDialog.waitFor({ state: "visible", timeout: 10000 });
  await assignDialog.getByPlaceholder("人员ID").fill(String(workerId));
  await waitForApi(page, "PUT", `/api/v1/production/work-orders/${workOrderId}/assign`, async () => {
    await assignDialog.getByRole("button", { name: /确认派工/ }).click();
  });
  const assigned = unwrap(await browserApi(page, "GET", `/production/work-orders/${workOrderId}`));
  if (assigned.status !== "ASSIGNED" || assigned.assigned_to !== workerId) {
    throw new Error(`Work order assign failed: ${JSON.stringify({ status: assigned.status, assigned_to: assigned.assigned_to })}`);
  }
  await saveScreenshot(page, "work-order-assigned");
  return { workOrderId, workOrderNo, status: assigned.status };
};

const pushWorkReport = (reportPayload) => {
  const workReport = unwrap(reportPayload);
  if (workReport.id) {
    createdReportIds.push(workReport.id);
    report.created.workReports.push({ id: workReport.id, report_no: workReport.report_no, report_type: workReport.report_type });
  }
  return workReport;
};

const runMobileWorkReportsViaUi = async (page) => {
  await gotoRoute(page, `/mobile/scan-start?workOrderId=${workOrderId}`, 1000);
  await page.getByText("工单信息").first().waitFor({ state: "visible", timeout: 10000 });
  const startResponse = await waitForApi(page, "POST", "/api/v1/production/work-reports/start", async () => {
    await page.getByRole("button", { name: /确认开工/ }).click();
  });
  pushWorkReport(startResponse.json);
  let order = unwrap(await browserApi(page, "GET", `/production/work-orders/${workOrderId}`));
  if (order.status !== "STARTED") throw new Error(`Work order expected STARTED, got ${order.status}`);

  await gotoRoute(page, `/mobile/progress-report?workOrderId=${workOrderId}`, 1000);
  await page.getByText("进度上报").first().waitFor({ state: "visible", timeout: 10000 });
  await page.getByRole("button", { name: /^50%$/ }).click();
  const progressInputs = page.locator('input[type="number"]');
  await progressInputs.nth(1).fill("1.5");
  await page.getByPlaceholder("填写进度说明...").fill(`${runPrefix} 进度上报`);
  const progressResponse = await waitForApi(page, "POST", "/api/v1/production/work-reports/progress", async () => {
    await page.getByRole("button", { name: /提交进度/ }).click();
  });
  pushWorkReport(progressResponse.json);

  await gotoRoute(page, `/mobile/complete-report?workOrderId=${workOrderId}`, 1000);
  await page.getByText("完工报工").first().waitFor({ state: "visible", timeout: 10000 });
  await page.getByRole("button", { name: /全部完成/ }).click();
  const completeInputs = page.locator('input[type="number"]');
  await completeInputs.nth(2).fill("2");
  await page.getByPlaceholder("填写完工说明...").fill(`${runPrefix} 完工报工`);
  const completeResponse = await waitForApi(page, "POST", "/api/v1/production/work-reports/complete", async () => {
    await page.getByRole("button", { name: /确认完工/ }).click();
  });
  pushWorkReport(completeResponse.json);

  order = unwrap(await browserApi(page, "GET", `/production/work-orders/${workOrderId}`));
  if (order.status !== "COMPLETED" || Number(order.completed_qty) !== 5) {
    throw new Error(`Work order expected COMPLETED qty=5, got ${order.status}/${order.completed_qty}`);
  }
  await saveScreenshot(page, "mobile-work-reports-completed");
  return { status: order.status, reportIds: createdReportIds };
};

const approveWorkReportsViaUi = async (page) => {
  await gotoRoute(page, "/work-reports", 1000);
  await page.getByText("报工管理").first().waitFor({ state: "visible", timeout: 10000 });
  const approved = [];
  for (const reportId of createdReportIds) {
    const detail = unwrap(await browserApi(page, "GET", `/production/work-reports/${reportId}`));
    await page.getByText(detail.report_no).first().waitFor({ state: "visible", timeout: 15000 });
    const row = rowByText(page, detail.report_no);
    const buttons = row.locator("button");
    const count = await buttons.count();
    if (count < 2) throw new Error(`Report ${detail.report_no} has no approve button`);
    await waitForApi(page, "PUT", `/api/v1/production/work-reports/${reportId}/approve`, async () => {
      await buttons.nth(count - 1).click();
      await clickConfirmDialog(page);
    });
    const after = unwrap(await browserApi(page, "GET", `/production/work-reports/${reportId}`));
    if (after.status !== "APPROVED") {
      throw new Error(`Report ${after.report_no} expected APPROVED, got ${after.status}`);
    }
    approved.push(after.report_no);
  }
  await saveScreenshot(page, "work-reports-approved");
  return { approved };
};

const createHandleCloseExceptionViaUi = async (page) => {
  exceptionTitle = `${runPrefix}_生产异常`;
  await gotoRoute(page, "/production-exceptions", 1000);
  await page.getByText("生产异常管理").first().waitFor({ state: "visible", timeout: 10000 });
  await page.getByRole("button", { name: /上报异常/ }).click();
  const dialog = page.getByRole("dialog", { name: /上报生产异常/ });
  await dialog.waitFor({ state: "visible", timeout: 10000 });
  await dialog.getByPlaceholder("请输入异常标题").fill(exceptionTitle);
  await selectRadixByPlaceholder(page, dialog, "选择项目", projectName);
  await dialog.getByPlaceholder("详细描述异常情况...").fill(`${runPrefix} 生产异常描述`);
  const numbers = dialog.locator('input[type="number"]');
  await numbers.nth(0).fill("2");
  await numbers.nth(1).fill("180");
  const createResponse = await waitForApi(page, "POST", "/api/v1/production/exceptions", async () => {
    await dialog.getByRole("button", { name: /^上报$/ }).click();
  });
  const exception = unwrap(createResponse.json);
  exceptionId = exception.id;
  if (!exceptionId) throw new Error("Production exception creation response missing id");
  report.created.productionExceptions.push({ id: exceptionId, exception_no: exception.exception_no, title: exceptionTitle });
  await page.getByText(exceptionTitle).first().waitFor({ state: "visible", timeout: 15000 });

  let row = rowByText(page, exceptionTitle);
  await row.locator("button").nth(1).click();
  const handleDialog = page.getByRole("dialog", { name: /处理生产异常/ });
  await handleDialog.waitFor({ state: "visible", timeout: 10000 });
  await handleDialog.getByPlaceholder("填写处理方案...").fill(`${runPrefix} 处理方案`);
  await handleDialog.getByPlaceholder("填写处理结果...").fill(`${runPrefix} 已复盘并处理`);
  await waitForApi(page, "PUT", `/api/v1/production/exceptions/${exceptionId}/handle`, async () => {
    await handleDialog.getByRole("button", { name: /^保存$/ }).click();
  });
  let detail = unwrap(await browserApi(page, "GET", `/production/exceptions/${exceptionId}`));
  if (detail.status !== "RESOLVED") throw new Error(`Exception expected RESOLVED, got ${detail.status}`);

  await page.getByText(exceptionTitle).first().waitFor({ state: "visible", timeout: 10000 });
  row = rowByText(page, exceptionTitle);
  await waitForApi(page, "PUT", `/api/v1/production/exceptions/${exceptionId}/close`, async () => {
    await row.locator("button").last().click();
    await clickConfirmDialog(page);
  });
  detail = unwrap(await browserApi(page, "GET", `/production/exceptions/${exceptionId}`));
  if (detail.status !== "CLOSED") throw new Error(`Exception expected CLOSED, got ${detail.status}`);
  await saveScreenshot(page, "production-exception-closed");
  return { exceptionId, status: detail.status };
};

const verifyReadOnlyProductionRoutes = async (page) => {
  const routes = [
    "/production/execution-center",
    `/workshops/${workshopId}/task-board`,
    `/work-orders/${workOrderId}`,
    "/production-board",
    "/production/capacity-analysis",
    "/production-dashboard",
  ];
  const visited = [];
  for (const route of routes) {
    await gotoRoute(page, route, 1000);
    await assertNoPageCrashed(page);
    visited.push(route);
  }
  await saveScreenshot(page, "read-only-production-routes");
  return { visited };
};

const verifyApiState = async (page) => {
  const plan = unwrap(await browserApi(page, "GET", `/production/production-plans/${planId}`));
  const order = unwrap(await browserApi(page, "GET", `/production/work-orders/${workOrderId}`));
  const exception = unwrap(await browserApi(page, "GET", `/production/exceptions/${exceptionId}`));
  const reports = await Promise.all(
    createdReportIds.map((id) => browserApi(page, "GET", `/production/work-reports/${id}`).then(unwrap)),
  );
  if (plan.status !== "PUBLISHED") throw new Error(`Plan expected PUBLISHED, got ${plan.status}`);
  if (order.status !== "COMPLETED") throw new Error(`Order expected COMPLETED, got ${order.status}`);
  if (!reports.every((item) => item.status === "APPROVED")) {
    throw new Error(`All work reports expected APPROVED, got ${reports.map((item) => item.status).join(",")}`);
  }
  if (exception.status !== "CLOSED") throw new Error(`Exception expected CLOSED, got ${exception.status}`);
  return {
    planStatus: plan.status,
    orderStatus: order.status,
    reportStatuses: reports.map((item) => `${item.report_no}:${item.status}`),
    exceptionStatus: exception.status,
  };
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
    if (
      type === "error" ||
      /DialogContent requires a DialogDescription|Missing `Description`|Cannot read properties|ReferenceError|TypeError/.test(text)
    ) {
      report.console.push({ type, text, url: page.url(), at: new Date().toISOString() });
    }
  });
  page.on("pageerror", (error) => {
    report.pageErrors.push({ message: error.message, stack: error.stack, url: page.url(), at: new Date().toISOString() });
  });
  page.on("requestfailed", (request) => {
    if (isIgnorableExternalResourceFailure(request.url())) return;
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
    await runStep(page, "create support project via API", async () => createSupportProjectViaApi(page));
    await runStep(page, "create and edit workshop via UI", async () => createAndEditWorkshopViaUi(page));
    await runStep(page, "create and edit worker via UI", async () => createAndEditWorkerViaUi(page));
    await runStep(page, "create submit approve publish production plan via UI", async () => createAndApproveProductionPlanViaUi(page));
    await runStep(page, "create and assign work order via UI", async () => createAndAssignWorkOrderViaUi(page));
    await runStep(page, "mobile start progress complete reports via UI", async () => runMobileWorkReportsViaUi(page));
    await runStep(page, "approve work reports via UI", async () => approveWorkReportsViaUi(page));
    await runStep(page, "create handle close production exception via UI", async () => createHandleCloseExceptionViaUi(page));
    await runStep(page, "verify production API state", async () => verifyApiState(page));
    await runStep(page, "verify read-only production routes", async () => verifyReadOnlyProductionRoutes(page));
    await runStep(page, "cleanup and verify residuals", () => verifyCleanup());
  } finally {
    await browser.close();
  }

  const failed = report.steps.filter((step) => step.status !== "passed");
  const evidenceFile = writeReport();
  console.log(`[report] ${evidenceFile}`);
  if (failed.length > 0) {
    throw new Error(`Production QA failed ${failed.length} step(s): ${failed.map((step) => step.name).join(", ")}`);
  }
  if (report.pageErrors.length || report.requestFailures.length || report.apiErrors.length || report.console.length) {
    throw new Error(
      `Production QA collected browser/API errors: page=${report.pageErrors.length}, request=${report.requestFailures.length}, api=${report.apiErrors.length}, console=${report.console.length}`,
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
