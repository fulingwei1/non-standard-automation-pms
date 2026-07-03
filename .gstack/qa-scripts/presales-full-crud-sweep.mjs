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
const runPrefix = `QA_PRESALE_${stamp}`;
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
    tickets: [],
    solutions: [],
    tenders: [],
    technicalTemplates: [],
    solutionTemplates: [],
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
  const file = path.join(reportDir, `presales-full-crud-sweep-${stamp}.json`);
  fs.writeFileSync(file, JSON.stringify(report, null, 2));
  return file;
};

const normalizeText = (text) => String(text || "").replace(/\s+/g, " ").trim();

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
  if (Array.isArray(data)) {
    return data;
  }
  return data?.items || [];
};

const saveScreenshot = async (page, label) => {
  const safe = label.replace(/[^a-z0-9\u4e00-\u9fa5_-]+/gi, "_").slice(0, 100);
  const file = path.join(screenshotDir, `presales-full-${safe}-${stamp}.png`);
  await page.screenshot({ path: file, fullPage: true }).catch(() => {});
  report.screenshots.push(file);
  return file;
};

const waitQuiet = async (page, settleMs = 550) => {
  await page.waitForLoadState("networkidle", { timeout: 3000 }).catch(() => {});
  await page.waitForTimeout(settleMs);
};

const isLoginPage = async (page) => {
  if (new URL(page.url()).pathname === "/login") {
    return true;
  }
  const loginInput = page.locator('input[placeholder="请输入用户名"]').first();
  return (await loginInput.count()) > 0 && (await loginInput.isVisible().catch(() => false));
};

const ensureAuthenticated = async (page) => {
  await page.goto(`${ROOT}/login`, { waitUntil: "domcontentloaded", timeout: 20000 });
  await waitQuiet(page);
  if (!(await isLoginPage(page))) {
    return;
  }

  await page.locator('input[placeholder="请输入用户名"]').fill(USERNAME);
  await page.locator('input[placeholder="请输入密码"]').fill(PASSWORD);
  await page.getByRole("button", { name: /^登录$/ }).click({ timeout: 8000 });
  await page.waitForURL((url) => new URL(url).pathname !== "/login", { timeout: 20000 }).catch(() => {});
  await waitQuiet(page);

  if (await isLoginPage(page)) {
    throw new Error("UI login did not leave /login");
  }
};

const gotoRoute = async (page, route, settleMs = 700) => {
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
      return {
        ok: response.ok,
        status: response.status,
        json,
        text,
      };
    },
    { method, apiPath, body },
  );

  if (!result.ok) {
    throw new Error(`${method} ${apiPath} -> ${result.status}: ${result.text?.slice(0, 400)}`);
  }
  return result.json;
};

const waitForApi = async (page, method, pattern, action) => {
  const responsePromise = page.waitForResponse(
    (response) =>
      response.url().includes(pattern) &&
      response.request().method().toUpperCase() === method.toUpperCase(),
    { timeout: 20000 },
  ).then(
    (response) => ({ response }),
    (error) => ({ error }),
  );
  await action();
  const { response, error } = await responsePromise;
  if (error) {
    throw error;
  }
  const body = await response.text().catch(() => "");
  if (!response.ok()) {
    throw new Error(`${method} ${pattern} -> ${response.status()}: ${body.slice(0, 400)}`);
  }
  return { status: response.status(), body };
};

const findByKeyword = async (page, apiPath, keyword, pageSize = 100) => {
  const separator = apiPath.includes("?") ? "&" : "?";
  const payload = await browserApi(
    page,
    "GET",
    `${apiPath}${separator}page=1&page_size=${pageSize}&keyword=${encodeURIComponent(keyword)}`,
  );
  return listItems(payload).find((item) =>
    JSON.stringify(item).toLowerCase().includes(String(keyword).toLowerCase()),
  );
};

const runStep = async (page, name, fn) => {
  const step = {
    name,
    startedAt: new Date().toISOString(),
    status: "running",
  };
  report.steps.push(step);
  console.log(`[step] ${name}`);
  const before = {
    apiErrors: report.apiErrors.length,
    pageErrors: report.pageErrors.length,
    requestFailures: report.requestFailures.length,
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
    };
    writeReport();
  }
};

const createTicketViaUi = async (page, route, title, customerName, description, kind = "task") => {
  await gotoRoute(page, route);
  const buttonName = kind === "survey" ? /新建调研/ : /新建任务/;
  await page.getByRole("button", { name: buttonName }).first().click();
  const titleInput = kind === "survey"
    ? page.locator("#requirement-survey-title")
    : page.locator("#presale-task-title");
  await titleInput.fill(title);
  const customerInput = kind === "survey"
    ? page.locator("#requirement-survey-customer")
    : page.locator("#presale-task-customer");
  await customerInput.fill(customerName);
  const dateInput = kind === "survey"
    ? page.locator("#requirement-survey-expected-date")
    : page.locator("#presale-task-expected-date");
  await dateInput.fill("2026-07-08");
  const descInput = kind === "survey"
    ? page.locator("#requirement-survey-description")
    : page.locator("#presale-task-description");
  await descInput.fill(description);
  if (kind === "task") {
    await page.locator("#presale-task-type").selectOption("SOLUTION_DESIGN");
    await page.locator("#presale-task-urgency").selectOption("URGENT");
  }

  const response = await waitForApi(page, "POST", "/api/v1/presale/tickets", async () => {
    await page.getByRole("button", { name: kind === "survey" ? /^创建调研$/ : /^创建任务$/ }).click();
  });
  await waitQuiet(page, 900);
  const ticket = parseJson(response.body) || {};
  const ticketId = ticket.id || ticket?.data?.id;
  if (!ticketId) {
    throw new Error(`创建售前工单未返回 id: ${response.body?.slice(0, 400)}`);
  }
  const tracked = { id: ticketId, title, type: kind, deleted: false };
  report.created.tickets.push(tracked);
  return tracked;
};

const openTaskDetail = async (page, title) => {
  await gotoRoute(page, "/presales/technical-solutions?tab=reviews", 900);
  await page.getByPlaceholder("搜索任务...").fill(title);
  await waitQuiet(page, 500);
  await page.getByText(title, { exact: false }).first().click();
  const panel = page.locator("text=任务详情").locator("xpath=ancestor::*[contains(@class, 'fixed')][1]").last();
  await panel.waitFor({ state: "visible", timeout: 8000 });
  return panel;
};

const exerciseTicketLifecycleViaUi = async (page, ticket, title) => {
  let panel = await openTaskDetail(page, title);
  await waitForApi(page, "PUT", `/api/v1/presale/tickets/${ticket.id}/accept`, async () => {
    await panel.getByRole("button", { name: /接单处理/ }).click();
  });
  await waitQuiet(page, 900);

  panel = await openTaskDetail(page, title);
  await panel.locator("#presale-deliverable-name").fill(`${runPrefix}_方案交付物`);
  await panel.locator("#presale-deliverable-type").selectOption("SOLUTION");
  await panel.locator("#presale-deliverable-path").fill(`/tmp/${runPrefix}_solution.pdf`);
  const deliverableResponse = await waitForApi(
    page,
    "POST",
    `/api/v1/presale/tickets/${ticket.id}/deliverables`,
    async () => {
      await panel.getByRole("button", { name: /提交交付物/ }).click();
    },
  );
  await waitQuiet(page, 800);
  const deliverable = parseJson(deliverableResponse.body) || {};
  if (!deliverable.id && !deliverable?.data?.id) {
    throw new Error(`交付物创建未返回 id: ${deliverableResponse.body?.slice(0, 400)}`);
  }

  const approveButton = panel.getByRole("button", { name: /通过交付物/ }).first();
  await approveButton.waitFor({ state: "visible", timeout: 8000 });
  await waitForApi(
    page,
    "PUT",
    `/api/v1/presale/tickets/${ticket.id}/deliverables/`,
    async () => {
      await approveButton.click();
    },
  );
  await waitQuiet(page, 800);

  const progressInput = panel.locator('input[type="number"]').first();
  await progressInput.fill("65");
  await panel.getByPlaceholder("进度说明...").fill(`${runPrefix} 进度更新`);
  await waitForApi(page, "PUT", `/api/v1/presale/tickets/${ticket.id}/progress`, async () => {
    await panel.getByRole("button", { name: /更新进度/ }).click();
  });
  await waitQuiet(page, 800);

  await panel.locator("#presale-complete-hours").fill("6.5");
  await panel.locator("#presale-completion-note").fill(`${runPrefix} 工单完成说明`);
  await waitForApi(page, "PUT", `/api/v1/presale/tickets/${ticket.id}/complete`, async () => {
    await panel.getByRole("button", { name: /完成工单/ }).click();
  });
  await waitQuiet(page, 1000);

  panel = await openTaskDetail(page, title);
  await panel.locator("#presale-rating-score").selectOption("5");
  await panel.locator("#presale-rating-feedback").fill(`${runPrefix} 满意度评价`);
  await waitForApi(page, "PUT", `/api/v1/presale/tickets/${ticket.id}/rating`, async () => {
    await panel.getByRole("button", { name: /提交评价/ }).click();
  });
  await waitQuiet(page, 900);

  const updated = unwrap(await browserApi(page, "GET", `/presale/tickets/${ticket.id}`));
  if (updated.status !== "COMPLETED" || Number(updated.satisfaction_score) !== 5) {
    throw new Error(`工单闭环状态异常: status=${updated.status}, score=${updated.satisfaction_score}`);
  }
  return {
    id: ticket.id,
    status: updated.status,
    satisfaction_score: updated.satisfaction_score,
    deliverables: updated.deliverables?.length || 0,
  };
};

const exerciseSolutionViaUi = async (page, solutionName) => {
  await gotoRoute(page, "/presales/technical-solutions?tab=solutions", 900);
  await page.getByRole("button", { name: /新建方案/ }).first().click();
  await waitQuiet(page, 400);
  await page.locator('input[placeholder="例如：新能源PACK线FCT测试方案"]').fill(solutionName);
  await page
    .locator('textarea[placeholder^="填写产线痛点"]')
    .fill(`${runPrefix} 需求：FCT 自动化测试线，1 秒节拍，MES 数据追溯，支持快速换型。`);
  const numberInputs = page.locator('input[type="number"]');
  await numberInputs.nth(0).fill("180000");
  await numberInputs.nth(1).fill("260000");
  await numberInputs.nth(2).fill("120");
  await numberInputs.nth(3).fill("35");

  const response = await waitForApi(page, "POST", "/api/v1/presale/proposals/solutions", async () => {
    await page.getByRole("button", { name: /生成并保存方案/ }).click();
  });
  await waitQuiet(page, 1200);
  const solution = parseJson(response.body) || {};
  const solutionId = solution.id || solution?.data?.id;
  if (!solutionId) {
    throw new Error(`方案创建未返回 id: ${response.body?.slice(0, 400)}`);
  }
  const tracked = { id: solutionId, name: solutionName, deleted: false };
  report.created.solutions.push(tracked);

  await page.locator("button").filter({ hasText: /^方案列表$/ }).first().click();
  await waitQuiet(page, 900);
  await page.getByPlaceholder("搜索方案名称 / 编号").fill(solutionName);
  await waitQuiet(page, 600);
  const submitButton = page.getByRole("button", { name: /提交评审/ }).first();
  await submitButton.waitFor({ state: "visible", timeout: 10000 });
  await waitForApi(
    page,
    "PUT",
    `/api/v1/presale/proposals/solutions/${solutionId}/review`,
    async () => {
      await submitButton.click();
    },
  );
  await waitQuiet(page, 900);

  const updated = unwrap(await browserApi(page, "GET", `/presale/proposals/solutions/${solutionId}`));
  if (updated.status !== "REVIEW" || updated.review_status !== "REVIEW") {
    throw new Error(`方案提交评审后状态异常: status=${updated.status}, review=${updated.review_status}`);
  }
  return { id: solutionId, status: updated.status, review_status: updated.review_status };
};

const exerciseTechnicalTemplateViaUi = async (page, templateName, templateCode) => {
  await gotoRoute(page, "/presales/technical-solutions?tab=parameters", 900);
  await page.getByRole("button", { name: /新增模板/ }).click();
  let modal = page.locator(".fixed.inset-0").filter({ hasText: "创建模板" }).last();
  await modal.waitFor({ state: "visible", timeout: 8000 });
  await modal.locator('input[type="text"]').nth(0).fill(templateName);
  await modal.locator('input[type="text"]').nth(1).fill(templateCode);
  await modal.locator("select").nth(0).selectOption("AUTOMOTIVE");
  await modal.locator("select").nth(1).selectOption("FCT");
  await modal.locator("textarea").nth(0).fill(`${runPrefix} 技术参数模板描述`);
  await modal.locator("textarea").nth(1).fill(
    JSON.stringify(
      {
        station_count: { label: "测试工位数", type: "number", default: 4, unit: "个" },
        cycle_time: { label: "节拍时间", type: "number", default: 30, unit: "秒" },
      },
      null,
      2,
    ),
  );
  await modal.locator("textarea").nth(2).fill(
    JSON.stringify(
      {
        base_cost: 50000,
        factors: {
          station_count: { type: "linear", coefficient: 8000 },
          cycle_time: { type: "inverse", base: 30, coefficient: 12000 },
        },
        category_ratios: {
          MECHANICAL: 0.35,
          ELECTRICAL: 0.3,
          SOFTWARE: 0.15,
          LABOR: 0.2,
        },
      },
      null,
      2,
    ),
  );

  const createResponse = await waitForApi(page, "POST", "/api/v1/presale/technical-parameters/templates", async () => {
    await modal.getByRole("button", { name: /^保存$/ }).click();
  });
  await waitQuiet(page, 1000);
  const created = parseJson(createResponse.body) || {};
  const templateId = created.id || created?.data?.id;
  if (!templateId) {
    throw new Error(`技术参数模板创建未返回 id: ${createResponse.body?.slice(0, 400)}`);
  }
  report.created.technicalTemplates.push({ id: templateId, code: templateCode, deleted: false });

  await page.getByPlaceholder("搜索模板名称或编码...").fill(templateCode);
  await waitQuiet(page, 600);
  let row = page.locator(".rounded-xl").filter({ hasText: templateCode }).first();
  await row.waitFor({ state: "visible", timeout: 8000 });
  await row.locator('button[title="编辑"]').click();
  modal = page.locator(".fixed.inset-0").filter({ hasText: "编辑模板" }).last();
  await modal.waitFor({ state: "visible", timeout: 8000 });
  await modal.locator("textarea").nth(0).fill(`${runPrefix} 技术参数模板描述-已编辑`);
  await waitForApi(
    page,
    "PUT",
    `/api/v1/presale/technical-parameters/templates/${templateId}`,
    async () => {
      await modal.getByRole("button", { name: /^保存$/ }).click();
    },
  );
  await waitQuiet(page, 900);

  row = page.locator(".rounded-xl").filter({ hasText: templateCode }).first();
  await row.locator('button[title="成本估算"]').click();
  modal = page.locator(".fixed.inset-0").filter({ hasText: "成本估算" }).last();
  await modal.waitFor({ state: "visible", timeout: 8000 });
  const estimateInputs = modal.locator('input[type="number"]');
  await estimateInputs.nth(0).fill("6");
  await estimateInputs.nth(1).fill("24");
  await waitForApi(page, "POST", "/api/v1/presale/technical-parameters/estimate-cost", async () => {
    await modal.getByRole("button", { name: /计算成本/ }).click();
  });
  await modal.getByText("预估总成本").waitFor({ state: "visible", timeout: 8000 });
  await modal.getByRole("button", { name: /^关闭$/ }).click();
  await waitQuiet(page, 500);

  row = page.locator(".rounded-xl").filter({ hasText: templateCode }).first();
  await waitForApi(
    page,
    "DELETE",
    `/api/v1/presale/technical-parameters/templates/${templateId}`,
    async () => {
      await row.locator('button[title="删除"]').click();
    },
  );
  await waitQuiet(page, 900);
  const tracked = report.created.technicalTemplates.find((item) => item.id === templateId);
  if (tracked) {
    tracked.deleted = true;
  }
  const active = await findByKeyword(page, "/presale/technical-parameters/templates", templateCode);
  if (active?.id === templateId) {
    throw new Error("技术参数模板删除后仍出现在启用列表中");
  }
  return { id: templateId, code: templateCode, softDeleted: true };
};

const exerciseTenderViaUi = async (page, tenderName, customerName) => {
  await gotoRoute(page, "/presales/technical-solutions?tab=bids", 900);
  await page.getByRole("button", { name: /新建投标/ }).click();
  await page.locator("#tender_name").fill(tenderName);
  await page.locator("#customer_name").fill(customerName);
  const response = await waitForApi(page, "POST", "/api/v1/presale/tenders", async () => {
    await page.getByRole("button", { name: /^创建投标$/ }).click();
  });
  await waitQuiet(page, 1000);
  const tender = parseJson(response.body) || {};
  const tenderId = tender.id || tender?.data?.id;
  if (!tenderId) {
    throw new Error(`投标创建未返回 id: ${response.body?.slice(0, 400)}`);
  }
  report.created.tenders.push({ id: tenderId, name: tenderName, deleted: false });

  await page.getByPlaceholder("搜索项目名称、客户、编号...").fill(tenderName);
  await waitQuiet(page, 700);
  await page.getByText(tenderName).first().click();
  const panel = page.locator("text=成本支持").locator("xpath=ancestor::*[contains(@class, 'fixed')][1]").last();
  await panel.waitFor({ state: "visible", timeout: 8000 });
  await panel.getByRole("button", { name: /申请成本支持/ }).click();
  await waitQuiet(page, 900);
  const url = new URL(page.url());
  if (url.searchParams.get("tab") !== "cost" || url.searchParams.get("tender_id") !== String(tenderId)) {
    throw new Error(`申请成本支持跳转异常: ${page.url()}`);
  }
  return { id: tenderId, costTabUrl: page.url() };
};

const createSolutionTemplateSeed = async (page, templateName) => {
  const response = await browserApi(page, "POST", "/presale/templates", {
    name: templateName,
    industry: "新能源",
    test_type: "FCT",
    description: `${runPrefix} 售前模板库 UI 测试模板`,
    content_template: "1. 客户需求\n2. 技术方案\n3. 成本测算\n4. 风险控制",
    cost_template: {},
    attachments: [],
  });
  const template = unwrap(response);
  if (!template?.id) {
    throw new Error(`模板库种子创建未返回 id: ${JSON.stringify(response).slice(0, 400)}`);
  }
  report.created.solutionTemplates.push({ id: template.id, name: templateName, deleted: false });
  return template;
};

const exerciseSolutionTemplateLibraryViaUi = async (page, template) => {
  await gotoRoute(page, "/presales/technical-solutions?tab=knowledge", 900);
  await page.locator('input[placeholder^="搜索模板名称"]').fill(template.name);
  await waitQuiet(page, 700);
  await page.getByText(template.name).first().waitFor({ state: "visible", timeout: 8000 });
  await page.getByRole("button", { name: /模板预览/ }).first().click();
  await page.getByRole("dialog").filter({ hasText: template.name }).waitFor({ state: "visible", timeout: 8000 });
  await waitForApi(page, "PUT", `/api/v1/presale/templates/${template.id}`, async () => {
    await page.getByRole("button", { name: /立即应用模板/ }).click();
  });
  await waitQuiet(page, 700);
  const ratingBox = page
    .getByText("请为模板评分")
    .first()
    .locator("xpath=ancestor::div[contains(@class, 'rounded-xl')][1]");
  const stars = ratingBox.locator("button");
  await waitForApi(page, "PUT", `/api/v1/presale/templates/${template.id}`, async () => {
    await stars.nth(4).click({ force: true });
  });
  await waitQuiet(page, 700);
  const updated = unwrap(await browserApi(page, "GET", `/presale/templates/${template.id}`));
  if ((updated.use_count || 0) < 1) {
    throw new Error(`模板应用次数未更新: ${updated.use_count}`);
  }
  return { id: template.id, use_count: updated.use_count };
};

const assertWorkbenchNavigation = async (page) => {
  await gotoRoute(page, "/presales/workbench", 900);
  await page.getByText("售前技术支持工作台").waitFor({ state: "visible", timeout: 8000 });
  const checks = [
    ["/presales/workbench/sales", "销售协同"],
    ["/presales/workbench/execution", "售前执行"],
    ["/presales/workbench/manager", "经理调度"],
    ["/presales/technical-solutions?tab=solutions", "技术方案"],
    ["/presales/technical-solutions?tab=cost", "成本估算"],
    ["/presales/technical-solutions?tab=knowledge", "模板库"],
    ["/presales/technical-solutions?tab=parameters", "技术参数"],
  ];

  for (const [href, label] of checks) {
    await gotoRoute(page, "/presales/workbench", 500);
    await page.locator(`a[href="${href}"]`).first().click();
    await waitQuiet(page, 900);
    if (await isLoginPage(page)) {
      throw new Error(`点击 ${label} 后回到登录页`);
    }
  }
  return { clicked: checks.map(([, label]) => label) };
};

const sqlList = (items) => items.map((item) => Number(item.id)).filter(Number.isInteger);

const execSql = (sql) => {
  execFileSync("sqlite3", [DB_PATH, sql], { stdio: "pipe" });
};

const cleanupCreatedData = () => {
  const solutionIds = sqlList(report.created.solutions);
  const tenderIds = sqlList(report.created.tenders);
  const ticketIds = sqlList(report.created.tickets);
  const technicalTemplateIds = sqlList(report.created.technicalTemplates);
  const solutionTemplateIds = sqlList(report.created.solutionTemplates);

  const statements = [];
  if (solutionIds.length) {
    statements.push(`DELETE FROM presale_solution_cost WHERE solution_id IN (${solutionIds.join(",")});`);
    statements.push(`DELETE FROM presale_solution WHERE id IN (${solutionIds.join(",")});`);
  }
  if (tenderIds.length) {
    statements.push(`DELETE FROM presale_tender_record WHERE id IN (${tenderIds.join(",")});`);
  }
  if (ticketIds.length) {
    statements.push(`DELETE FROM presale_ticket_progress WHERE ticket_id IN (${ticketIds.join(",")});`);
    statements.push(`DELETE FROM presale_ticket_deliverable WHERE ticket_id IN (${ticketIds.join(",")});`);
    statements.push(`DELETE FROM presale_support_ticket WHERE id IN (${ticketIds.join(",")});`);
  }
  if (technicalTemplateIds.length) {
    statements.push(`DELETE FROM technical_parameter_templates WHERE id IN (${technicalTemplateIds.join(",")});`);
  }
  if (solutionTemplateIds.length) {
    statements.push(`DELETE FROM presale_solution_template WHERE id IN (${solutionTemplateIds.join(",")});`);
  }
  if (!statements.length) {
    return;
  }

  try {
    execSql(["PRAGMA foreign_keys=OFF;", ...statements].join("\n"));
    for (const item of report.created.solutions) item.deleted = true;
    for (const item of report.created.tenders) item.deleted = true;
    for (const item of report.created.tickets) item.deleted = true;
    for (const item of report.created.technicalTemplates) item.deleted = true;
    for (const item of report.created.solutionTemplates) item.deleted = true;
    report.cleanup.push({
      type: "sqlite",
      status: "deleted",
      solutionIds,
      tenderIds,
      ticketIds,
      technicalTemplateIds,
      solutionTemplateIds,
    });
  } catch (error) {
    report.cleanup.push({ type: "sqlite", status: "failed", error: error.message });
  }
};

const main = async () => {
  const browser = await chromium.launch({ headless });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });

  page.on("console", (msg) => {
    if (msg.type() === "error" || msg.type() === "warning") {
      report.console.push({
        type: msg.type(),
        text: msg.text(),
        url: page.url(),
        at: new Date().toISOString(),
      });
    }
  });
  page.on("pageerror", (error) => {
    report.pageErrors.push({ message: error.message, stack: error.stack, url: page.url() });
  });
  page.on("requestfailed", (request) => {
    const failure = request.failure()?.errorText;
    if (failure !== "net::ERR_ABORTED") {
      report.requestFailures.push({ url: request.url(), method: request.method(), failure, pageUrl: page.url() });
    }
  });
  page.on("response", async (response) => {
    const status = response.status();
    const url = response.url();
    if (url.includes("/api/") && status >= 400 && status !== 401 && status !== 403 && status !== 429) {
      report.apiErrors.push({
        url,
        status,
        method: response.request().method(),
        pageUrl: page.url(),
        body: (await response.text().catch(() => "")).slice(0, 600),
      });
    }
  });
  page.on("dialog", async (dialog) => {
    report.dialogs.push({
      type: dialog.type(),
      message: dialog.message(),
      url: page.url(),
      at: new Date().toISOString(),
    });
    await dialog.accept().catch(() => {});
  });

  const surveyTitle = `${runPrefix}_需求调研`;
  const taskTitle = `${runPrefix}_方案设计任务`;
  const solutionName = `${runPrefix}_技术方案`;
  const technicalTemplateName = `${runPrefix}_参数模板`;
  const technicalTemplateCode = `${runPrefix}_PARAM`;
  const tenderName = `${runPrefix}_投标项目`;
  const templateName = `${runPrefix}_模板库样例`;
  const customerName = `${runPrefix}_客户`;

  try {
    await ensureAuthenticated(page);

    await runStep(page, "工作台-角色入口和资产入口导航", async () => assertWorkbenchNavigation(page));

    await runStep(page, "需求调研-UI创建调研工单", async () => {
      const ticket = await createTicketViaUi(
        page,
        "/presales/technical-solutions?tab=surveys",
        surveyTitle,
        customerName,
        `${runPrefix} 现场需求调研：治具空间、电气接口、验收口径待确认。`,
        "survey",
      );
      const found = await findByKeyword(page, "/presale/tickets", surveyTitle);
      if (!found?.id) {
        throw new Error("调研工单创建后列表接口未查到");
      }
      return ticket;
    });

    let task = null;
    await runStep(page, "工单看板-UI创建售前任务", async () => {
      task = await createTicketViaUi(
        page,
        "/presales/technical-solutions?tab=reviews",
        taskTitle,
        customerName,
        `${runPrefix} 方案设计任务：FCT + MES + 数据追溯，要求输出方案、成本和风险。`,
        "task",
      );
      return task;
    });

    await runStep(page, "工单看板-接单进度交付物完成评价闭环", async () => {
      if (!task?.id) {
        throw new Error("缺少已创建售前任务");
      }
      return exerciseTicketLifecycleViaUi(page, task, taskTitle);
    });

    await runStep(page, "方案管理-UI创建方案并提交评审", async () =>
      exerciseSolutionViaUi(page, solutionName),
    );

    await runStep(page, "技术参数-UI创建编辑估算删除模板", async () =>
      exerciseTechnicalTemplateViaUi(page, technicalTemplateName, technicalTemplateCode),
    );

    await runStep(page, "投标支持-UI创建投标并进入成本支持", async () =>
      exerciseTenderViaUi(page, tenderName, customerName),
    );

    let solutionTemplate = null;
    await runStep(page, "知识模板-种子模板创建", async () => {
      solutionTemplate = await createSolutionTemplateSeed(page, templateName);
      return { id: solutionTemplate.id, name: solutionTemplate.name };
    });

    await runStep(page, "知识模板-UI预览应用评分", async () => {
      if (!solutionTemplate?.id) {
        throw new Error("缺少模板库种子模板");
      }
      return exerciseSolutionTemplateLibraryViaUi(page, solutionTemplate);
    });
  } finally {
    cleanupCreatedData();
    await browser.close().catch(() => {});
  }

  const file = writeReport();
  const failedSteps = report.steps.filter((step) => step.status === "failed").length;
  const cleanupFailures = report.cleanup.filter((item) => item.status === "failed").length;
  const hardConsoleErrors = report.console.filter(
    (item) => item.type === "error" && !/Warning:|429|Too Many Requests/.test(item.text),
  ).length;
  const summary = {
    file,
    runPrefix,
    steps: report.steps.length,
    failedSteps,
    apiErrors: report.apiErrors.length,
    pageErrors: report.pageErrors.length,
    requestFailures: report.requestFailures.length,
    consoleItems: report.console.length,
    hardConsoleErrors,
    cleanupFailures,
    cleanup: report.cleanup,
  };
  console.log(JSON.stringify(summary, null, 2));
  if (
    failedSteps > 0 ||
    report.apiErrors.length > 0 ||
    report.pageErrors.length > 0 ||
    report.requestFailures.length > 0 ||
    hardConsoleErrors > 0 ||
    cleanupFailures > 0
  ) {
    process.exitCode = 1;
  }
};

main().catch((error) => {
  report.fatal = error?.stack || error?.message || String(error);
  cleanupCreatedData();
  const file = writeReport();
  console.error(report.fatal);
  console.error(`report: ${file}`);
  process.exit(1);
});
