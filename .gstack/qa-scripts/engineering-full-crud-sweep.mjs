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
const runPrefix = `QA_ENGINEERING_${stamp}`;
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
    ecns: [],
    ecnTypes: [],
    technicalReviews: [],
    reviewParticipants: [],
    reviewMaterials: [],
    reviewChecklistRecords: [],
    reviewIssues: [],
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
  const file = path.join(reportDir, `engineering-full-crud-sweep-${stamp}.json`);
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
  const file = path.join(screenshotDir, `engineering-full-${safe}-${stamp}.png`);
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

const clickReviewDetailTab = async (page, label) => {
  const trigger = page.locator("button, [role='tab']").filter({ hasText: label }).first();
  await trigger.waitFor({ state: "visible", timeout: 10000 });
  await trigger.click();
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

const chooseRadixOption = async (page, container, triggerText, optionText) => {
  await container.locator('button[role="combobox"]').filter({ hasText: triggerText }).first().click();
  await page.getByRole("option", { name: optionText }).click({ timeout: 8000 });
};

const createSupportProjectViaApi = async (page) => {
  const project = unwrap(
    await browserApi(page, "POST", "/projects/", {
      project_code: `${runPrefix}_PRJ`.slice(0, 48),
      project_name: `${runPrefix}_工程技术载体`,
      short_name: `${runPrefix.slice(-8)}工程`,
      project_type: "CUSTOM",
      contract_no: `${runPrefix}_CONTRACT`.slice(0, 80),
      contract_date: "2026-07-01",
      planned_start_date: "2026-07-02",
      planned_end_date: "2026-09-18",
      contract_amount: 420000,
      budget_amount: 300000,
      description: `${runPrefix} 工程技术模块真实浏览器验收载体项目`,
    }),
  );
  if (!project.id) {
    throw new Error(`项目创建未返回 id: ${JSON.stringify(project).slice(0, 400)}`);
  }
  report.created.projects.push({
    id: project.id,
    project_code: project.project_code,
    project_name: project.project_name,
  });
  return project;
};

const getActiveUsers = async (page) => {
  const payload = await browserApi(page, "GET", "/users/options?page=1&page_size=20&is_active=true");
  const users = listItems(payload);
  if (!users.length) {
    throw new Error("没有可用于技术评审的 active user");
  }
  return users;
};

const createEcnViaUi = async (page, projectId) => {
  const title = `${runPrefix}_设计变更`;
  await gotoRoute(page, "/change-management/ecn-center?tab=management", 1200);
  await page.getByText("ECN中心").first().waitFor({ state: "visible", timeout: 10000 });
  await page.getByRole("button", { name: /新建 ECN/ }).first().click();

  const dialog = page.getByRole("dialog", { name: /新建 ECN 工程变更/ });
  await dialog.waitFor({ state: "visible", timeout: 10000 });
  await dialog.locator('input[placeholder="留空自动生成"]').fill(`${runPrefix}_SRC`);
  await dialog.locator('input[placeholder="简要描述变更内容"]').fill(title);
  await chooseRadixOption(page, dialog, "选择变更类型", "设计变更");
  await dialog.locator("textarea").fill(`${runPrefix} 设计评审后发现治具定位结构需要调整，触发工程变更。`);
  await dialog.locator('input[placeholder="输入项目 ID 后按回车添加"]').fill(String(projectId));
  await dialog.locator('input[placeholder="输入项目 ID 后按回车添加"]').press("Enter");
  await dialog.getByText(`项目 ${projectId}`).waitFor({ state: "visible", timeout: 8000 });

  const createResponse = await waitForApi(page, "POST", "/api/v1/ecns", async () => {
    await dialog.getByRole("button", { name: /^创建$/ }).click();
  });
  await dialog.waitFor({ state: "hidden", timeout: 10000 });
  await waitQuiet(page, 900);

  const ecn = unwrap(createResponse.json);
  if (!ecn.id) {
    throw new Error(`ECN 创建未返回 id: ${createResponse.body.slice(0, 600)}`);
  }
  report.created.ecns.push({
    id: ecn.id,
    ecn_no: ecn.ecn_no,
    ecn_title: ecn.ecn_title,
    project_id: ecn.project_id,
  });
  await page.getByText(title).first().waitFor({ state: "visible", timeout: 10000 });
  return ecn;
};

const openEcnImpactViaUi = async (page, ecn) => {
  await gotoRoute(page, "/change-management/ecn-center?tab=management", 1000);
  await page.getByText(ecn.ecn_title).first().waitFor({ state: "visible", timeout: 10000 });

  const card = page.locator(".grid .rounded, .grid [class*=Card]").filter({ hasText: ecn.ecn_title }).first();
  const buttonScope = (await card.count()) ? card : page;
  await waitForApi(page, "GET", `/api/v1/ecns/${ecn.id}/bom-impact-summary`, async () => {
    await buttonScope.getByRole("button", { name: /影响分析/ }).first().click();
  });

  const dialog = page.getByRole("dialog", { name: /变更影响分析/ });
  await dialog.waitFor({ state: "visible", timeout: 10000 });
  await dialog.getByText(/变更影响分析/).first().waitFor({ state: "visible", timeout: 5000 });
  await dialog.getByRole("button", { name: /关闭/ }).first().click();
  await dialog.waitFor({ state: "hidden", timeout: 10000 });
  return { ecn_id: ecn.id };
};

const createAndDeleteEcnTypeViaUi = async (page) => {
  const typeCode = `QAENG${stamp.slice(-10)}`.slice(0, 20);
  const typeName = `${runPrefix}_类型`;
  await gotoRoute(page, "/change-management/ecn-center?tab=types", 1000);
  await page.getByText("ECN类型列表").waitFor({ state: "visible", timeout: 10000 });
  await page.getByRole("button", { name: /新建类型/ }).click();

  const dialog = page.getByRole("dialog", { name: /新建ECN类型/ });
  await dialog.waitFor({ state: "visible", timeout: 10000 });
  await dialog.locator('input[placeholder="如：DESIGN"]').fill(typeCode);
  await dialog.locator('input[placeholder="如：设计变更"]').fill(typeName);
  await dialog.locator("textarea").first().fill(`${runPrefix} 工程技术 QA 类型配置`);
  await dialog.getByRole("button", { name: "机械部" }).first().click();

  const createResponse = await waitForApi(page, "POST", "/api/v1/ecn-types", async () => {
    await dialog.getByRole("button", { name: /^保存$/ }).click();
  });
  await dialog.waitFor({ state: "hidden", timeout: 10000 });
  await waitQuiet(page, 800);
  const type = unwrap(createResponse.json);
  if (!type.id) {
    throw new Error(`ECN 类型创建未返回 id: ${createResponse.body.slice(0, 600)}`);
  }
  report.created.ecnTypes.push({ id: type.id, type_code: type.type_code, type_name: type.type_name });
  await page.getByText(typeCode).waitFor({ state: "visible", timeout: 10000 });

  const row = page.getByRole("row").filter({ hasText: typeCode }).first();
  await row.getByRole("button").last().click();
  const confirm = page.getByRole("dialog", { name: /确认删除/ });
  await confirm.waitFor({ state: "visible", timeout: 10000 });
  await waitForApi(page, "DELETE", `/api/v1/ecn-types/${type.id}`, async () => {
    await confirm.getByRole("button", { name: /^删除$/ }).click();
  });
  await waitQuiet(page, 800);
  report.created.ecnTypes[report.created.ecnTypes.length - 1].deleted = true;
  return type;
};

const visitEcnStatistics = async (page) => {
  await gotoRoute(page, "/change-management/ecn-center?tab=statistics", 1000);
  await page.getByText(/ECN统计|统计概览|ECN总数/).first().waitFor({ state: "visible", timeout: 12000 });
  await waitQuiet(page, 800);
  return { route: "/change-management/ecn-center?tab=statistics" };
};

const createTechnicalReviewViaUi = async (page, project, users) => {
  const reviewName = `${runPrefix}_详细设计评审`;
  await gotoRoute(page, `/technical-reviews?project_id=${project.id}`, 1000);
  await page.getByText("技术评审管理").first().waitFor({ state: "visible", timeout: 10000 });
  await page.getByRole("button", { name: /创建技术评审|创建第一个技术评审/ }).first().click();
  await page.waitForURL((url) => new URL(url).pathname === "/technical-reviews/new", { timeout: 10000 });
  await waitQuiet(page, 1000);
  await page.getByText("创建技术评审").first().waitFor({ state: "visible", timeout: 10000 });

  await page.locator('select[name="review_type"]').selectOption("DDR");
  await page.locator('input[placeholder="请输入评审名称"]').fill(reviewName);
  await page.locator('select[name="project_id"]').selectOption(String(project.id));
  await page.locator('input[type="datetime-local"]').fill("2026-07-08T10:30");
  await page.locator('input[placeholder="请输入评审地点"]').fill("三楼工程评审室");
  await page.locator('select[name="meeting_type"]').selectOption("ONSITE");
  await page.locator('select[name="host_id"]').selectOption(String(users[0].id));
  await page.locator('select[name="presenter_id"]').selectOption(String(users[1]?.id || users[0].id));
  await page.locator('select[name="recorder_id"]').selectOption(String(users[2]?.id || users[0].id));

  const createResponse = await waitForApi(page, "POST", "/api/v1/technical-reviews", async () => {
    await page.getByRole("button", { name: /^保存$/ }).click();
  });
  await page.waitForURL((url) => new URL(url).pathname === "/technical-reviews", { timeout: 10000 });
  await waitQuiet(page, 1000);

  const review = unwrap(createResponse.json);
  if (!review.id) {
    throw new Error(`技术评审创建未返回 id: ${createResponse.body.slice(0, 600)}`);
  }
  report.created.technicalReviews.push({
    id: review.id,
    review_no: review.review_no,
    review_name: review.review_name,
    project_id: review.project_id,
  });
  await page.getByText(reviewName).first().waitFor({ state: "visible", timeout: 10000 });
  return review;
};

const addTechnicalReviewChildrenViaUi = async (page, review, users) => {
  await gotoRoute(page, `/technical-reviews/${review.id}`, 1000);
  await page.getByText(`技术评审 - ${review.review_name}`).first().waitFor({ state: "visible", timeout: 10000 });

  await clickReviewDetailTab(page, "参与人");
  await page.getByRole("button", { name: /添加参与人/ }).click();
  let dialog = page.getByRole("dialog", { name: /添加评审参与人/ });
  await dialog.waitFor({ state: "visible", timeout: 10000 });
  await dialog.locator("select").first().selectOption(String(users[3]?.id || users[0].id));
  await dialog.locator("select").nth(1).selectOption("expert");
  let apiResponse = await waitForApi(page, "POST", `/api/v1/technical-reviews/${review.id}/participants`, async () => {
    await dialog.getByRole("button", { name: /添加参与人/ }).click();
  });
  let created = unwrap(apiResponse.json);
  report.created.reviewParticipants.push({ id: created.id, review_id: review.id, user_id: created.user_id });
  await page.getByText("待确认").first().waitFor({ state: "visible", timeout: 10000 });

  await clickReviewDetailTab(page, "材料");
  await page.getByRole("button", { name: /上传材料/ }).click();
  dialog = page.getByRole("dialog", { name: /登记评审材料/ });
  await dialog.waitFor({ state: "visible", timeout: 10000 });
  await dialog.locator("select").first().selectOption("bom");
  await dialog.locator("input").nth(0).fill(`${runPrefix}_BOM评审包`);
  await dialog.locator("input").nth(1).fill(`/qa/${runPrefix}/bom-review.xlsx`);
  await dialog.locator('input[type="number"]').fill("204800");
  await dialog.locator("label").filter({ hasText: "版本号" }).locator("input").fill("V1.0");
  apiResponse = await waitForApi(page, "POST", `/api/v1/technical-reviews/${review.id}/materials`, async () => {
    await dialog.getByRole("button", { name: /登记材料/ }).click();
  });
  created = unwrap(apiResponse.json);
  report.created.reviewMaterials.push({ id: created.id, review_id: review.id, material_name: created.material_name });
  await page.getByText(`${runPrefix}_BOM评审包`).waitFor({ state: "visible", timeout: 10000 });

  await clickReviewDetailTab(page, "检查项");
  await page.getByRole("button", { name: /添加检查项/ }).click();
  dialog = page.getByRole("dialog", { name: /添加检查项/ });
  await dialog.waitFor({ state: "visible", timeout: 10000 });
  await dialog.locator("input").first().fill("设计完整性");
  await dialog.locator("textarea").first().fill(`${runPrefix} 图纸、BOM、测试方案三方一致`);
  await dialog.locator("select").nth(2).selectOption(String(users[0].id));
  await dialog.locator("textarea").last().fill(`${runPrefix} 检查通过`);
  apiResponse = await waitForApi(page, "POST", `/api/v1/technical-reviews/${review.id}/checklist-records`, async () => {
    await dialog.getByRole("button", { name: /添加检查项/ }).click();
  });
  created = unwrap(apiResponse.json);
  report.created.reviewChecklistRecords.push({ id: created.id, review_id: review.id, category: created.category });
  await page.getByText(`${runPrefix} 图纸、BOM、测试方案三方一致`).waitFor({ state: "visible", timeout: 10000 });

  await clickReviewDetailTab(page, "问题");
  await page.getByRole("button", { name: /创建问题/ }).click();
  dialog = page.getByRole("dialog", { name: /创建评审问题/ });
  await dialog.waitFor({ state: "visible", timeout: 10000 });
  await dialog.locator("select").first().selectOption("B");
  await dialog.locator("input").first().fill("结构设计");
  await dialog.locator("textarea").nth(0).fill(`${runPrefix} 治具定位销公差需复核`);
  await dialog.locator("textarea").nth(1).fill(`${runPrefix} 由机械工程师补充计算并更新图纸`);
  await dialog.locator("select").nth(1).selectOption(String(users[1]?.id || users[0].id));
  await dialog.locator('input[type="date"]').fill("2026-07-15");
  apiResponse = await waitForApi(page, "POST", `/api/v1/technical-reviews/${review.id}/issues`, async () => {
    await dialog.getByRole("button", { name: /提交问题/ }).click();
  });
  created = unwrap(apiResponse.json);
  report.created.reviewIssues.push({ id: created.id, review_id: review.id, issue_no: created.issue_no });
  await page.getByText(`${runPrefix} 治具定位销公差需复核`).waitFor({ state: "visible", timeout: 10000 });

  return {
    participants: report.created.reviewParticipants.length,
    materials: report.created.reviewMaterials.length,
    checklistRecords: report.created.reviewChecklistRecords.length,
    issues: report.created.reviewIssues.length,
  };
};

const verifyEngineeringData = async (page, project, ecn, review) => {
  const ecnDetail = unwrap(await browserApi(page, "GET", `/ecns/${ecn.id}`));
  if (ecnDetail.project_id !== project.id) {
    throw new Error(`ECN project_id 不匹配: ${ecnDetail.project_id} !== ${project.id}`);
  }

  const reviewDetail = unwrap(await browserApi(page, "GET", `/technical-reviews/${review.id}`));
  if (reviewDetail.project_id !== project.id) {
    throw new Error(`技术评审 project_id 不匹配: ${reviewDetail.project_id} !== ${project.id}`);
  }
  if ((reviewDetail.participants || []).length < 1) throw new Error("技术评审参与人未落库");
  if ((reviewDetail.materials || []).length < 1) throw new Error("技术评审材料未落库");
  if ((reviewDetail.checklist_records || []).length < 1) throw new Error("技术评审检查项未落库");
  if ((reviewDetail.issues || []).length < 1) throw new Error("技术评审问题未落库");

  const ecnList = listItems(await browserApi(page, "GET", `/ecns?page=1&page_size=20&keyword=${encodeURIComponent(ecn.ecn_title)}`));
  const reviewList = listItems(
    await browserApi(page, "GET", `/technical-reviews?page=1&page_size=20&keyword=${encodeURIComponent(review.review_name)}`),
  );
  if (!ecnList.some((item) => item.id === ecn.id)) throw new Error("ECN 列表无法检索到本轮记录");
  if (!reviewList.some((item) => item.id === review.id)) throw new Error("技术评审列表无法检索到本轮记录");

  return {
    ecn: ecnDetail.id,
    review: reviewDetail.id,
    participants: reviewDetail.participants.length,
    materials: reviewDetail.materials.length,
    checklistRecords: reviewDetail.checklist_records.length,
    issues: reviewDetail.issues.length,
  };
};

const shellSql = (sql, args = []) =>
  execFileSync("sqlite3", [DB_PATH, ...args, sql], { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] });

const idsOf = (items) => items.map((item) => Number(item.id)).filter(Number.isInteger);

const fkReferences = (targetTable) =>
  shellSql(
    `select m.name || '|' || fk.'from' from sqlite_master m, pragma_foreign_key_list(m.name) fk where fk.'table'='${targetTable}' order by m.name;`,
  )
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [table, column] = line.split("|");
      return { table, column };
    });

const cleanupCreatedData = () => {
  const projectIds = idsOf(report.created.projects);
  const ecnIds = idsOf(report.created.ecns);
  const ecnTypeIds = idsOf(report.created.ecnTypes.filter((item) => !item.deleted));
  const reviewIds = idsOf(report.created.technicalReviews);
  const statements = ["PRAGMA foreign_keys=OFF;"];

  if (reviewIds.length) {
    const reviewList = reviewIds.join(",");
    statements.push(`DELETE FROM issues WHERE project_id IN (${projectIds.join(",") || "NULL"}) AND issue_type='TECHNICAL_REVIEW';`);
    for (const { table, column } of fkReferences("technical_reviews")) {
      if (table === "technical_reviews") continue;
      statements.push(`DELETE FROM "${table}" WHERE "${column}" IN (${reviewList});`);
    }
    statements.push(`DELETE FROM technical_reviews WHERE id IN (${reviewList});`);
  }

  if (ecnIds.length) {
    const ecnList = ecnIds.join(",");
    for (const { table, column } of fkReferences("ecn")) {
      if (table === "ecn") continue;
      statements.push(`DELETE FROM "${table}" WHERE "${column}" IN (${ecnList});`);
    }
    statements.push(`DELETE FROM ecn WHERE id IN (${ecnList});`);
  }

  if (ecnTypeIds.length) {
    statements.push(`DELETE FROM ecn_types WHERE id IN (${ecnTypeIds.join(",")});`);
  }

  if (projectIds.length) {
    const projectList = projectIds.join(",");
    for (const { table, column } of fkReferences("projects")) {
      if (table === "projects") continue;
      statements.push(`DELETE FROM "${table}" WHERE "${column}" IN (${projectList});`);
    }
    statements.push(`DELETE FROM projects WHERE id IN (${projectList});`);
  }

  statements.push("PRAGMA foreign_keys=ON;");
  shellSql(statements.join("\n"));

  for (const item of report.created.projects) item.deleted = true;
  for (const item of report.created.ecns) item.deleted = true;
  for (const item of report.created.ecnTypes) item.deleted = true;
  for (const item of report.created.technicalReviews) item.deleted = true;
  for (const item of report.created.reviewParticipants) item.deleted = true;
  for (const item of report.created.reviewMaterials) item.deleted = true;
  for (const item of report.created.reviewChecklistRecords) item.deleted = true;
  for (const item of report.created.reviewIssues) item.deleted = true;
  report.cleanup.push({ type: "sqlite", status: "deleted", projectIds, ecnIds, ecnTypeIds, reviewIds });
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
        body: (await response.text().catch(() => "")).slice(0, 1000),
      });
    }
  });
  page.on("dialog", async (dialog) => {
    report.dialogs.push({ type: dialog.type(), message: dialog.message(), url: page.url() });
    await dialog.accept().catch(() => {});
  });

  let project;
  let users = [];
  let ecn;
  let review;
  let reportFile = "";

  try {
    await ensureAuthenticated(page);
    await runStep(page, "工程技术-准备载体项目和用户", async () => {
      project = await createSupportProjectViaApi(page);
      users = await getActiveUsers(page);
      return { project_id: project.id, userCount: users.length };
    });
    if (project?.id) {
      await runStep(page, "ECN中心-UI新建工程变更", async () => {
        ecn = await createEcnViaUi(page, project.id);
        return ecn;
      });
      if (ecn?.id) {
        await runStep(page, "ECN中心-UI查看影响分析", () => openEcnImpactViaUi(page, ecn));
      }
      await runStep(page, "ECN中心-类型配置创建删除", () => createAndDeleteEcnTypeViaUi(page));
      await runStep(page, "ECN中心-统计页导航", () => visitEcnStatistics(page));
      await runStep(page, "技术评审-UI创建评审", async () => {
        review = await createTechnicalReviewViaUi(page, project, users);
        return review;
      });
      if (review?.id) {
        await runStep(page, "技术评审-UI添加参与人材料检查项问题", () =>
          addTechnicalReviewChildrenViaUi(page, review, users),
        );
        await runStep(page, "工程技术-下游数据API复核", () => verifyEngineeringData(page, project, ecn, review));
      }
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
