import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { createRequire } from "node:module";

const require = createRequire(new URL("../../frontend/package.json", import.meta.url));
const { chromium } = require("playwright");

const ROOT = process.env.QA_ROOT || "http://127.0.0.1:5173";
const DB_PATH = process.env.QA_DB_PATH || "data/app.db";
const USERNAME = process.env.QA_USER || "admin";
const PASSWORD = process.env.QA_PASSWORD || "admin123";
const ADMIN_ID = 15;
const headless = process.env.QA_HEADLESS !== "0";
const stamp = new Date().toISOString().replace(/[-:TZ.]/g, "").slice(0, 14);
const runPrefix = `QA_ACCEPT_${stamp}`;
const reportDir = path.resolve(".gstack/qa-reports");
const screenshotDir = path.join(reportDir, "screenshots");
fs.mkdirSync(screenshotDir, { recursive: true });

const report = {
  stamp,
  runPrefix,
  root: ROOT,
  dbPath: DB_PATH,
  headless,
  steps: [],
  created: {
    customers: [],
    projects: [],
    machines: [],
    templates: [],
    categories: [],
    templateItems: [],
    orders: [],
    orderItems: [],
    issues: [],
  },
  cleanup: [],
  console: [],
  pageErrors: [],
  requestFailures: [],
  dialogs: [],
  screenshots: [],
};

const reportFile = () => path.join(reportDir, `acceptance-management-sweep-${stamp}.json`);
const writeReport = () => {
  const file = reportFile();
  fs.writeFileSync(file, JSON.stringify(report, null, 2));
  return file;
};

const dbExec = (sql) =>
  execFileSync("sqlite3", ["-cmd", ".timeout 5000", DB_PATH, sql], {
    encoding: "utf8",
  }).trim();

const dbValue = (sql) => dbExec(sql).split("\n").filter(Boolean).at(-1) || "";

const sqlList = (ids) => (ids.length ? ids.join(",") : "NULL");

const cleanupCreated = () => {
  const sql = `
    PRAGMA foreign_keys=OFF;
    DELETE FROM issue_follow_ups
      WHERE issue_id IN (
        SELECT id FROM acceptance_issues
        WHERE order_id IN (
          SELECT id FROM acceptance_orders WHERE project_id IN (${sqlList(report.created.projects)})
        )
      );
    DELETE FROM acceptance_issues
      WHERE order_id IN (
        SELECT id FROM acceptance_orders WHERE project_id IN (${sqlList(report.created.projects)})
      );
    DELETE FROM acceptance_order_items
      WHERE order_id IN (
        SELECT id FROM acceptance_orders WHERE project_id IN (${sqlList(report.created.projects)})
      );
    DELETE FROM acceptance_reports
      WHERE order_id IN (
        SELECT id FROM acceptance_orders WHERE project_id IN (${sqlList(report.created.projects)})
      );
    DELETE FROM acceptance_signatures
      WHERE order_id IN (
        SELECT id FROM acceptance_orders WHERE project_id IN (${sqlList(report.created.projects)})
      );
    DELETE FROM acceptance_orders WHERE project_id IN (${sqlList(report.created.projects)});
    DELETE FROM template_check_items WHERE category_id IN (${sqlList(report.created.categories)});
    DELETE FROM template_categories WHERE template_id IN (${sqlList(report.created.templates)});
    DELETE FROM acceptance_templates WHERE id IN (${sqlList(report.created.templates)});
    DELETE FROM machines WHERE id IN (${sqlList(report.created.machines)});
    DELETE FROM projects WHERE id IN (${sqlList(report.created.projects)}) AND project_code LIKE '${runPrefix}%';
    DELETE FROM customers WHERE id IN (${sqlList(report.created.customers)}) AND customer_code LIKE '${runPrefix}%';
  `;
  const output = dbExec(sql);
  report.cleanup.push({ at: new Date().toISOString(), output });
  writeReport();
};

const saveScreenshot = async (page, label) => {
  const safe = label.replace(/[^a-z0-9\u4e00-\u9fa5_-]+/gi, "_").slice(0, 100);
  const file = path.join(screenshotDir, `acceptance-${safe}-${stamp}.png`);
  await page.screenshot({ path: file, fullPage: true }).catch(() => {});
  report.screenshots.push(file);
  return file;
};

const waitQuiet = async (page, settleMs = 700) => {
  await page.waitForLoadState("networkidle", { timeout: 3500 }).catch(() => {});
  await page.waitForTimeout(settleMs);
};

const parseJson = (text) => {
  try {
    return text ? JSON.parse(text) : null;
  } catch {
    return null;
  }
};

const unwrap = (payload) => payload?.data?.data ?? payload?.data ?? payload ?? {};

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
    throw new Error(`${method} ${pattern} -> ${response.status()}: ${body.slice(0, 800)}`);
  }
  return { status: response.status(), body, json: parseJson(body) };
};

const runStep = async (page, name, fn) => {
  const step = { name, status: "running", startedAt: new Date().toISOString() };
  report.steps.push(step);
  console.log(`[step] ${name}`);
  try {
    step.result = await fn(page, step);
    step.status = "passed";
  } catch (error) {
    step.status = "failed";
    step.error = error?.stack || error?.message || String(error);
    step.screenshot = await saveScreenshot(page, `failed-${name}`);
    throw error;
  } finally {
    step.finishedAt = new Date().toISOString();
    writeReport();
  }
};

const login = async (page) => {
  const response = await fetch(`${ROOT}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ username: USERNAME, password: PASSWORD }),
  });
  if (!response.ok) {
    throw new Error(`登录接口失败：${response.status} ${await response.text()}`);
  }
  const data = await response.json();
  await page.goto(ROOT, { waitUntil: "domcontentloaded", timeout: 20000 });
  await page.evaluate((payload) => {
    localStorage.setItem("token", payload.access_token);
    if (payload.refresh_token) localStorage.setItem("refresh_token", payload.refresh_token);
  }, data);
};

const selectOption = async (page, comboName, optionName) => {
  await page.getByRole("combobox", { name: comboName }).click();
  await page.getByRole("option", { name: optionName }).click();
};

const setupData = () => {
  cleanupCreated();

  const customerCode = `${runPrefix}_CUST`;
  const projectCode = `${runPrefix}_PRJ`;
  const machineCode = `${runPrefix}_MC`;
  const templateCode = `${runPrefix}_SAT_TPL`;

  dbExec(`
    INSERT INTO customers (
      customer_code, customer_name, short_name, customer_type, industry,
      address, contact_person, contact_phone, status, created_by, is_active,
      created_at, updated_at
    ) VALUES (
      '${customerCode}', '${runPrefix} 客户', 'QA验收客户', 'enterprise', '自动化测试',
      '深圳市南山区 QA 验收地址', '验收客户代表', '13800000000',
      'ACTIVE', ${ADMIN_ID}, 1, datetime('now'), datetime('now')
    );
  `);
  const customerId = Number(dbValue(`SELECT id FROM customers WHERE customer_code='${customerCode}';`));
  report.created.customers.push(customerId);

  dbExec(`
    INSERT INTO projects (
      project_code, project_name, short_name, customer_id, customer_name,
      customer_contact, customer_phone, customer_address, project_type,
      contract_no, stage, status, health, is_active, is_archived, created_by,
      created_at, updated_at
    ) VALUES (
      '${projectCode}', '${runPrefix} 现场验收项目', 'QA验收项目',
      ${customerId}, '${runPrefix} 客户', '验收客户代表', '13800000000',
      '深圳市南山区 QA 验收地址', 'CUSTOM', '${runPrefix}_CONTRACT',
      'S7', 'ST01', 'H1', 1, 0, ${ADMIN_ID}, datetime('now'), datetime('now')
    );
  `);
  const projectId = Number(dbValue(`SELECT id FROM projects WHERE project_code='${projectCode}';`));
  report.created.projects.push(projectId);

  dbExec(`
    INSERT INTO machines (
      project_id, machine_code, machine_name, machine_no, stage, status, health,
      created_at, updated_at
    ) VALUES (
      ${projectId}, '${machineCode}', '${runPrefix} 现场验收设备', 1,
      'S7', 'ST01', 'H1', datetime('now'), datetime('now')
    );
  `);
  const machineId = Number(dbValue(`SELECT id FROM machines WHERE machine_code='${machineCode}';`));
  report.created.machines.push(machineId);

  dbExec(`
    INSERT INTO acceptance_templates (
      template_code, template_name, acceptance_type, equipment_type, version,
      description, is_system, is_active, created_by, created_at, updated_at
    ) VALUES (
      '${templateCode}', '${runPrefix} SAT验收模板', 'SAT', '非标自动化设备', '1.0',
      'QA SAT 现场验收模板', 0, 1, ${ADMIN_ID}, datetime('now'), datetime('now')
    );
  `);
  const templateId = Number(dbValue(`SELECT id FROM acceptance_templates WHERE template_code='${templateCode}';`));
  report.created.templates.push(templateId);

  dbExec(`
    INSERT INTO template_categories (
      template_id, category_code, category_name, weight, sort_order, is_required,
      description, created_at, updated_at
    ) VALUES (
      ${templateId}, 'SITE', '现场验收检查', 100, 1, 1,
      'QA 现场验收检查分类', datetime('now'), datetime('now')
    );
  `);
  const categoryId = Number(dbValue(`SELECT id FROM template_categories WHERE template_id=${templateId};`));
  report.created.categories.push(categoryId);

  dbExec(`
    INSERT INTO template_check_items (
      category_id, item_code, item_name, check_method, acceptance_criteria,
      standard_value, unit, is_required, is_key_item, sort_order,
      created_at, updated_at
    ) VALUES
      (${categoryId}, '${runPrefix}_ITEM1', 'QA 电气安全检查', '现场检测',
       '急停、接地、联锁保护正常', 'OK', '', 1, 1, 1, datetime('now'), datetime('now')),
      (${categoryId}, '${runPrefix}_ITEM2', 'QA 机构运行检查', '现场空跑',
       '机构运行平稳无异常噪声', 'OK', '', 1, 0, 2, datetime('now'), datetime('now'));
  `);
  const templateItemIds = dbExec(
    `SELECT id FROM template_check_items WHERE category_id=${categoryId} ORDER BY id;`,
  )
    .split("\n")
    .filter(Boolean)
    .map(Number);
  report.created.templateItems.push(...templateItemIds);

  dbExec(`
    INSERT INTO acceptance_orders (
      order_no, project_id, machine_id, acceptance_type, planned_date,
      actual_start_date, actual_end_date, location, status, total_items,
      passed_items, failed_items, na_items, pass_rate, overall_result,
      conclusion, created_by, created_at, updated_at
    ) VALUES (
      'FAT-${projectCode}-M01-001', ${projectId}, ${machineId}, 'FAT',
      '2035-01-20', datetime('now'), datetime('now'), 'QA 出厂验收区',
      'COMPLETED', 1, 1, 0, 0, 100, 'PASSED',
      'QA 前置 FAT 已通过', ${ADMIN_ID}, datetime('now'), datetime('now')
    );
  `);
  const fatOrderId = Number(dbValue(`SELECT id FROM acceptance_orders WHERE order_no='FAT-${projectCode}-M01-001';`));
  report.created.orders.push(fatOrderId);

  return {
    customerId,
    projectId,
    projectCode,
    machineId,
    machineCode,
    templateId,
    templateCode,
  };
};

let setupIds;
let satOrderId;
let satOrderNo;

const createSatAcceptanceViaUi = async (page) => {
  await page.goto(`${ROOT}/delivery/acceptance-center?tab=acceptance`, {
    waitUntil: "domcontentloaded",
    timeout: 20000,
  });
  await waitQuiet(page);
  await page.getByText("验收管理").first().waitFor({ state: "visible", timeout: 15000 });
  await page.getByRole("button", { name: /新建验收/ }).click();
  await page.getByText("新建验收记录").waitFor({ state: "visible", timeout: 10000 });

  await selectOption(page, "验收类型", "SAT - 现场验收测试");
  await selectOption(page, "选择项目", `${runPrefix} 现场验收项目`);
  await page.getByRole("combobox", { name: "关联设备" }).waitFor({ state: "visible", timeout: 10000 });
  await selectOption(page, "关联设备", `${runPrefix} 现场验收设备`);
  await selectOption(page, "检查模板", `${runPrefix} SAT验收模板`);
  await page.getByLabel("验收标题").fill(`${runPrefix} SAT现场验收`);
  await page.getByLabel("计划日期").fill("2035-02-01");
  await page.getByPlaceholder("例如：公司装配车间").fill("客户现场 QA 区");

  const response = await waitForApi(
    page,
    "POST",
    "/api/v1/acceptance/acceptance-orders",
    async () => {
      await page.getByRole("button", { name: /^创建$/ }).click();
    },
  );
  const order = unwrap(response.json);
  satOrderId = order.id;
  satOrderNo = order.order_no;
  if (!satOrderId || !satOrderNo) {
    throw new Error(`创建验收单响应缺少 id/order_no: ${JSON.stringify(response.json)}`);
  }
  report.created.orders.push(satOrderId);

  await page.getByText(satOrderNo).waitFor({ state: "visible", timeout: 15000 });
  await saveScreenshot(page, "sat-created-in-acceptance-center");
  return { satOrderId, satOrderNo };
};

const startAndEnterExecutionViaUi = async (page) => {
  const row = page.locator("tr").filter({ hasText: satOrderNo }).first();
  await row.waitFor({ state: "visible", timeout: 10000 });

  await waitForApi(
    page,
    "PUT",
    `/api/v1/acceptance/acceptance-orders/${satOrderId}/start`,
    async () => {
      await row.getByRole("button", { name: new RegExp(`开始验收 ${satOrderNo}`) }).click();
    },
  );

  const refreshedRow = page.locator("tr").filter({ hasText: satOrderNo }).first();
  await refreshedRow
    .getByRole("button", { name: new RegExp(`执行验收 ${satOrderNo}`) })
    .waitFor({ state: "visible", timeout: 15000 });
  await refreshedRow.getByRole("button", { name: new RegExp(`执行验收 ${satOrderNo}`) }).click();
  await page.waitForURL((url) => new URL(url).pathname === `/acceptance-orders/${satOrderId}/execute`, {
    timeout: 15000,
  });
  await page.getByText(`验收执行 - ${satOrderNo}`).waitFor({ state: "visible", timeout: 15000 });
  await saveScreenshot(page, "sat-execution-page-opened");
  return { route: `/acceptance-orders/${satOrderId}/execute` };
};

const updateCheckItem = async (page, itemName, actualValue) => {
  await page.getByText(itemName).first().click();
  await page.getByText(`${itemName} - 检查结果`).waitFor({ state: "visible", timeout: 10000 });
  await page.getByPlaceholder("填写实际测量值").fill(actualValue);
  await page.getByPlaceholder("备注说明").fill(`${itemName} 已通过 QA 现场验证`);
  await waitForApi(
    page,
    "PUT",
    "/api/v1/acceptance/acceptance-items/",
    async () => {
      await page.getByRole("button", { name: /^保存$/ }).click();
    },
  );
  await page.getByText(`${itemName} - 检查结果`).waitFor({ state: "hidden", timeout: 10000 }).catch(() => {});
};

const executeCheckItemsViaUi = async (page) => {
  await updateCheckItem(page, "QA 电气安全检查", "OK");
  await updateCheckItem(page, "QA 机构运行检查", "OK");
  await page.getByText("100.0%").first().waitFor({ state: "visible", timeout: 15000 });
  await saveScreenshot(page, "sat-check-items-passed");
  const ids = dbExec(`SELECT id FROM acceptance_order_items WHERE order_id=${satOrderId} ORDER BY id;`)
    .split("\n")
    .filter(Boolean)
    .map(Number);
  report.created.orderItems.push(...ids);
  return { checkedItems: ids.length };
};

const createIssueViaUi = async (page) => {
  await page.getByRole("button", { name: /上报问题/ }).click();
  await page.getByRole("heading", { name: "上报问题" }).waitFor({ state: "visible", timeout: 10000 });
  await page.getByPlaceholder("问题分类").fill("现场观察项");
  await page.getByPlaceholder("详细描述问题...").fill(`${runPrefix} 客户建议增加铭牌中文说明`);

  const response = await waitForApi(
    page,
    "POST",
    `/api/v1/acceptance/acceptance-orders/${satOrderId}/issues`,
    async () => {
      await page.getByRole("button", { name: /^提交$/ }).click();
    },
  );
  const issue = unwrap(response.json);
  if (!issue.id) throw new Error(`创建问题响应缺少 id: ${JSON.stringify(response.json)}`);
  report.created.issues.push(issue.id);
  await page.getByText(`${runPrefix} 客户建议增加铭牌中文说明`).waitFor({
    state: "visible",
    timeout: 10000,
  });
  await saveScreenshot(page, "sat-issue-created");
  return { issueId: issue.id };
};

const completeAcceptanceViaUi = async (page) => {
  await page.getByRole("button", { name: /^完成验收$/ }).click();
  await page.getByRole("heading", { name: "完成验收" }).waitFor({ state: "visible", timeout: 10000 });
  await page.getByPlaceholder("验收结论...").fill(`${runPrefix} SAT 现场验收通过`);

  await waitForApi(
    page,
    "PUT",
    `/api/v1/acceptance/acceptance-orders/${satOrderId}/complete`,
    async () => {
      await page.getByRole("button", { name: /^完成验收$/ }).last().click();
    },
  );
  await waitQuiet(page);
  await saveScreenshot(page, "sat-completed");
  return { satOrderId };
};

const verifyDatabaseState = () => {
  const state = dbExec(`
    SELECT
      o.status || '|' || o.overall_result || '|' || o.pass_rate || '|' ||
      (SELECT COUNT(*) FROM acceptance_order_items i WHERE i.order_id=o.id AND i.result_status='PASSED') || '|' ||
      (SELECT COUNT(*) FROM acceptance_issues ai WHERE ai.order_id=o.id)
    FROM acceptance_orders o
    WHERE o.id=${satOrderId};
  `);
  if (!state.startsWith("COMPLETED|PASSED|100")) {
    throw new Error(`验收单状态未完成通过：${state}`);
  }
  if (!state.endsWith("|2|1")) {
    throw new Error(`检查项/问题数量不符合预期：${state}`);
  }
  return { state };
};

const verifyCleanup = () => {
  cleanupCreated();
  const residual = dbExec(`
    SELECT
      (SELECT COUNT(*) FROM customers WHERE customer_code LIKE '${runPrefix}%') || '|' ||
      (SELECT COUNT(*) FROM projects WHERE project_code LIKE '${runPrefix}%') || '|' ||
      (SELECT COUNT(*) FROM machines WHERE machine_code LIKE '${runPrefix}%') || '|' ||
      (SELECT COUNT(*) FROM acceptance_templates WHERE template_code LIKE '${runPrefix}%') || '|' ||
      (SELECT COUNT(*) FROM acceptance_orders WHERE order_no LIKE '%${runPrefix}%');
  `);
  if (residual !== "0|0|0|0|0") {
    throw new Error(`清理后仍有残留：${residual}`);
  }
  return { residual };
};

const main = async () => {
  writeReport();
  const browser = await chromium.launch({ headless });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });

  page.on("console", (message) => {
    if (["error", "warning"].includes(message.type())) {
      const text = message.text();
      if (!text.includes("[API请求]") && !text.includes("[API]")) {
        report.console.push({ type: message.type(), text });
      }
    }
  });
  page.on("pageerror", (error) => report.pageErrors.push(error.message));
  page.on("requestfailed", (request) => {
    const url = request.url();
    if (url.startsWith("https://rsms.me/inter/font-files/")) return;
    report.requestFailures.push(`${request.method()} ${url} ${request.failure()?.errorText}`);
  });
  page.on("dialog", async (dialog) => {
    report.dialogs.push({ type: dialog.type(), message: dialog.message() });
    await dialog.accept().catch(() => {});
  });

  try {
    await runStep(page, "setup qa SAT acceptance data", async () => {
      setupIds = setupData();
      return setupIds;
    });
    await runStep(page, "login", () => login(page));
    await runStep(page, "create SAT acceptance order via delivery acceptance center UI", createSatAcceptanceViaUi);
    await runStep(page, "start SAT acceptance and enter execution page", startAndEnterExecutionViaUi);
    await runStep(page, "execute SAT checklist items", executeCheckItemsViaUi);
    await runStep(page, "create non-blocking acceptance issue", createIssueViaUi);
    await runStep(page, "complete SAT acceptance", completeAcceptanceViaUi);
    await runStep(page, "verify acceptance database state", () => verifyDatabaseState());
    await runStep(page, "cleanup and verify residuals", () => verifyCleanup());
  } finally {
    await browser.close();
  }

  const failed = report.steps.filter((step) => step.status !== "passed");
  const file = writeReport();
  if (failed.length) {
    console.error(`FAILED acceptance QA: ${file}`);
    process.exit(1);
  }
  console.log(JSON.stringify({ ok: true, report: file, steps: report.steps.length }, null, 2));
};

main().catch((error) => {
  try {
    cleanupCreated();
  } catch {
    // best-effort cleanup
  }
  writeReport();
  console.error(error);
  process.exit(1);
});
