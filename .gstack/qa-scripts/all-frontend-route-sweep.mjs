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
const routeOffset = Number(process.env.QA_ROUTE_OFFSET || 0);
const routeLimit = Number(process.env.QA_ROUTE_LIMIT || 0);
const buttonLimit = Number(process.env.QA_BUTTON_LIMIT || 8);
const routeFilter = process.env.QA_ROUTE_FILTER || "";
const includeDynamic = process.env.QA_INCLUDE_DYNAMIC !== "0";
const listOnly = process.env.QA_LIST_ONLY === "1";
const headless = process.env.QA_HEADLESS !== "0";
const networkIdleTimeout = Number(process.env.QA_NETWORK_IDLE_TIMEOUT || 2500);
const settleMs = Number(process.env.QA_SETTLE_MS || 400);
const actionDelayMs = Number(process.env.QA_ACTION_DELAY_MS || 500);
const routeDelayMs = Number(process.env.QA_ROUTE_DELAY_MS || 0);
const stamp = new Date().toISOString().replace(/[-:TZ.]/g, "").slice(0, 14);
const reportDir = path.resolve(".gstack/qa-reports");
const screenshotDir = path.join(reportDir, "screenshots");
fs.mkdirSync(screenshotDir, { recursive: true });

const routeSourceFiles = [
  "frontend/src/routes/routeConfig.jsx",
  ...fs
    .readdirSync("frontend/src/routes/modules")
    .filter((name) => name.endsWith(".jsx"))
    .map((name) => `frontend/src/routes/modules/${name}`),
  "frontend/src/components/layout/sidebarConfig/default.js",
  "frontend/src/lib/allMenuItems.js",
];

const dangerousPattern =
  /(删除|移除|作废|清空|关闭|撤回|驳回|拒绝|通过|批准|审批|发料|提交|发布|签署|开票|收款|付款|生成项目|转项目|转换|确认收款|批量|导入|导出|下载|开始审批|启动审批|发起立项|立项|禁用|停用|结算|退出登录|注销|保存|完成|开始|启动|派工|分配|指派|接单|验收通过|确认|恢复|重置密码|上传)/;
const loginPagePattern = /(登录|系统管理员|全权限验证|副总经理|记住登录状态|忘记密码)/;
const noisyStatusPattern = /\.(png|jpe?g|gif|svg|webp|ico|css|js|map|woff2?)($|\?)/i;
const missingOptionalApiPattern =
  /(\/api\/v1\/notifications\/unread-count|\/api\/v1\/my\/|\/api\/v1\/users\/me\/permissions)/;
const hardConsoleAllowPattern =
  /ResizeObserver loop completed|Warning:|Each child in a list should have a unique "key"|React Router Future Flag Warning/;

const report = {
  stamp,
  root: ROOT,
  dbPath: DB_PATH,
  headless,
  routeOffset,
  routeLimit,
  buttonLimit,
  routeFilter,
  includeDynamic,
  listOnly,
  networkIdleTimeout,
  settleMs,
  actionDelayMs,
  routeDelayMs,
  routeInventory: [],
  selectedRoutes: [],
  skippedRoutes: [],
  routes: [],
  console: [],
  pageErrors: [],
  requestFailures: [],
  apiErrors: [],
  rateLimitErrors: [],
  clickedTotal: 0,
  skippedTotal: 0,
  screenshots: [],
};

const reportFile = () => path.join(reportDir, `all-frontend-route-sweep-${stamp}.json`);
const writeReport = () => {
  const file = reportFile();
  fs.writeFileSync(file, JSON.stringify(report, null, 2));
  return file;
};

const dbValue = (sql) => {
  try {
    return execFileSync("sqlite3", ["-cmd", ".timeout 5000", DB_PATH, sql], {
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"],
    })
      .trim()
      .split("\n")
      .filter(Boolean)
      .at(-1);
  } catch {
    return "";
  }
};

const firstExistingId = (table, where = "1=1") =>
  dbValue(`SELECT id FROM ${table} WHERE ${where} ORDER BY id LIMIT 1;`) || "1";

const firstEngineerUserId = () =>
  dbValue("SELECT user_id FROM engineer_profile ORDER BY user_id LIMIT 1;") || sampleIds.userId || "1";

const sampleIds = {
  projectId: firstExistingId("projects", "is_active=1"),
  project_id: firstExistingId("projects", "is_active=1"),
  scheduleId: firstExistingId("project_delivery_schedules"),
  templateId: firstExistingId("stage_templates"),
  reviewId: firstExistingId("project_reviews"),
  review_id: firstExistingId("project_reviews"),
  taskId: firstExistingId("tasks"),
  task_id: firstExistingId("tasks"),
  orderId: firstExistingId("purchase_orders"),
  order_id: firstExistingId("purchase_orders"),
  schedule_id: firstExistingId("project_delivery_schedules"),
  userId: firstExistingId("users"),
  user_id: firstExistingId("users"),
  employeeId: firstExistingId("users"),
  employee_id: firstExistingId("users"),
  customerId: firstExistingId("customers"),
  customer_id: firstExistingId("customers"),
  leadId: firstExistingId("leads"),
  lead_id: firstExistingId("leads"),
  sourceType: "lead",
  source_type: "lead",
  sourceId: firstExistingId("leads"),
  source_id: firstExistingId("leads"),
  opportunityId: firstExistingId("opportunities"),
  opportunity_id: firstExistingId("opportunities"),
  quoteId: firstExistingId("quotes"),
  quote_id: firstExistingId("quotes"),
  contractId: firstExistingId("contracts"),
  contract_id: firstExistingId("contracts"),
  invoiceId: firstExistingId("invoices"),
  invoice_id: firstExistingId("invoices"),
  materialId: firstExistingId("materials"),
  material_id: firstExistingId("materials"),
  machineId: firstExistingId("machines"),
  machine_id: firstExistingId("machines"),
  workerId: firstExistingId("workers"),
  worker_id: firstExistingId("workers"),
  workshopId: firstExistingId("workshops"),
  workshop_id: firstExistingId("workshops"),
  reportId: firstExistingId("shortage_reports"),
  report_id: firstExistingId("shortage_reports"),
  department: "production",
  section: "knowledge",
  id: "1",
};

const contextualId = (route, param) => {
  if (param === "userId" && route.includes("/engineer-performance/engineer/")) {
    return firstEngineerUserId();
  }
  if (param !== "id") return sampleIds[param] || "1";
  if (route.includes("/alerts/")) return firstExistingId("alerts");
  if (route.includes("/approvals/")) return firstExistingId("approval_records");
  if (route.includes("/change-management/ecn/") || route.includes("/ecn/")) return firstExistingId("ecn_orders");
  if (route.includes("/rd-projects/")) return firstExistingId("rd_projects");
  if (route.includes("/purchases/receipts/")) return firstExistingId("purchase_receipts");
  if (route.includes("/purchases/")) return firstExistingId("purchase_orders");
  if (route.includes("/purchase-requests/")) return firstExistingId("purchase_requests");
  if (route.includes("/shortage/")) return firstExistingId("shortage_reports");
  if (route.includes("/arrival-tracking/")) return firstExistingId("shortage_arrivals");
  if (route.includes("/solutions/")) return firstExistingId("presale_solutions");
  if (route.includes("/customers/") || route.includes("/sales/customers/")) return sampleIds.customerId;
  if (route.includes("/projects/")) return sampleIds.projectId;
  return "1";
};

const normalizePath = (routePath) => {
  const source = String(routePath || "").trim();
  if (!source || source === "*" || source === "/*") return null;
  if (!source.startsWith("/")) return null;
  return source;
};

const extractRoutes = () => {
  const candidates = [];
  for (const file of routeSourceFiles) {
    if (!fs.existsSync(file)) continue;
    const text = fs.readFileSync(file, "utf8");
    const patterns = [
      /<Route[\s\S]*?\bpath\s*=\s*["']([^"']+)["']/g,
      /\bpath\s*:\s*["']([^"']+)["']/g,
      /\bpath\s*=\s*["']([^"']+)["']/g,
    ];
    for (const pattern of patterns) {
      for (const match of text.matchAll(pattern)) {
        const routePath = normalizePath(match[1]);
        if (!routePath) continue;
        candidates.push({ path: routePath, source: file });
      }
    }
  }

  const byPath = new Map();
  for (const candidate of candidates) {
    if (!byPath.has(candidate.path)) {
      byPath.set(candidate.path, { path: candidate.path, sources: new Set() });
    }
    byPath.get(candidate.path).sources.add(candidate.source);
  }

  return Array.from(byPath.values())
    .map((route) => {
      const params = [...route.path.matchAll(/:([A-Za-z_][A-Za-z0-9_]*)/g)].map((match) => match[1]);
      let resolved = route.path;
      const replacements = {};
      for (const param of params) {
        const value = contextualId(route.path, param);
        replacements[param] = value;
        resolved = resolved.replace(new RegExp(`:${param}\\b`, "g"), value);
      }
      return {
        originalPath: route.path,
        route: resolved,
        isDynamic: params.length > 0,
        params,
        replacements,
        sources: Array.from(route.sources).sort(),
      };
    })
    .sort((a, b) => a.route.localeCompare(b.route, "zh-Hans-CN"));
};

const routeInventory = extractRoutes();
report.routeInventory = routeInventory;

const selectedRoutes = routeInventory
  .filter((entry) => includeDynamic || !entry.isDynamic)
  .filter((entry) => !routeFilter || entry.route.includes(routeFilter) || entry.originalPath.includes(routeFilter))
  .slice(routeOffset, routeLimit > 0 ? routeOffset + routeLimit : undefined);
report.selectedRoutes = selectedRoutes;
report.skippedRoutes = routeInventory.filter((entry) => includeDynamic ? false : entry.isDynamic);

const normalizeText = (text) => String(text || "").replace(/\s+/g, " ").trim();
const escapeRegExp = (text) => text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

const saveScreenshot = async (page, routeReport, label) => {
  const safe = label.replace(/[^a-z0-9\u4e00-\u9fa5_-]+/gi, "_").slice(0, 100);
  const file = path.join(screenshotDir, `all-routes-${safe}-${stamp}.png`);
  await page.screenshot({ path: file, fullPage: true }).catch(() => {});
  routeReport.screenshots.push(file);
  report.screenshots.push(file);
};

const saveReportScreenshot = async (page, label) => {
  const safe = label.replace(/[^a-z0-9\u4e00-\u9fa5_-]+/gi, "_").slice(0, 100);
  const file = path.join(screenshotDir, `all-routes-${safe}-${stamp}.png`);
  await page.screenshot({ path: file, fullPage: true }).catch(() => {});
  report.screenshots.push(file);
  return file;
};

const waitQuiet = async (page) => {
  await page.waitForLoadState("networkidle", { timeout: networkIdleTimeout }).catch(() => {});
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
  await page.locator('form button[type="submit"]').click({ timeout: 8000 });
  await page.waitForURL((url) => new URL(url).pathname !== "/login", { timeout: 20000 }).catch(() => {});
  await waitQuiet(page);

  if (await isLoginPage(page)) {
    const errorText = await page.locator(".text-red-500").first().innerText().catch(() => "");
    const screenshot = await saveReportScreenshot(page, "auth-login-failed");
    report.auth = {
      failed: true,
      url: page.url(),
      errorText,
      tokenPresent: await page.evaluate(() => Boolean(localStorage.getItem("token"))).catch(() => false),
      screenshot,
    };
    throw new Error(`UI login did not leave /login${errorText ? `: ${errorText}` : ""}`);
  }
};

const gotoAuthenticatedRoute = async (page, route) => {
  await page.goto(`${ROOT}${route}`, { waitUntil: "domcontentloaded", timeout: 25000 });
  await waitQuiet(page);
  if (await isLoginPage(page)) {
    await ensureAuthenticated(page);
    await page.goto(`${ROOT}${route}`, { waitUntil: "domcontentloaded", timeout: 25000 });
    await waitQuiet(page);
  }
  await page.evaluate(() => window.scrollTo(0, 0)).catch(() => {});
};

const closeTransientUi = async (page) => {
  if (page.isClosed()) return;
  const transient = page.locator('[role="dialog"], .ant-modal, .ant-drawer, [data-radix-popper-content-wrapper]').last();
  if ((await transient.count().catch(() => 0)) > 0 && (await transient.isVisible().catch(() => false))) {
    const antCloseButton = page
      .locator(".ant-modal-wrap .ant-modal-close, .ant-drawer .ant-drawer-close, button[aria-label='Close'], button[aria-label='关闭']")
      .last();
    if ((await antCloseButton.count().catch(() => 0)) > 0 && (await antCloseButton.isVisible().catch(() => false))) {
      await antCloseButton.click({ timeout: 3000 }).catch(() => {});
      await page.waitForTimeout(250).catch(() => {});
      return;
    }

    const closeButton = transient
      .locator("button")
      .filter({ hasText: /取消|关闭|返回|知道了|我知道了/ })
      .first();
    if ((await closeButton.count().catch(() => 0)) > 0) {
      await closeButton.click({ timeout: 3000 }).catch(() => {});
    } else {
      const xButton = transient
        .locator('button[aria-label="Close"], button[aria-label="关闭"], .ant-modal-close, .ant-drawer-close')
        .first();
      if ((await xButton.count().catch(() => 0)) > 0) {
        await xButton.click({ timeout: 3000 }).catch(() => {});
      } else {
        await page.keyboard.press("Escape").catch(() => {});
      }
    }
    await page.waitForTimeout(250).catch(() => {});
  }
  await page.keyboard.press("Escape").catch(() => {});
};

const isHardApiStatus = (status, url) =>
  status >= 400 &&
  status !== 401 &&
  status !== 403 &&
  status !== 404 &&
  status !== 429 &&
  !missingOptionalApiPattern.test(url);

const isHardConsole = (item) => {
  if (item.type !== "error") return false;
  return !hardConsoleAllowPattern.test(item.text || "") && !/429|Too Many Requests|请求过于频繁/.test(item.text || "");
};

const snapshotButtons = async (page) =>
  page.locator("main button, main [role='button']").evaluateAll((buttons) =>
    buttons
      .map((button, index) => {
        const rect = button.getBoundingClientRect();
        const style = window.getComputedStyle(button);
        const text = (button.innerText || button.textContent || button.getAttribute("aria-label") || button.title || "")
          .replace(/\s+/g, " ")
          .trim();
        return {
          index,
          text,
          aria: button.getAttribute("aria-label") || "",
          title: button.title || "",
          disabled: button.disabled || button.getAttribute("aria-disabled") === "true",
          role: button.getAttribute("role") || "",
          type: button.getAttribute("type") || "",
          visible:
            rect.width > 1 &&
            rect.height > 1 &&
            style.visibility !== "hidden" &&
            style.display !== "none",
        };
      })
      .filter((item) => item.visible && !item.disabled && item.text),
  );

const errorBoundaryVisible = async (page) => {
  const text = page.locator("text=/页面加载失败|出现错误|Something went wrong|ErrorBoundary/i").first();
  return (await text.count()) > 0 && (await text.isVisible().catch(() => false));
};

const runRoute = async (page, entry) => {
  const routeReport = {
    originalPath: entry.originalPath,
    route: entry.route,
    sources: entry.sources,
    isDynamic: entry.isDynamic,
    params: entry.params,
    replacements: entry.replacements,
    startedAt: new Date().toISOString(),
    finalUrl: "",
    loaded: false,
    errorBoundary: false,
    buttonsFound: 0,
    clicked: [],
    skipped: [],
    apiErrors: [],
    pageErrors: [],
    requestFailures: [],
    consoleErrors: [],
    rateLimitErrors: [],
    screenshots: [],
    authFailure: false,
  };
  report.routes.push(routeReport);
  const baseline = {
    apiErrors: report.apiErrors.length,
    rateLimitErrors: report.rateLimitErrors.length,
    pageErrors: report.pageErrors.length,
    requestFailures: report.requestFailures.length,
    console: report.console.length,
  };

  console.log(`\n[route] ${entry.route} (${entry.originalPath})`);
  try {
    await gotoAuthenticatedRoute(page, entry.route);
    routeReport.loaded = true;
    routeReport.finalUrl = page.url();
  } catch (error) {
    routeReport.loadError = error?.stack || error?.message || String(error);
    await saveScreenshot(page, routeReport, `${entry.route}-load-failed`);
    writeReport();
    return;
  }

  if (await isLoginPage(page)) {
    routeReport.authFailure = true;
    routeReport.skipped.push({ label: entry.route, reason: "still-on-login-page" });
    await saveScreenshot(page, routeReport, `${entry.route}-auth-failure`);
    writeReport();
    return;
  }

  routeReport.errorBoundary = await errorBoundaryVisible(page);
  if (routeReport.errorBoundary) {
    await saveScreenshot(page, routeReport, `${entry.route}-error-boundary`);
  }

  const buttons = await snapshotButtons(page).catch((error) => {
    routeReport.buttonSnapshotError = error?.message || String(error);
    return [];
  });
  routeReport.buttonsFound = buttons.length;
  const candidates = buttons
    .filter((button) => {
      const label = normalizeText(button.text || button.aria || button.title);
      return label && !loginPagePattern.test(label);
    })
    .slice(0, buttonLimit);

  for (const button of candidates) {
    const label = normalizeText(button.text || button.aria || button.title);
    if (dangerousPattern.test(label)) {
      routeReport.skipped.push({ label, reason: "dangerous-write-action" });
      report.skippedTotal += 1;
      continue;
    }
    if (label.length > 50 && !/(新建|新增|创建|添加|刷新|搜索|筛选|重置|详情|查看|展开|收起|更多|返回)/.test(label)) {
      routeReport.skipped.push({ label, reason: "long-non-action-text" });
      report.skippedTotal += 1;
      continue;
    }

    if (await isLoginPage(page)) {
      await gotoAuthenticatedRoute(page, entry.route);
    }
    const beforeUrl = page.url();
    await page.evaluate(() => window.scrollTo(0, 0)).catch(() => {});
    const beforeErrors = {
      apiErrors: report.apiErrors.length,
      rateLimitErrors: report.rateLimitErrors.length,
      pageErrors: report.pageErrors.length,
      requestFailures: report.requestFailures.length,
      console: report.console.length,
    };
    try {
      let locator = page.locator("main button, main [role='button']").nth(button.index);
      if (!(await locator.isVisible({ timeout: 1000 }).catch(() => false))) {
        locator = page
          .locator("main button, main [role='button']")
          .filter({ hasText: new RegExp(`^${escapeRegExp(label)}$`) })
          .first();
      }
      if (!(await locator.isVisible({ timeout: 2000 }).catch(() => false))) {
        routeReport.skipped.push({ label, reason: "not-visible-at-click-time" });
        report.skippedTotal += 1;
        continue;
      }
      if (await locator.isDisabled().catch(() => false)) {
        routeReport.skipped.push({ label, reason: "disabled-at-click-time" });
        report.skippedTotal += 1;
        continue;
      }

      await locator.click({ timeout: 5000 });
      await waitQuiet(page);
      const changedUrl = page.url() !== beforeUrl;
      const newErrors = {
        apiErrors: report.apiErrors.length - beforeErrors.apiErrors,
        rateLimitErrors: report.rateLimitErrors.length - beforeErrors.rateLimitErrors,
        pageErrors: report.pageErrors.length - beforeErrors.pageErrors,
        requestFailures: report.requestFailures.length - beforeErrors.requestFailures,
        consoleErrors: report.console.slice(beforeErrors.console).filter(isHardConsole).length,
      };
      routeReport.clicked.push({ label, changedUrl, newErrors });
      report.clickedTotal += 1;
      if (newErrors.apiErrors || newErrors.pageErrors || newErrors.requestFailures || newErrors.consoleErrors) {
        await saveScreenshot(page, routeReport, `${entry.route}-${label}-error`);
      }
      await closeTransientUi(page);
      if (changedUrl) {
        await gotoAuthenticatedRoute(page, entry.route).catch(() => {});
      }
      await page.waitForTimeout(actionDelayMs);
    } catch (error) {
      const message = error?.message || String(error);
      routeReport.clicked.push({ label, index: button.index, error: message });
      await saveScreenshot(page, routeReport, `${entry.route}-${label}-click-failed`);
      await closeTransientUi(page);
      await gotoAuthenticatedRoute(page, entry.route).catch(() => {});
      await page.waitForTimeout(actionDelayMs);
    }
  }

  routeReport.apiErrors = report.apiErrors.slice(baseline.apiErrors);
  routeReport.rateLimitErrors = report.rateLimitErrors.slice(baseline.rateLimitErrors);
  routeReport.pageErrors = report.pageErrors.slice(baseline.pageErrors);
  routeReport.requestFailures = report.requestFailures.slice(baseline.requestFailures);
  routeReport.consoleErrors = report.console.slice(baseline.console).filter(isHardConsole);
  routeReport.finishedAt = new Date().toISOString();
  writeReport();
};

const main = async () => {
  writeReport();
  console.log(
    JSON.stringify(
      {
        routeInventory: report.routeInventory.length,
        selectedRoutes: report.selectedRoutes.length,
        routeOffset,
        routeLimit,
        routeFilter,
        includeDynamic,
        listOnly,
      },
      null,
      2,
    ),
  );

  if (listOnly) {
    const file = writeReport();
    console.log(JSON.stringify({ file, listOnly: true }, null, 2));
    return;
  }

  const browser = await chromium.launch({ headless });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });

  page.on("console", (msg) => {
    const text = msg.text();
    const type = msg.type();
    if (type === "error" || type === "warning") {
      report.console.push({ type, text, url: page.url(), at: new Date().toISOString() });
    }
  });
  page.on("pageerror", (error) => {
    report.pageErrors.push({ message: error.message, stack: error.stack, url: page.url() });
  });
  page.on("requestfailed", (request) => {
    const url = request.url();
    const failure = request.failure()?.errorText;
    if (!noisyStatusPattern.test(url) && failure !== "net::ERR_ABORTED") {
      report.requestFailures.push({
        url,
        method: request.method(),
        failure,
        pageUrl: page.url(),
      });
    }
  });
  page.on("response", async (response) => {
    const url = response.url();
    const status = response.status();
    if (url.includes("/api/") && status === 429) {
      report.rateLimitErrors.push({
        url,
        status,
        method: response.request().method(),
        pageUrl: page.url(),
        body: (await response.text().catch(() => "")).slice(0, 600),
      });
    } else if (url.includes("/api/") && isHardApiStatus(status, url)) {
      report.apiErrors.push({
        url,
        status,
        method: response.request().method(),
        pageUrl: page.url(),
        body: (await response.text().catch(() => "")).slice(0, 600),
      });
    }
  });

  try {
    await ensureAuthenticated(page);
    for (const entry of selectedRoutes) {
      await runRoute(page, entry);
      if (routeDelayMs > 0) {
        await page.waitForTimeout(routeDelayMs);
      }
    }
  } finally {
    await browser.close().catch(() => {});
  }

  const file = writeReport();
  const hardConsoleItems = report.console.filter(isHardConsole);
  const clickErrorCount = report.routes.reduce(
    (sum, route) => sum + route.clicked.filter((item) => item.error).length,
    0,
  );
  const loadErrorCount = report.routes.filter((route) => route.loadError).length;
  const errorBoundaryCount = report.routes.filter((route) => route.errorBoundary).length;
  const authFailureCount = report.routes.filter((route) => route.authFailure).length;
  const hardErrorCount =
    report.apiErrors.length +
    report.pageErrors.length +
    report.requestFailures.length +
    hardConsoleItems.length +
    errorBoundaryCount;
  const summary = {
    file,
    routeInventory: report.routeInventory.length,
    routes: report.routes.length,
    clickedTotal: report.clickedTotal,
    skippedTotal: report.skippedTotal,
    hardErrorCount,
    clickErrorCount,
    loadErrorCount,
    errorBoundaryCount,
    authFailureCount,
    apiErrors: report.apiErrors.length,
    rateLimitErrors: report.rateLimitErrors.length,
    pageErrors: report.pageErrors.length,
    requestFailures: report.requestFailures.length,
    hardConsoleErrors: hardConsoleItems.length,
    consoleItems: report.console.length,
  };
  report.summary = summary;
  writeReport();
  console.log(JSON.stringify(summary, null, 2));
  if (hardErrorCount > 0 || clickErrorCount > 0 || loadErrorCount > 0 || authFailureCount > 0) {
    process.exitCode = 1;
  }
};

main().catch((error) => {
  report.fatal = error?.stack || error?.message || String(error);
  const file = writeReport();
  console.error(report.fatal);
  console.error(`report: ${file}`);
  process.exit(1);
});
