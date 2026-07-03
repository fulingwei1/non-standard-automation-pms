import { execFileSync } from "node:child_process";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require("../../frontend/node_modules/playwright");

const BASE_URL = process.env.QA_BASE_URL || "http://127.0.0.1:5173";
const DB_PATH = process.env.QA_DB_PATH || "data/app.db";
const TEST_DATE = "2035-01-31";
const QA_PREFIX = "QA-FSLOG-20350131";
const ADMIN_ID = 15;

const runSql = (sql) =>
  execFileSync("sqlite3", ["-cmd", ".timeout 5000", DB_PATH, sql], {
    encoding: "utf8",
  }).trim();

const sqlValue = (sql) => runSql(sql).split("\n").filter(Boolean).at(-1) || "";

const cleanup = () => {
  runSql(`
    PRAGMA foreign_keys=OFF;
    DELETE FROM work_log_mentions
      WHERE work_log_id IN (
        SELECT id FROM work_logs
        WHERE user_id=${ADMIN_ID} AND work_date='${TEST_DATE}'
      );
    DELETE FROM timesheet
      WHERE id IN (
        SELECT timesheet_id FROM work_logs
        WHERE user_id=${ADMIN_ID} AND work_date='${TEST_DATE}' AND timesheet_id IS NOT NULL
      );
    DELETE FROM work_logs WHERE user_id=${ADMIN_ID} AND work_date='${TEST_DATE}';
    DELETE FROM installation_dispatch_orders WHERE order_no LIKE '${QA_PREFIX}%';
    DELETE FROM machines WHERE machine_code LIKE '${QA_PREFIX}%';
    DELETE FROM projects WHERE project_code LIKE '${QA_PREFIX}%';
    DELETE FROM customers WHERE customer_code LIKE '${QA_PREFIX}%';
  `);
};

const setup = () => {
  cleanup();
  runSql(`
    INSERT INTO customers (
      customer_code, customer_name, address, contact_person, contact_phone,
      status, created_by, is_active, created_at, updated_at
    ) VALUES (
      '${QA_PREFIX}-CUST', 'QA售后日志客户', '深圳市南山区测试路',
      '王工', '13800000000', 'ACTIVE', ${ADMIN_ID}, 1, datetime('now'), datetime('now')
    );
  `);
  const customerId = Number(sqlValue("SELECT id FROM customers WHERE customer_code='QA-FSLOG-20350131-CUST';"));
  runSql(`
    INSERT INTO projects (
      project_code, project_name, customer_id, customer_name, customer_contact,
      customer_phone, customer_address, stage, status, health, is_active,
      is_archived, created_by, created_at, updated_at
    ) VALUES (
      '${QA_PREFIX}-PJ', 'QA售后日志项目', ${customerId}, 'QA售后日志客户',
      '王工', '13800000000', '深圳市南山区测试路', 'S7', 'ST01', 'H1',
      1, 0, ${ADMIN_ID}, datetime('now'), datetime('now')
    );
  `);
  const projectId = Number(sqlValue("SELECT id FROM projects WHERE project_code='QA-FSLOG-20350131-PJ';"));
  runSql(`
    INSERT INTO machines (
      project_id, machine_code, machine_name, machine_no, stage, status, health,
      created_at, updated_at
    ) VALUES (
      ${projectId}, '${QA_PREFIX}-MC', 'QA售后日志设备', 1, 'S7', 'ST01', 'H1',
      datetime('now'), datetime('now')
    );
  `);
  const machineId = Number(sqlValue("SELECT id FROM machines WHERE machine_code='QA-FSLOG-20350131-MC';"));
  runSql(`
    INSERT INTO installation_dispatch_orders (
      order_no, project_id, machine_id, customer_id, task_type, task_title,
      task_description, location, scheduled_date, estimated_hours,
      assigned_to_id, assigned_to_name, assigned_by_id, assigned_by_name,
      assigned_time, status, priority, progress, customer_contact,
      customer_phone, customer_address, execution_notes, created_at, updated_at
    ) VALUES (
      '${QA_PREFIX}-INST', ${projectId}, ${machineId}, ${customerId},
      'INSTALLATION', '现场安装调试', '完成现场安装、接线和基础调试',
      '深圳客户现场', '${TEST_DATE}', 7.5, ${ADMIN_ID}, '系统管理员',
      ${ADMIN_ID}, '系统管理员', datetime('now'), 'IN_PROGRESS', 'HIGH', 35,
      '王工', '13800000000', '深圳市南山区测试路', '已到场并完成设备定位',
      datetime('now'), datetime('now')
    );
  `);
  return { customerId, projectId, machineId };
};

const login = async (page) => {
  const response = await fetch(`${BASE_URL}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ username: "admin", password: "admin123" }),
  });
  if (!response.ok) {
    throw new Error(`登录接口失败：${response.status} ${await response.text()}`);
  }
  const data = await response.json();
  await page.goto(BASE_URL, { waitUntil: "domcontentloaded" });
  await page.evaluate((payload) => {
    localStorage.setItem("token", payload.access_token);
    if (payload.refresh_token) {
      localStorage.setItem("refresh_token", payload.refresh_token);
    }
  }, data);
};

const main = async () => {
  const setupIds = setup();
  const errors = [];
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  page.on("console", (message) => {
    if (["error", "warning"].includes(message.type())) {
      errors.push({ type: message.type(), text: message.text() });
    }
  });
  page.on("requestfailed", (request) => {
    errors.push({ type: "requestfailed", text: `${request.method()} ${request.url()} ${request.failure()?.errorText}` });
  });
  page.on("pageerror", (error) => {
    errors.push({ type: "pageerror", text: error.message });
  });

  try {
    await login(page);
    await page.goto(`${BASE_URL}/delivery/acceptance-center?tab=installation`, {
      waitUntil: "domcontentloaded",
    });
    await page.getByText("安装调试派工管理").waitFor({ timeout: 20000 });
    await page.getByText(`${QA_PREFIX}-INST`).waitFor({ timeout: 20000 }).catch(async (error) => {
      const token = await page.evaluate(() => localStorage.getItem("token"));
      const apiProbe = await page.evaluate(async () => {
        const response = await fetch("/api/v1/installation-dispatch/orders?page=1&page_size=10&keyword=QA-FSLOG-20350131", {
          headers: { Authorization: `Bearer ${localStorage.getItem("token") || ""}` },
        });
        return { status: response.status, body: await response.text() };
      });
      const body = await page.locator("body").innerText();
      throw new Error(
        `列表未显示 QA 派工单；token=${token ? "set" : "missing"}；api=${JSON.stringify(apiProbe)}；errors=${JSON.stringify(errors)}；body=${body.slice(0, 1500)}`,
        { cause: error },
      );
    });
    await page.getByRole("button", { name: "今日外出日志" }).click();
    await page.locator('input[type="date"]').fill(TEST_DATE);
    await page.getByText("QA售后日志项目 / QA售后日志设备").waitFor({ timeout: 20000 });
    await page.getByPlaceholder("小时").fill("7.5");
    await page.getByPlaceholder("完成了哪些现场工作").fill("完成电气接线和通电检查");
    await page.getByPlaceholder("没有问题可填暂无").fill("暂无异常");
    await page.getByPlaceholder("后续计划").fill("明天进行联机调试");
    await page.getByRole("button", { name: "提交日志" }).click();
    await page.getByText("工作日志已提交").waitFor({ timeout: 20000 });

    const verification = runSql(`
      SELECT
        wl.id || '|' || wl.content || '|' || group_concat(wlm.mention_type || ':' || wlm.mention_id, ',')
      FROM work_logs wl
      LEFT JOIN work_log_mentions wlm ON wlm.work_log_id = wl.id
      WHERE wl.user_id=${ADMIN_ID} AND wl.work_date='${TEST_DATE}'
      GROUP BY wl.id;
    `);
    if (!verification.includes("完成电气接线和通电检查")) {
      throw new Error(`工作日志内容未写入：${verification}`);
    }
    if (!verification.includes(`PROJECT:${setupIds.projectId}`)) {
      throw new Error(`工作日志未关联项目：${verification}`);
    }
    if (!verification.includes(`MACHINE:${setupIds.machineId}`)) {
      throw new Error(`工作日志未关联设备：${verification}`);
    }

    const report = {
      ok: true,
      setupIds,
      verification,
      browserErrors: errors,
    };
    console.log(JSON.stringify(report, null, 2));
  } finally {
    await browser.close();
    cleanup();
  }
};

main().catch((error) => {
  try {
    cleanup();
  } catch {
    // ignore cleanup failure in failure path
  }
  console.error(error);
  process.exit(1);
});
