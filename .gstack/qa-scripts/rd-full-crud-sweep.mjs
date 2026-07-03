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
const UPLOAD_DIR = process.env.QA_UPLOAD_DIR || "uploads";
const headless = process.env.QA_HEADLESS !== "0";
const stamp = new Date().toISOString().replace(/[-:TZ.]/g, "").slice(0, 14);
const runPrefix = `QA_RD_${stamp}`;
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
    rdProjects: [],
    rdCosts: [],
    worklogs: [],
    documents: [],
    uploadFiles: [],
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
  const file = path.join(reportDir, `rd-full-crud-sweep-${stamp}.json`);
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
  const file = path.join(screenshotDir, `rd-full-${safe}-${stamp}.png`);
  await page.screenshot({ path: file, fullPage: true }).catch(() => {});
  report.screenshots.push(file);
  return file;
};

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

const selectRadixOption = async (page, scope, index, optionName) => {
  await scope.getByRole("combobox").nth(index).click();
  await page.getByRole("option", { name: optionName }).click();
};

const clickDetailTab = async (page, label) => {
  const trigger = page.locator("button, [role='tab']").filter({ hasText: label }).first();
  await trigger.waitFor({ state: "visible", timeout: 10000 });
  await trigger.click();
  await waitQuiet(page, 400);
};

const createRdProjectViaUi = async (page) => {
  const projectName = `${runPrefix}_研发立项`;
  await gotoRoute(page, "/rd-projects", 1000);
  await page.getByText("研发项目管理").first().waitFor({ state: "visible", timeout: 10000 });
  await page.getByRole("button", { name: /创建研发项目|创建第一个研发项目/ }).first().click();

  const dialog = page.getByRole("dialog", { name: /创建研发项目/ });
  await dialog.waitFor({ state: "visible", timeout: 10000 });
  await dialog.getByPlaceholder("请输入项目名称").fill(projectName);
  const dates = dialog.locator('input[type="date"]');
  await dates.nth(0).fill("2026-07-01");
  await dates.nth(1).fill("2026-07-02");
  await dates.nth(2).fill("2026-09-30");
  await dialog.locator('input[type="number"]').fill("180000");
  const textareas = dialog.locator("textarea");
  await textareas.nth(0).fill(`${runPrefix} 立项原因：围绕非标自动化测试平台进行工艺验证。`);
  await textareas.nth(1).fill(`${runPrefix} 研究目标：形成可复用夹治具设计参数和验证报告。`);
  await textareas.nth(2).fill(`${runPrefix} 研究内容：结构验证、测试流程、BOM 成本和工时沉淀。`);
  await textareas.nth(3).fill(`${runPrefix} 预期结果：输出研发样机验证包。`);
  await textareas.nth(4).fill(`${runPrefix} 浏览器 QA 创建`);

  const response = await waitForApi(page, "POST", "/api/v1/rd-projects", async () => {
    await dialog.getByRole("button", { name: /创建项目/ }).click();
  });
  const created = unwrap(response.json);
  if (!created.id) throw new Error(`研发项目创建未返回 id: ${response.body.slice(0, 600)}`);
  report.created.rdProjects.push({
    id: created.id,
    project_no: created.project_no,
    project_name: created.project_name,
  });
  await page.getByText(projectName).first().waitFor({ state: "visible", timeout: 10000 });
  return created;
};

const verifyRdCostEntryMenuRoute = async (page) => {
  await gotoRoute(page, "/rd-cost", 1000);
  await page.waitForURL((url) => ["/rd-cost-summary", "/rd-cost"].includes(new URL(url).pathname), {
    timeout: 10000,
  }).catch(() => {});
  await page.getByText(/请选择研发项目查看研发费用汇总|研发项目不存在/).first().waitFor({
    state: "visible",
    timeout: 10000,
  });
  const stillLoading = await page.getByText("加载中...").first().isVisible().catch(() => false);
  if (stillLoading) throw new Error("/rd-cost 入口仍停留在加载中");
  return { route: new URL(page.url()).pathname };
};

const verifyDetailNavigation = async (page, rdProject) => {
  await gotoRoute(page, `/rd-projects/${rdProject.id}`, 1000);
  await page.getByText(`研发项目 - ${rdProject.project_name}`).first().waitFor({ state: "visible", timeout: 10000 }).catch(async () => {
    await page.getByText(rdProject.project_name).first().waitFor({ state: "visible", timeout: 10000 });
  });

  await page.getByRole("button", { name: /录入费用/ }).first().click();
  await page.waitForURL((url) => new URL(url).pathname === `/rd-projects/${rdProject.id}/cost-entry`, {
    timeout: 10000,
  });
  await page.getByText("研发费用录入").first().waitFor({ state: "visible", timeout: 10000 });

  await gotoRoute(page, `/rd-projects/${rdProject.id}`, 700);
  await page.getByRole("button", { name: /费用汇总/ }).first().click();
  await page.waitForURL((url) => new URL(url).pathname === `/rd-projects/${rdProject.id}/cost-summary`, {
    timeout: 10000,
  });
  await page.getByText("研发费用汇总").first().waitFor({ state: "visible", timeout: 10000 });

  await gotoRoute(page, `/rd-projects/${rdProject.id}`, 700);
  await clickDetailTab(page, "报表");
  await page.getByText("加计扣除明细").first().click();
  await page.waitForURL(
    (url) =>
      new URL(url).pathname === `/rd-projects/${rdProject.id}/reports` &&
      new URL(url).searchParams.get("type") === "deduction-detail",
    { timeout: 10000 },
  );
  await page.getByText("研发费用报表").first().waitFor({ state: "visible", timeout: 10000 });
  return { checked: ["cost-entry", "cost-summary", "reports?type=deduction-detail"] };
};

const addRdCostViaUi = async (page, rdProject) => {
  const costTypes = listItems(await browserApi(page, "GET", "/rd-projects/rd-cost-types"));
  const costType = costTypes[0];
  if (!costType?.id) throw new Error("没有可用研发费用类型");
  const costTypeName = costType.cost_type_name || costType.type_name || costType.type_code;
  if (!costTypeName) throw new Error(`研发费用类型缺少显示名称: ${JSON.stringify(costType)}`);

  await gotoRoute(page, `/rd-projects/${rdProject.id}/cost-entry`, 1000);
  await page.getByText("研发费用录入").first().waitFor({ state: "visible", timeout: 10000 });
  await page.getByRole("button", { name: /录入费用|录入第一条费用/ }).first().click();
  const dialog = page.getByRole("dialog", { name: /录入研发费用/ });
  await dialog.waitFor({ state: "visible", timeout: 10000 });
  await selectRadixOption(page, dialog, 0, costTypeName);
  await dialog.locator('input[type="date"]').fill("2026-07-10");
  const numbers = dialog.locator('input[type="number"]');
  await numbers.nth(0).fill("12500");
  await numbers.nth(1).fill("8750");
  await dialog.locator("textarea").nth(0).fill(`${runPrefix} 研发样机材料和测试工装费用`);
  await dialog.locator("textarea").nth(1).fill(`${runPrefix} 研发费用 QA 备注`);

  const response = await waitForApi(page, "POST", "/api/v1/rd-projects/rd-costs", async () => {
    await dialog.getByRole("button", { name: /^保存$/ }).click();
  });
  const created = unwrap(response.json);
  if (!created.id) throw new Error(`研发费用创建未返回 id: ${response.body.slice(0, 600)}`);
  report.created.rdCosts.push({
    id: created.id,
    rd_project_id: rdProject.id,
    cost_no: created.cost_no,
    cost_description: created.cost_description,
  });
  await page.getByText(`${runPrefix} 研发样机材料和测试工装费用`).first().waitFor({
    state: "visible",
    timeout: 10000,
  });
  return created;
};

const addWorklogViaUi = async (page, rdProject) => {
  await gotoRoute(page, `/rd-projects/${rdProject.id}/worklogs`, 1000);
  await page.getByText("研发人员工作日志").first().waitFor({ state: "visible", timeout: 10000 });
  await page.getByRole("button", { name: /记录工作日志|记录第一条工作日志/ }).first().click();
  const dialog = page.getByRole("dialog", { name: /记录工作日志/ });
  await dialog.waitFor({ state: "visible", timeout: 10000 });
  await dialog.locator('input[type="date"]').fill("2026-07-11");
  await dialog.locator('input[type="number"]').fill("3.5");
  await dialog.locator("select").selectOption("OVERTIME");
  await dialog.locator("textarea").fill(`${runPrefix} 完成样机结构验证与测试记录整理`);

  const response = await waitForApi(page, "POST", `/api/v1/rd-projects/${rdProject.id}/worklogs`, async () => {
    await dialog.getByRole("button", { name: /^保存$/ }).click();
  });
  const created = unwrap(response.json);
  if (!created.id) throw new Error(`工作日志创建未返回 id: ${response.body.slice(0, 600)}`);
  report.created.worklogs.push({
    id: created.id,
    rd_project_id: rdProject.id,
    description: created.description,
  });
  await page.getByText(`${runPrefix} 完成样机结构验证与测试记录整理`).first().waitFor({
    state: "visible",
    timeout: 10000,
  });
  return created;
};

const uploadDocumentViaUi = async (page, rdProject) => {
  const localFile = path.join(reportDir, `rd-upload-${stamp}.txt`);
  fs.writeFileSync(localFile, `${runPrefix} 研发项目过程文档\n`, "utf8");

  await gotoRoute(page, `/rd-projects/${rdProject.id}/documents`, 1000);
  await page.getByText("研发项目文档管理").first().waitFor({ state: "visible", timeout: 10000 });
  await page.getByRole("button", { name: /上传文档|上传第一个文档/ }).first().click();
  const dialog = page.getByRole("dialog", { name: /上传文档/ });
  await dialog.waitFor({ state: "visible", timeout: 10000 });
  await dialog.locator('input[type="file"]').setInputFiles(localFile);
  await dialog.locator('input:not([type="file"])').nth(0).fill("V1.1");
  await dialog.locator('input:not([type="file"])').nth(1).fill(`${runPrefix}_研发验证报告.txt`);
  await dialog.locator('input:not([type="file"])').nth(2).fill(`${runPrefix}_DOC`);
  await dialog.locator("textarea").fill(`${runPrefix} 研发验证报告文档上传`);

  const response = await waitForApi(page, "POST", `/api/v1/rd-projects/${rdProject.id}/documents/upload`, async () => {
    await dialog.getByRole("button", { name: /^上传$/ }).click();
  });
  const created = unwrap(response.json);
  if (!created.id) throw new Error(`文档上传未返回 id: ${response.body.slice(0, 600)}`);
  report.created.documents.push({
    id: created.id,
    rd_project_id: rdProject.id,
    project_id: created.project_id,
    doc_name: created.doc_name,
    file_path: created.file_path,
  });
  if (created.file_path) report.created.uploadFiles.push(created.file_path);
  await page.getByText(`${runPrefix}_研发验证报告.txt`).first().waitFor({ state: "visible", timeout: 10000 });

  await page.getByRole("combobox").first().click();
  await page.getByRole("option", { name: "全部类型" }).click();
  await waitQuiet(page, 500);
  await page.getByText(`${runPrefix}_研发验证报告.txt`).first().waitFor({ state: "visible", timeout: 10000 });
  return created;
};

const verifyRdData = async (page, rdProject, rdCost, worklog, document) => {
  const projectDetail = unwrap(await browserApi(page, "GET", `/rd-projects/${rdProject.id}`));
  if (projectDetail.project_name !== rdProject.project_name) {
    throw new Error("研发项目详情名称不匹配");
  }

  const costs = listItems(
    await browserApi(page, "GET", `/rd-projects/rd-costs?rd_project_id=${rdProject.id}&page_size=100`),
  );
  if (!costs.some((item) => item.id === rdCost.id)) throw new Error("研发费用未落库");

  const worklogs = listItems(await browserApi(page, "GET", `/rd-projects/${rdProject.id}/worklogs?page_size=100`));
  if (!worklogs.some((item) => item.id === worklog.id)) throw new Error("研发工作日志未落库");

  const documents = listItems(await browserApi(page, "GET", `/rd-projects/${rdProject.id}/documents?page_size=100`));
  if (!documents.some((item) => item.id === document.id)) throw new Error("研发文档未落库");

  await browserApi(page, "GET", `/rd-projects/${rdProject.id}/cost-summary`);
  await browserApi(page, "GET", `/rd-projects/${rdProject.id}/timesheet-summary`);
  await browserApi(
    page,
    "GET",
    `/report-center/rd-expense/rd-deduction-detail?project_id=${rdProject.id}&year=2026`,
  );

  return {
    project: projectDetail.id,
    costs: costs.length,
    worklogs: worklogs.length,
    documents: documents.length,
  };
};

const shellSql = (sql) => execFileSync("sqlite3", [DB_PATH, sql], { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] });

const idsOf = (items) => items.map((item) => Number(item.id)).filter(Number.isInteger);

const cleanupCreatedData = () => {
  const documentIds = idsOf(report.created.documents);
  const worklogIds = idsOf(report.created.worklogs);
  const costIds = idsOf(report.created.rdCosts);
  const projectIds = idsOf(report.created.rdProjects);
  const statements = ["PRAGMA foreign_keys=OFF;"];

  for (const filePath of report.created.uploadFiles) {
    const resolved = path.resolve(UPLOAD_DIR, filePath);
    const uploadRoot = path.resolve(UPLOAD_DIR);
    if (resolved.startsWith(uploadRoot) && fs.existsSync(resolved)) {
      fs.unlinkSync(resolved);
    }
  }

  if (documentIds.length) statements.push(`DELETE FROM project_documents WHERE id IN (${documentIds.join(",")});`);
  if (worklogIds.length) statements.push(`DELETE FROM timesheet WHERE id IN (${worklogIds.join(",")});`);
  if (costIds.length) statements.push(`DELETE FROM rd_cost WHERE id IN (${costIds.join(",")});`);
  if (projectIds.length) statements.push(`DELETE FROM rd_project WHERE id IN (${projectIds.join(",")});`);
  statements.push("PRAGMA foreign_keys=ON;");

  shellSql(statements.join("\n"));
  for (const item of report.created.documents) item.deleted = true;
  for (const item of report.created.worklogs) item.deleted = true;
  for (const item of report.created.rdCosts) item.deleted = true;
  for (const item of report.created.rdProjects) item.deleted = true;
  report.cleanup.push({ type: "sqlite", status: "deleted", projectIds, costIds, worklogIds, documentIds });
};

const main = async () => {
  const browser = await chromium.launch({ headless, slowMo: headless ? 0 : 60 });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, acceptDownloads: true });
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
    if (request.url().startsWith("https://rsms.me/inter/font-files/")) return;
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

  let rdProject;
  let rdCost;
  let worklog;
  let document;
  let reportFile;
  try {
    await ensureAuthenticated(page);
    await runStep(page, "研发管理-UI创建研发项目", async () => {
      rdProject = await createRdProjectViaUi(page);
      return { rd_project_id: rdProject.id };
    });
    await runStep(page, "研发管理-研发成本菜单入口", async () => verifyRdCostEntryMenuRoute(page));
    await runStep(page, "研发管理-详情快速操作和报表导航", async () => verifyDetailNavigation(page, rdProject));
    await runStep(page, "研发管理-UI录入研发费用", async () => {
      rdCost = await addRdCostViaUi(page, rdProject);
      return { rd_cost_id: rdCost.id };
    });
    await runStep(page, "研发管理-UI记录工作日志", async () => {
      worklog = await addWorklogViaUi(page, rdProject);
      return { worklog_id: worklog.id };
    });
    await runStep(page, "研发管理-UI上传研发文档", async () => {
      document = await uploadDocumentViaUi(page, rdProject);
      return { document_id: document.id, project_id: document.project_id };
    });
    await runStep(page, "研发管理-下游数据API复核", async () => verifyRdData(page, rdProject, rdCost, worklog, document));
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
