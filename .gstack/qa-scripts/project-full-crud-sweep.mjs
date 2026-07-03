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
const runPrefix = `QA_PROJECT_${stamp}`;
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
    tasks: [],
    milestones: [],
    costs: [],
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
  const file = path.join(reportDir, `project-full-crud-sweep-${stamp}.json`);
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
  const file = path.join(screenshotDir, `project-full-${safe}-${stamp}.png`);
  await page.screenshot({ path: file, fullPage: true }).catch(() => {});
  report.screenshots.push(file);
  return file;
};

const waitQuiet = async (page, settleMs = 600) => {
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
    throw new Error(`${method} ${apiPath} -> ${result.status}: ${result.text?.slice(0, 500)}`);
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
    throw new Error(`${method} ${pattern} -> ${response.status()}: ${body.slice(0, 500)}`);
  }
  return { status: response.status(), body };
};

const runStep = async (page, name, fn) => {
  const step = { name, startedAt: new Date().toISOString(), status: "running" };
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

const createProjectViaUi = async (page) => {
  const projectCode = `${runPrefix}_CODE`.slice(0, 48);
  const projectName = `${runPrefix}_项目管理链路`;

  await gotoRoute(page, "/project/management-center?tab=board&view=card", 1000);
  await page.getByText("项目中心").first().waitFor({ state: "visible", timeout: 10000 });
  await page.getByRole("button", { name: /新建项目/ }).first().click();

  const dialog = page.getByRole("dialog", { name: /新建项目/ });
  await dialog.waitFor({ state: "visible", timeout: 10000 });
  await dialog.getByPlaceholder("例如: PJ260104001").fill(projectCode);
  await dialog.getByPlaceholder("请输入项目全称").fill(projectName);
  await dialog.getByPlaceholder("项目简称（可选）").fill(`${runPrefix.slice(-8)}项目`);
  await dialog.getByPlaceholder("例如: ICT测试设备").fill("FCT测试设备");
  await dialog.getByPlaceholder("例如: 消费电子").fill("新能源");
  await dialog.getByPlaceholder("请输入项目描述").fill(`${runPrefix} 从售前移交到项目执行的真实浏览器验证项目`);
  await dialog.getByRole("button", { name: /下一步/ }).click();

  await dialog.getByPlaceholder("搜索客户名称或编码").fill("比亚迪");
  await dialog.getByText("比亚迪汽车工业有限公司（演示）", { exact: false }).first().click();
  await dialog.locator('input[placeholder="合同编号（可选）"]').fill(`${runPrefix}-CONTRACT`);
  await dialog.getByRole("button", { name: /下一步/ }).click();

  const financeNumbers = dialog.locator('input[type="number"]');
  await financeNumbers.nth(0).fill("360000");
  await financeNumbers.nth(1).fill("260000");
  await dialog.locator('input[type="date"]').fill("2026-07-01");
  await dialog.getByRole("button", { name: /下一步/ }).click();

  const scheduleDates = dialog.locator('input[type="date"]');
  await scheduleDates.nth(0).fill("2026-07-02");
  await scheduleDates.nth(1).fill("2026-08-16");
  await dialog.getByPlaceholder("请输入项目需求摘要（可选）").fill(`${runPrefix} 项目需求摘要：售前方案已完成，进入项目执行。`);

  const response = await waitForApi(page, "POST", "/api/v1/projects/", async () => {
    await dialog.getByRole("button", { name: /创建项目/ }).click();
  });
  await waitQuiet(page, 1200);
  const project = parseJson(response.body) || {};
  const projectId = project.id || project?.data?.id;
  if (!projectId) {
    throw new Error(`创建项目未返回 id: ${response.body?.slice(0, 500)}`);
  }
  report.created.projects.push({ id: projectId, project_code: projectCode, project_name: projectName, deleted: false });

  const saved = unwrap(await browserApi(page, "GET", `/projects/${projectId}`));
  if (saved.project_code !== projectCode) {
    throw new Error(`项目创建后读取异常: expected ${projectCode}, got ${saved.project_code}`);
  }

  return { id: projectId, project_code: projectCode, project_name: saved.project_name || saved.name };
};

const assertProjectCenterTabs = async (page, projectId) => {
  const checks = [
    ["/project/management-center?tab=board&view=list", "看板"],
    ["/project/management-center?tab=dashboard", "驾驶舱"],
    ["/project/management-center?tab=tasks&project_id=" + projectId, "任务"],
    ["/project/management-center?tab=tracking&trackingTab=milestones&project_id=" + projectId, "进度"],
    ["/project/management-center?tab=presales&project_id=" + projectId, "售前"],
    ["/project/management-center?tab=planning&project_id=" + projectId, "计划资源"],
    ["/project/management-center?tab=cost&project_id=" + projectId, "成本"],
    ["/project/management-center?tab=closing&project_id=" + projectId, "收尾"],
    ["/project/management-center?tab=ai&project_id=" + projectId, "AI工具"],
  ];

  const visited = [];
  for (const [route, label] of checks) {
    await gotoRoute(page, route, 900);
    if (await isLoginPage(page)) {
      throw new Error(`项目中心 ${label} 进入后回到登录页`);
    }
    await page.locator("main").waitFor({ state: "visible", timeout: 8000 });
    visited.push(label);
  }
  return { visited };
};

const createProjectTaskViaUi = async (page, projectId) => {
  const taskName = `${runPrefix}_项目任务`;
  await gotoRoute(page, `/projects/${projectId}/tasks`, 1000);
  await page.getByRole("button", { name: /新建任务/ }).click();
  const dialog = page.getByRole("dialog", { name: /新建任务/ });
  await dialog.waitFor({ state: "visible", timeout: 8000 });
  await dialog.getByPlaceholder("请输入任务名称").fill(taskName);
  const dates = dialog.locator('input[type="date"]');
  await dates.nth(0).fill("2026-07-03");
  await dates.nth(1).fill("2026-07-12");
  await dialog.locator('input[type="number"]').fill("30");
  await dialog.getByPlaceholder("任务描述").fill(`${runPrefix} 项目执行任务描述`);

  const response = await waitForApi(page, "POST", `/api/v1/projects/${projectId}/tasks`, async () => {
    await dialog.getByRole("button", { name: /^创建$/ }).click();
  });
  await waitQuiet(page, 1000);
  const task = parseJson(response.body) || {};
  if (!task.id) {
    throw new Error(`创建项目任务未返回 id: ${response.body?.slice(0, 500)}`);
  }
  report.created.tasks.push({ id: task.id, project_id: projectId, task_name: taskName, deleted: false });

  await page.getByPlaceholder("搜索任务名称...").fill(taskName);
  await waitQuiet(page, 700);
  await page.getByText(taskName, { exact: false }).first().waitFor({ state: "visible", timeout: 8000 });
  await page.locator("tr").filter({ hasText: taskName }).first().getByRole("button").click();
  await page.getByRole("dialog", { name: /任务详情/ }).waitFor({ state: "visible", timeout: 8000 });

  return { id: task.id, task_name: taskName };
};

const createAndCompleteMilestoneViaUi = async (page, projectId) => {
  const milestoneName = `${runPrefix}_里程碑`;
  await gotoRoute(page, `/projects/${projectId}/milestones`, 1000);
  await page.getByRole("button", { name: /新建里程碑/ }).click();
  const dialog = page.getByRole("dialog", { name: /新建里程碑/ });
  await dialog.waitFor({ state: "visible", timeout: 8000 });
  await dialog.getByPlaceholder("请输入里程碑名称").fill(milestoneName);
  await dialog.locator('input[type="date"]').fill("2026-07-20");
  await dialog.locator('input[type="number"]').fill("120000");
  await dialog.getByPlaceholder("里程碑描述").fill(`${runPrefix} 里程碑描述`);

  const response = await waitForApi(page, "POST", "/api/v1/milestones/", async () => {
    await dialog.getByRole("button", { name: /^创建$/ }).click();
  });
  await waitQuiet(page, 1000);
  const milestone = parseJson(response.body) || {};
  if (!milestone.id) {
    throw new Error(`创建里程碑未返回 id: ${response.body?.slice(0, 500)}`);
  }
  report.created.milestones.push({ id: milestone.id, project_id: projectId, milestone_name: milestoneName, deleted: false });

  await page.getByPlaceholder("搜索里程碑...").fill(milestoneName);
  await waitQuiet(page, 700);
  const row = page.locator(".relative.border-l-2").filter({ hasText: milestoneName }).first();
  await row.waitFor({ state: "visible", timeout: 8000 });
  await row.getByRole("button").first().click();
  await page.getByRole("dialog", { name: /里程碑详情/ }).waitFor({ state: "visible", timeout: 8000 });
  await page.getByRole("dialog", { name: /里程碑详情/ }).getByRole("button", { name: /^关闭$/ }).first().click();

  await waitForApi(page, "PUT", `/api/v1/milestones/${milestone.id}/complete`, async () => {
    await row.getByRole("button", { name: /完成/ }).click();
    const confirmDialog = page.getByText("确认完成此里程碑？").locator("xpath=ancestor::*[contains(@class, 'fixed')][1]");
    await confirmDialog.waitFor({ state: "visible", timeout: 8000 });
    await confirmDialog.getByRole("button", { name: /^确认$/ }).click();
  });
  await waitQuiet(page, 1000);
  const completed = unwrap(await browserApi(page, "GET", `/milestones/${milestone.id}`));
  if (completed.status !== "COMPLETED") {
    throw new Error(`里程碑完成状态异常: ${completed.status}`);
  }

  return { id: milestone.id, status: completed.status };
};

const createCostViaUi = async (page, projectId) => {
  const description = `${runPrefix}_项目成本`;
  await gotoRoute(page, `/costs?project_id=${projectId}`, 1200);
  await page.getByRole("button", { name: /录入成本/ }).click();
  const dialog = page.getByRole("dialog", { name: /录入成本/ });
  await dialog.waitFor({ state: "visible", timeout: 8000 });
  await dialog.locator("select").nth(0).selectOption(String(projectId));
  await dialog.locator("select").nth(1).selectOption("MATERIAL");
  await dialog.getByPlaceholder("请输入金额").fill("12345.67");
  await dialog.locator('input[type="date"]').fill("2026-07-04");
  await dialog.getByPlaceholder("请输入成本描述...").fill(description);

  const response = await waitForApi(page, "POST", `/api/v1/projects/${projectId}/costs/`, async () => {
    await dialog.getByRole("button", { name: /^保存$/ }).click();
  });
  await waitQuiet(page, 1200);
  const cost = parseJson(response.body) || {};
  if (!cost.id) {
    throw new Error(`录入成本未返回 id: ${response.body?.slice(0, 500)}`);
  }
  report.created.costs.push({ id: cost.id, project_id: projectId, description, deleted: false });

  const saved = unwrap(await browserApi(page, "GET", `/projects/${projectId}/costs/${cost.id}`));
  if (String(saved.description) !== description) {
    throw new Error(`成本读取异常: ${JSON.stringify(saved).slice(0, 500)}`);
  }

  return { id: cost.id, amount: saved.amount, cost_basis: saved.cost_basis };
};

const verifyProjectDownstreamData = async (page, projectId) => {
  const project = unwrap(await browserApi(page, "GET", `/projects/${projectId}`));
  const tasks = listItems(await browserApi(page, "GET", `/projects/${projectId}/tasks?page=1&page_size=100`));
  const milestones = listItems(await browserApi(page, "GET", `/milestones/?page=1&page_size=100&project_id=${projectId}`));
  const costs = listItems(await browserApi(page, "GET", `/projects/${projectId}/costs/?page=1&page_size=100`));
  return {
    project_code: project.project_code,
    tasks: tasks.length,
    milestones: milestones.length,
    costs: costs.length,
  };
};

const shellSql = (sql, args = []) =>
  execFileSync("sqlite3", [DB_PATH, ...args, sql], { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] });

const sqlList = (items) => items.map((item) => Number(item.id)).filter(Number.isInteger);

const cleanupCreatedData = () => {
  const projectIds = sqlList(report.created.projects);
  const taskIds = sqlList(report.created.tasks);
  const milestoneIds = sqlList(report.created.milestones);
  const costIds = sqlList(report.created.costs);
  if (!projectIds.length) return;

  const projectList = projectIds.join(",");
  const taskList = taskIds.join(",");
  const milestoneList = milestoneIds.join(",");
  const costList = costIds.join(",");
  const statements = ["PRAGMA foreign_keys=OFF;"];

  if (taskIds.length) {
    statements.push(`DELETE FROM task_operation_log WHERE task_id IN (${taskList});`);
    statements.push(`DELETE FROM task_comment WHERE task_id IN (${taskList});`);
    statements.push(`DELETE FROM task_dependencies WHERE task_id IN (${taskList}) OR depends_on_task_id IN (${taskList});`);
    statements.push(`DELETE FROM tasks WHERE id IN (${taskList});`);
  }
  if (milestoneIds.length) {
    statements.push(`DELETE FROM project_milestones WHERE id IN (${milestoneList});`);
  }
  if (costIds.length) {
    statements.push(`DELETE FROM project_costs WHERE id IN (${costList});`);
  }

  const fkRows = shellSql(
    "select m.name || '|' || fk.'from' from sqlite_master m, pragma_foreign_key_list(m.name) fk where fk.'table'='projects' order by m.name;",
  )
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [table, column] = line.split("|");
      return { table, column };
    });

  for (const { table, column } of fkRows) {
    if (table === "projects") continue;
    statements.push(`DELETE FROM "${table}" WHERE "${column}" IN (${projectList});`);
  }
  statements.push(`DELETE FROM projects WHERE id IN (${projectList});`);
  statements.push("PRAGMA foreign_keys=ON;");

  shellSql(statements.join("\n"));

  for (const item of report.created.projects) item.deleted = true;
  for (const item of report.created.tasks) item.deleted = true;
  for (const item of report.created.milestones) item.deleted = true;
  for (const item of report.created.costs) item.deleted = true;
  report.cleanup.push({
    type: "sqlite",
    status: "deleted",
    projectIds,
    taskIds,
    milestoneIds,
    costIds,
  });
};

const main = async () => {
  const browser = await chromium.launch({ headless, slowMo: headless ? 0 : 60 });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  const page = await context.newPage();

  page.on("console", (msg) => {
    const text = msg.text();
    const type = msg.type();
    if (["error", "warning"].includes(type)) {
      report.console.push({ type, text, url: page.url() });
    }
  });
  page.on("pageerror", (error) => {
    report.pageErrors.push({ message: error.message, stack: error.stack, url: page.url() });
  });
  page.on("requestfailed", (request) => {
    report.requestFailures.push({
      url: request.url(),
      method: request.method(),
      failure: request.failure()?.errorText,
    });
  });
  page.on("response", async (response) => {
    const url = response.url();
    if (!url.includes("/api/")) return;
    const status = response.status();
    if (status >= 400) {
      report.apiErrors.push({
        status,
        method: response.request().method(),
        url,
        body: (await response.text().catch(() => "")).slice(0, 800),
      });
    }
  });
  page.on("dialog", async (dialog) => {
    report.dialogs.push({ type: dialog.type(), message: dialog.message(), url: page.url() });
    await dialog.accept().catch(() => {});
  });

  let reportFile = "";
  try {
    await ensureAuthenticated(page);
    let project;
    await runStep(page, "项目看板-新建项目", async () => {
      project = await createProjectViaUi(page);
      return project;
    });
    if (project?.id) {
      await runStep(page, "项目中心-九个主入口导航", () => assertProjectCenterTabs(page, project.id));
      await runStep(page, "项目任务-创建并查看详情", () => createProjectTaskViaUi(page, project.id));
      await runStep(page, "里程碑-创建查看并完成", () => createAndCompleteMilestoneViaUi(page, project.id));
      await runStep(page, "成本核算-录入项目成本", () => createCostViaUi(page, project.id));
      await runStep(page, "项目下游数据-API复核", () => verifyProjectDownstreamData(page, project.id));
    }
  } finally {
    try {
      cleanupCreatedData();
    } catch (error) {
      report.cleanup.push({ type: "sqlite", status: "failed", error: error?.stack || error?.message || String(error) });
    }
    reportFile = writeReport();
    await context.close().catch(() => {});
    await browser.close().catch(() => {});
    console.log(`[report] ${reportFile}`);
    console.log(`[summary] runPrefix=${runPrefix}`);
    console.log(`[summary] steps=${report.steps.length} failedSteps=${report.steps.filter((s) => s.status === "failed").length}`);
    console.log(
      `[summary] apiErrors=${report.apiErrors.length} pageErrors=${report.pageErrors.length} requestFailures=${report.requestFailures.length} consoleItems=${report.console.length}`,
    );
    console.log(`[summary] cleanupFailures=${report.cleanup.filter((item) => item.status === "failed").length}`);
  }

  const failedSteps = report.steps.filter((step) => step.status === "failed");
  if (
    failedSteps.length ||
    report.apiErrors.length ||
    report.pageErrors.length ||
    report.requestFailures.length ||
    report.console.length ||
    report.cleanup.some((item) => item.status === "failed")
  ) {
    process.exitCode = 1;
  }
};

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
