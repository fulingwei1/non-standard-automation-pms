import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";

const require = createRequire(new URL("../../frontend/package.json", import.meta.url));
const { chromium, request } = require("playwright");

const ROOT = "http://127.0.0.1:5173";
const API = "http://127.0.0.1:8002/api/v1";
const USERNAME = process.env.QA_USER || "admin";
const PASSWORD = process.env.QA_PASSWORD || "admin123";
const stamp = new Date().toISOString().replace(/[-:TZ.]/g, "").slice(0, 14);
const projectCode = `QA_BTN_${stamp}`;
const projectName = `按钮级流程验证 ${stamp}`;
const reportDir = path.resolve(".gstack/qa-reports");
const screenshotDir = path.join(reportDir, "screenshots");
fs.mkdirSync(screenshotDir, { recursive: true });

const report = {
  stamp,
  projectCode,
  projectName,
  projectId: null,
  costId: null,
  stageCount: null,
  steps: [],
  console: [],
  pageErrors: [],
  requestFailures: [],
  apiErrors: [],
  screenshots: [],
  cleanup: null,
};

const recordStep = (name, extra = {}) => {
  report.steps.push({ name, at: new Date().toISOString(), ...extra });
  console.log(`[step] ${name}`);
};

const fail = (name, error) => {
  const message = error?.stack || error?.message || String(error);
  report.steps.push({ name, at: new Date().toISOString(), error: message });
  throw error;
};

const expectNoHardErrors = (label) => {
  if (report.pageErrors.length || report.requestFailures.length || report.apiErrors.length) {
    throw new Error(`${label} captured hard errors: ${JSON.stringify({
      pageErrors: report.pageErrors,
      requestFailures: report.requestFailures,
      apiErrors: report.apiErrors,
    }, null, 2)}`);
  }
};

const saveScreenshot = async (page, name) => {
  const file = path.join(screenshotDir, `${name}-${stamp}.png`);
  await page.screenshot({ path: file, fullPage: true });
  report.screenshots.push(file);
};

const login = async (apiContext) => {
  const res = await apiContext.post(`${API}/auth/login`, {
    form: { username: USERNAME, password: PASSWORD },
  });
  if (!res.ok()) {
    throw new Error(`login failed ${res.status()} ${await res.text()}`);
  }
  const payload = await res.json();
  if (!payload.access_token) {
    throw new Error(`login response missing access_token: ${JSON.stringify(payload)}`);
  }
  return payload;
};

const apiGetJson = async (apiContext, token, url) => {
  const res = await apiContext.get(`${API}${url}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok()) {
    throw new Error(`GET ${url} failed ${res.status()} ${await res.text()}`);
  }
  return res.json();
};

const getTimelineData = async (apiContext, token) => (
  apiGetJson(apiContext, token, `/projects/${report.projectId}/stages/views/timeline?include_nodes=true`)
);

const findCreatedProject = async (apiContext, token) => {
  const payload = await apiGetJson(apiContext, token, `/projects/?keyword=${encodeURIComponent(projectCode)}&page_size=20`);
  const items = payload.items || payload.data?.items || payload || [];
  const project = items.find((item) => item.project_code === projectCode);
  if (!project?.id) {
    throw new Error(`created project not found via keyword: ${JSON.stringify(payload).slice(0, 1000)}`);
  }
  report.projectId = project.id;
  return project;
};

const cleanupProject = async (apiContext, token) => {
  if (!report.projectId) {
    return;
  }
  const cleanup = {};
  if (report.costId) {
    const costRes = await apiContext.delete(`${API}/projects/${report.projectId}/costs/${report.costId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    cleanup.cost = {
      costId: report.costId,
      status: costRes.status(),
      body: await costRes.text(),
    };
  }
  const res = await apiContext.delete(`${API}/projects/${report.projectId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  report.cleanup = {
    ...cleanup,
    projectId: report.projectId,
    status: res.status(),
    body: await res.text(),
  };
};

const setAuthStorage = async (page, tokens) => {
  await page.goto(ROOT, { waitUntil: "domcontentloaded" });
  await page.evaluate(({ access, refresh, username }) => {
    localStorage.setItem("token", access);
    localStorage.setItem("refresh_token", refresh || "");
    localStorage.setItem("user", JSON.stringify({
      id: 15,
      username,
      real_name: "管理员",
      role: "admin",
      is_superuser: true,
    }));
  }, {
    access: tokens.access_token,
    refresh: tokens.refresh_token,
    username: USERNAME,
  });
};

const clickButton = async (page, name, options = {}) => {
  const button = page.getByRole("button", { name }).first();
  await button.waitFor({ state: "visible", timeout: options.timeout || 15000 });
  await button.click();
};

const fillByPlaceholder = async (page, placeholder, value) => {
  const input = page.getByPlaceholder(placeholder).first();
  await input.waitFor({ state: "visible", timeout: 15000 });
  await input.fill(value);
};

const fillInDialogByPlaceholder = async (page, placeholder, value) => {
  const dialog = page.getByRole("dialog").last();
  const input = dialog.getByPlaceholder(placeholder).first();
  await input.waitFor({ state: "visible", timeout: 15000 });
  await input.fill(value);
};

const fillFirstInputAfterText = async (page, labelText, value) => {
  const locator = page.locator(`text=${labelText}`).locator("..").locator("input").first();
  await locator.waitFor({ state: "visible", timeout: 15000 });
  await locator.fill(value);
};

const chooseFirstSelectOption = async (page, labelText) => {
  const wrapper = page.locator(`text=${labelText}`).locator("..").locator('[role="combobox"], button').first();
  await wrapper.waitFor({ state: "visible", timeout: 15000 });
  await wrapper.click();
  const option = page.locator('[role="option"]').filter({ hasNotText: /选择|请选择/ }).first();
  await option.waitFor({ state: "visible", timeout: 15000 });
  await option.click();
};

const createProjectViaUi = async (page) => {
  recordStep("open project center");
  await page.goto(`${ROOT}/project/management-center?tab=board&view=card`, { waitUntil: "networkidle" });
  await clickButton(page, "新建项目");
  await page.getByRole("heading", { name: "新建项目" }).waitFor({ state: "visible", timeout: 15000 });

  recordStep("fill project basic step");
  const createDialog = page.getByRole("dialog").last();
  const stageTemplateOption = createDialog
    .locator(".cursor-pointer")
    .filter({ hasText: /个阶段|阶段|模板|TEMP|STANDARD|NO_/ })
    .first();
  await stageTemplateOption.waitFor({ state: "visible", timeout: 15000 }).catch(() => {});
  if (await stageTemplateOption.count()) {
    await stageTemplateOption.click();
    recordStep("selected stage template");
  } else {
    recordStep("stage template option not available");
  }
  await fillByPlaceholder(page, "例如: PJ260104001", projectCode);
  await fillByPlaceholder(page, "请输入项目全称", projectName);
  await fillByPlaceholder(page, "项目简称（可选）", `按钮流${stamp.slice(-4)}`);
  const product = page.getByPlaceholder("例如: ICT测试设备").first();
  if (await product.count()) {
    await product.fill("ICT测试设备");
  }
  await clickButton(page, "下一步");

  recordStep("fill customer step");
  await page.getByText("客户信息", { exact: true }).waitFor({ state: "visible", timeout: 15000 });
  await fillInDialogByPlaceholder(page, "搜索客户名称或编码", "");
  await fillInDialogByPlaceholder(page, "搜索客户名称或编码", "客户");
  const dialog = page.getByRole("dialog").last();
  const customerOption = dialog.locator(".max-h-48 .cursor-pointer").first();
  await customerOption.waitFor({ state: "visible", timeout: 15000 });
  await customerOption.click();
  await clickButton(page, "下一步");

  recordStep("fill finance step");
  await fillFirstInputAfterText(page, "合同金额", "100000");
  await fillFirstInputAfterText(page, "预算金额", "80000");
  const pmCombobox = page.locator("text=项目经理").locator("..").locator('[role="combobox"], button, select').first();
  if (await pmCombobox.count()) {
    const tag = await pmCombobox.evaluate((el) => el.tagName.toLowerCase()).catch(() => "");
    if (tag === "select") {
      await pmCombobox.selectOption({ index: 1 }).catch(async () => {});
    } else {
      await pmCombobox.click();
      const option = page.locator('[role="option"]').first();
      await option.waitFor({ state: "visible", timeout: 15000 }).catch(async () => {});
      if (await option.count()) {
        await option.click();
      }
    }
  }
  await clickButton(page, "下一步");

  recordStep("fill schedule step and submit project");
  await fillFirstInputAfterText(page, "计划开始日期", "2026-07-01");
  await fillFirstInputAfterText(page, "计划结束日期", "2026-08-31");
  await clickButton(page, "创建项目");
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(1000);
};

const addMemberViaUi = async (page) => {
  recordStep("add project member via detail button");
  await page.goto(`${ROOT}/projects/${report.projectId}`, { waitUntil: "networkidle" });
  await clickButton(page, "添加成员");
  await page.getByText("添加项目成员", { exact: true }).waitFor({ state: "visible", timeout: 15000 });
  const dialog = page.getByRole("dialog").last();
  const select = dialog.locator("select").filter({ hasText: "-- 选择用户 --" }).first();
  await select.waitFor({ state: "visible", timeout: 15000 });
  const selectHandle = await select.elementHandle();
  await page.waitForFunction((el) => !el.disabled && el.options.length > 1, selectHandle, { timeout: 15000 });
  const optionCount = await select.locator("option").count();
  if (optionCount < 2) {
    recordStep("skip add member no available users");
    await dialog.getByRole("button", { name: "取消" }).click();
    return;
  }
  const optionValue = await select.locator("option").nth(1).getAttribute("value");
  await select.selectOption(optionValue);
  await page.waitForFunction((el) => Boolean(el.value), selectHandle, { timeout: 5000 });
  const addButton = dialog.getByRole("button", { name: "添加" });
  const addHandle = await addButton.elementHandle();
  await page.waitForFunction((el) => !el.disabled, addHandle, { timeout: 5000 });
  await addButton.click();
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(800);
};

const recordStageCount = async (apiContext, token) => {
  const timeline = await getTimelineData(apiContext, token);
  report.stageCount = Array.isArray(timeline.stages) ? timeline.stages.length : null;
  recordStep("record created stage instances", { stageCount: report.stageCount });
};

const openProjectTimelineViaUi = async (page) => {
  await page.goto(`${ROOT}/project/management-center?tab=board&view=card`, { waitUntil: "networkidle" });
  const allProjects = page.getByRole("button", { name: "全部项目" }).first();
  if (await allProjects.count()) {
    await allProjects.click();
  }
  await fillByPlaceholder(page, "搜索项目编号、名称...", projectCode).catch(async () => {});
  await page.getByText(projectCode).first().waitFor({ state: "visible", timeout: 20000 });
  await page.getByText(projectCode).first().click();
  await page.getByText("时间轴视图").first().click();
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(1000);
};

const waitForStageStatus = async (apiContext, token, stageId, expectedStatus) => {
  const deadline = Date.now() + 10000;
  let latestStage = null;
  while (Date.now() < deadline) {
    const timeline = await getTimelineData(apiContext, token);
    latestStage = timeline.stages?.find((stage) => stage.id === stageId);
    if (latestStage?.status === expectedStatus) {
      return latestStage;
    }
    await new Promise((resolve) => setTimeout(resolve, 300));
  }
  throw new Error(`stage ${stageId} did not reach ${expectedStatus}; latest=${JSON.stringify(latestStage)}`);
};

const createTaskViaUi = async (page) => {
  recordStep("create project task via button");
  await page.goto(`${ROOT}/projects/${report.projectId}/tasks`, { waitUntil: "networkidle" });
  await clickButton(page, "新建任务");
  await page.getByRole("heading", { name: "新建任务" }).waitFor({ state: "visible", timeout: 15000 });
  await fillByPlaceholder(page, "请输入任务名称", `按钮流任务 ${stamp}`);
  await fillFirstInputAfterText(page, "计划开始日期", "2026-07-02");
  await fillFirstInputAfterText(page, "计划结束日期", "2026-07-10");
  await fillByPlaceholder(page, "0", "20");
  await fillByPlaceholder(page, "任务描述", "按钮级流程自动验证任务");
  await clickButton(page, "创建");
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(800);
};

const createCostViaUi = async (page, apiContext, token) => {
  recordStep("create project cost via button");
  const description = `按钮流成本 ${stamp}`;
  await page.goto(`${ROOT}/costs?project_id=${report.projectId}`, { waitUntil: "networkidle" });
  await page.getByText("成本核算", { exact: true }).first().waitFor({ state: "visible", timeout: 15000 });
  await clickButton(page, "录入成本");

  const dialog = page.getByRole("dialog").last();
  await dialog.getByText("录入项目成本记录", { exact: true }).waitFor({ state: "visible", timeout: 15000 });
  const selects = dialog.locator("select");
  await selects.nth(0).selectOption(String(report.projectId));
  await selects.nth(1).selectOption("MATERIAL");
  await dialog.getByPlaceholder("请输入金额").fill("1234.56");
  await dialog.locator('input[type="date"]').fill("2026-07-03");
  await dialog.getByPlaceholder("请输入成本描述...").fill(description);

  const costResponse = page.waitForResponse((res) => (
    res.url().includes(`/projects/${report.projectId}/costs/`) &&
    res.request().method() === "POST"
  ), { timeout: 15000 });
  await dialog.getByRole("button", { name: "保存" }).click();
  const costResult = await costResponse;
  if (!costResult.ok()) {
    throw new Error(`cost create failed ${costResult.status()} ${await costResult.text()}`);
  }

  const costs = await apiGetJson(apiContext, token, `/projects/${report.projectId}/costs/`);
  const items = costs.items || costs.data?.items || costs || [];
  const createdCost = items.find((cost) => cost.description === description);
  if (!createdCost?.id) {
    throw new Error(`created cost not found: ${JSON.stringify(costs).slice(0, 1000)}`);
  }
  report.costId = createdCost.id;
  recordStep("project cost created via UI", {
    costId: createdCost.id,
    amount: Number(createdCost.amount),
    costType: createdCost.cost_type,
  });
};

const runStageActionsViaUi = async (page, apiContext, token) => {
  recordStep("start and complete first available stage via timeline");
  const timelineBefore = await getTimelineData(apiContext, token);
  const targetStage = timelineBefore.stages?.find((stage) => stage.status === "PENDING");
  if (!targetStage) {
    throw new Error(`no pending stage available: ${JSON.stringify(timelineBefore).slice(0, 1000)}`);
  }

  await openProjectTimelineViaUi(page);

  const start = page.getByRole("button", { name: /^开始$/ }).first();
  await start.waitFor({ state: "visible", timeout: 15000 });
  const startResponse = page.waitForResponse((res) => (
    res.url().includes(`/projects/${report.projectId}/stages/`) &&
    res.url().includes("/start") &&
    res.request().method() === "POST"
  ), { timeout: 15000 });
  await start.click();
  const startResult = await startResponse;
  if (!startResult.ok()) {
    throw new Error(`stage start failed ${startResult.status()} ${await startResult.text()}`);
  }
  const startedStage = await waitForStageStatus(apiContext, token, targetStage.id, "IN_PROGRESS");
  recordStep("stage started via UI", {
    stageId: startedStage.id,
    stageCode: startedStage.stage_code,
    stageName: startedStage.stage_name,
  });

  await openProjectTimelineViaUi(page);
  const complete = page.getByRole("button", { name: /^完成$/ }).first();
  await complete.waitFor({ state: "visible", timeout: 15000 });
  const completeResponse = page.waitForResponse((res) => (
    res.url().includes(`/projects/${report.projectId}/stages/`) &&
    res.url().includes("/complete") &&
    res.request().method() === "POST"
  ), { timeout: 15000 });
  await complete.click();
  const completeResult = await completeResponse;
  if (!completeResult.ok()) {
    throw new Error(`stage complete failed ${completeResult.status()} ${await completeResult.text()}`);
  }
  const completedStage = await waitForStageStatus(apiContext, token, targetStage.id, "COMPLETED");
  recordStep("stage completed via UI", {
    stageId: completedStage.id,
    stageCode: completedStage.stage_code,
    stageName: completedStage.stage_name,
  });
};

const createDeliveryScheduleViaUi = async (page) => {
  recordStep("create delivery schedule via button");
  await page.goto(`${ROOT}/projects/${report.projectId}/delivery/create`, { waitUntil: "networkidle" });
  await page.getByText("创建项目交付排产计划", { exact: true }).waitFor({ state: "visible", timeout: 15000 });
  await fillByPlaceholder(page, "如：ICT 测试机台项目交付排产计划", `按钮流交付计划 ${stamp}`);
  const projectIdInput = page.locator('input[type="number"]').nth(1);
  await projectIdInput.fill(String(report.projectId));
  page.once("dialog", async (dialog) => {
    report.steps.push({ name: "delivery schedule dialog", message: dialog.message(), at: new Date().toISOString() });
    await dialog.accept();
  });
  await clickButton(page, "创建排产计划");
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(800);
};

const main = async () => {
  const apiContext = await request.newContext();
  const tokens = await login(apiContext);
  let browser;
  try {
    browser = await chromium.launch({ headless: true });
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });

    page.on("console", (msg) => {
      const text = msg.text();
      if (["error", "warning"].includes(msg.type()) && !text.includes("[API请求]")) {
        report.console.push({ type: msg.type(), text });
      }
    });
    page.on("pageerror", (err) => report.pageErrors.push(err.message));
    page.on("requestfailed", (req) => {
      const url = req.url();
      if (url.includes("rsms.me/inter/font-files/")) {
        return;
      }
      if (req.failure()?.errorText === "net::ERR_ABORTED") {
        return;
      }
      report.requestFailures.push({
        method: req.method(),
        url,
        failure: req.failure()?.errorText,
      });
    });
    page.on("response", (res) => {
      const url = res.url();
      const status = res.status();
      if (url.includes("/api/") && status >= 400) {
        report.apiErrors.push({ method: res.request().method(), url, status });
      }
    });

    await setAuthStorage(page, tokens);
    await createProjectViaUi(page);
    await findCreatedProject(apiContext, tokens.access_token);
    await recordStageCount(apiContext, tokens.access_token);
    await addMemberViaUi(page);
    await createTaskViaUi(page);
    await createCostViaUi(page, apiContext, tokens.access_token);
    await runStageActionsViaUi(page, apiContext, tokens.access_token);
    await createDeliveryScheduleViaUi(page);
    await saveScreenshot(page, "project-button-flow-final");
    expectNoHardErrors("project button flow");
  } catch (error) {
    report.error = error?.stack || error?.message || String(error);
    if (browser) {
      const pages = browser.contexts().flatMap((context) => context.pages());
      if (pages[0]) {
        await saveScreenshot(pages[0], "project-button-flow-failure").catch(() => {});
      }
    }
    throw error;
  } finally {
    await cleanupProject(apiContext, tokens.access_token).catch((error) => {
      report.cleanup = { error: error?.stack || error?.message || String(error) };
    });
    await browser?.close();
    await apiContext.dispose();
    const reportPath = path.join(reportDir, `project-button-flow-${stamp}.json`);
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
    console.log(`[report] ${reportPath}`);
    console.log(JSON.stringify({
      projectId: report.projectId,
      steps: report.steps.length,
      apiErrors: report.apiErrors,
      pageErrors: report.pageErrors,
      requestFailures: report.requestFailures,
      cleanup: report.cleanup,
      screenshots: report.screenshots,
      error: report.error,
    }, null, 2));
  }
};

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
