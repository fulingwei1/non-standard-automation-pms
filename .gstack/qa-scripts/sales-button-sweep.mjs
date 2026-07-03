import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";

const require = createRequire(new URL("../../frontend/package.json", import.meta.url));
const { chromium } = require("playwright");

const ROOT = process.env.QA_ROOT || "http://127.0.0.1:5173";
const USERNAME = process.env.QA_USER || "admin";
const PASSWORD = process.env.QA_PASSWORD || "admin123";
const routeOffset = Number(process.env.QA_ROUTE_OFFSET || 0);
const routeLimit = Number(process.env.QA_ROUTE_LIMIT || 0);
const buttonLimit = Number(process.env.QA_BUTTON_LIMIT || 12);
const routeFilter = process.env.QA_ROUTE_FILTER || "";
const headless = process.env.QA_HEADLESS !== "0";
const networkIdleTimeout = Number(process.env.QA_NETWORK_IDLE_TIMEOUT || 2500);
const settleMs = Number(process.env.QA_SETTLE_MS || 300);
const actionDelayMs = Number(process.env.QA_ACTION_DELAY_MS || 750);
const routeDelayMs = Number(process.env.QA_ROUTE_DELAY_MS || 0);
const stamp = new Date().toISOString().replace(/[-:TZ.]/g, "").slice(0, 14);
const reportDir = path.resolve(".gstack/qa-reports");
const screenshotDir = path.join(reportDir, "screenshots");
fs.mkdirSync(screenshotDir, { recursive: true });

const salesRoutes = [
  "/sales/dashboard",
  "/sales/workstation",
  "/sales/funnel",
  "/sales/customers",
  "/sales/leads",
  "/sales/opportunities",
  "/sales/quotes",
  "/sales/quotes/management",
  "/sales/contracts",
  "/sales/receivables",
  "/payments",
  "/invoices",
  "/sales/statistics",
  "/sales/team",
  "/sales/team-center",
  "/sales/opportunity-center",
  "/sales/templates",
  "/sales/templates/center",
  "/sales/cpq",
  "/sales/purchase-material-costs",
  "/financial-costs",
  "/sales/cost-templates",
  "/sales/presale-expenses",
  "/sales/priority",
  "/sales/loss-analysis",
  "/sales/pipeline-break-analysis",
  "/sales/accountability-analysis",
  "/sales/health-monitoring",
  "/sales/delay-analysis",
  "/sales/cost-overrun-analysis",
  "/sales/information-gap-analysis",
  "/sales/intelligent-quote",
  "/sales/automation",
  "/sales/forecast-dashboard",
  "/sales/customer-360",
  "/sales/performance-incentive",
  "/sales/collaboration",
  "/sales/relationship-maturity",
  "/sales/win-rate-prediction",
  "/sales/competitor-analysis",
  "/sales/organization",
  "/sales/data-quality",
  "/sales/role-based-view",
  "/sales-projects",
  "/contract-approval",
  "/cost-quotes/quotes",
  "/cost-quotes/margin",
  "/cost-quotes/material-costs",
  "/cost-quotes/financial-costs",
  "/cost-quotes/templates",
];

const selectedRoutes = salesRoutes
  .filter((route) => !routeFilter || route.includes(routeFilter))
  .slice(routeOffset, routeLimit > 0 ? routeOffset + routeLimit : undefined);

const dangerousPattern =
  /(删除|移除|作废|清空|撤回|驳回|拒绝|通过|批准|审批|提交|发布|签署|开票|收款|生成项目|转项目|转换|确认收款|批量|导入|导出|下载|开始审批|启动审批|发起立项|立项|禁用|停用|结算|退出登录|注销|保存)/;
const loginPagePattern = /(登录|系统管理员|全权限验证|副总经理|记住登录状态|忘记密码)/;
const noisyStatusPattern = /\.(png|jpe?g|gif|svg|webp|ico|css|js|map|woff2?)($|\?)/i;

const report = {
  stamp,
  root: ROOT,
  headless,
  routeOffset,
  routeLimit,
  buttonLimit,
  routeFilter,
  networkIdleTimeout,
  settleMs,
  actionDelayMs,
  routeDelayMs,
  selectedRoutes,
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

const writeReport = () => {
  const file = path.join(reportDir, `sales-button-sweep-${stamp}.json`);
  fs.writeFileSync(file, JSON.stringify(report, null, 2));
  return file;
};

const saveScreenshot = async (page, routeReport, label) => {
  const safe = label.replace(/[^a-z0-9\u4e00-\u9fa5_-]+/gi, "_").slice(0, 80);
  const file = path.join(screenshotDir, `sales-${safe}-${stamp}.png`);
  await page.screenshot({ path: file, fullPage: true }).catch(() => {});
  routeReport.screenshots.push(file);
  report.screenshots.push(file);
};

const waitQuiet = async (page) => {
  await page.waitForLoadState("networkidle", { timeout: networkIdleTimeout }).catch(() => {});
  await page.waitForTimeout(settleMs);
};

const normalizeText = (text) => String(text || "").replace(/\s+/g, " ").trim();
const escapeRegExp = (text) => text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

const snapshotButtons = async (page) =>
  page.locator("main button").evaluateAll((buttons) =>
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

const closeTransientUi = async (page) => {
  const dialog = page.locator('[role="dialog"], .ant-modal, .ant-drawer').last();
  if ((await dialog.count()) > 0 && (await dialog.isVisible().catch(() => false))) {
    const closeButton = dialog
      .locator("button")
      .filter({ hasText: /取消|关闭|返回|知道了/ })
      .first();
    if ((await closeButton.count()) > 0) {
      await closeButton.click({ timeout: 3000 }).catch(() => {});
    } else {
      const xButton = dialog.locator('button[aria-label="Close"], .ant-modal-close, .ant-drawer-close').first();
      if ((await xButton.count()) > 0) {
        await xButton.click({ timeout: 3000 }).catch(() => {});
      } else {
        await page.keyboard.press("Escape").catch(() => {});
      }
    }
    await page.waitForTimeout(300);
  }
  await page.keyboard.press("Escape").catch(() => {});
};

const isHardApiStatus = (status) => status >= 400 && status !== 401 && status !== 403 && status !== 429;
const isHardConsoleError = (item) =>
  item.type === "error" &&
  !/429|Too Many Requests|请求过于频繁|Warning:/.test(item.text || "");

const gotoAuthenticatedRoute = async (page, route) => {
  await page.goto(`${ROOT}${route}`, { waitUntil: "domcontentloaded", timeout: 20000 });
  await waitQuiet(page);
  if (await isLoginPage(page)) {
    await ensureAuthenticated(page);
    await page.goto(`${ROOT}${route}`, { waitUntil: "domcontentloaded", timeout: 20000 });
    await waitQuiet(page);
  }
};

const runRoute = async (page, route) => {
  const routeReport = {
    route,
    startedAt: new Date().toISOString(),
    loaded: false,
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

  console.log(`\n[route] ${route}`);
  await gotoAuthenticatedRoute(page, route);
  routeReport.loaded = true;
  await saveScreenshot(page, routeReport, route);
  if (await isLoginPage(page)) {
    routeReport.authFailure = true;
    routeReport.skipped.push({ label: route, reason: "still-on-login-page" });
    writeReport();
    return;
  }

  const buttons = await snapshotButtons(page);
  routeReport.buttonsFound = buttons.length;
  const candidates = buttons.filter((button) => {
    const label = normalizeText(button.text || button.aria || button.title);
    return label && !loginPagePattern.test(label);
  }).slice(0, buttonLimit);

  for (const button of candidates) {
    const label = normalizeText(button.text || button.aria || button.title);
    if (dangerousPattern.test(label)) {
      routeReport.skipped.push({ label, reason: "dangerous-write-action" });
      report.skippedTotal += 1;
      continue;
    }
    if (label.length > 40 && !/(新建|新增|创建|添加|刷新|搜索|筛选|重置|详情|查看|展开|收起|更多)/.test(label)) {
      routeReport.skipped.push({ label, reason: "long-non-action-text" });
      report.skippedTotal += 1;
      continue;
    }

    if (new URL(page.url()).pathname !== route || (await isLoginPage(page))) {
      await gotoAuthenticatedRoute(page, route);
    }
    const beforeUrl = page.url();
    const beforeErrors = {
      apiErrors: report.apiErrors.length,
      rateLimitErrors: report.rateLimitErrors.length,
      pageErrors: report.pageErrors.length,
      requestFailures: report.requestFailures.length,
    };
    try {
      let locator = page.locator("main button").nth(button.index);
      if (!(await locator.isVisible({ timeout: 1000 }).catch(() => false))) {
        locator = page
          .locator("main button")
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
      };
      routeReport.clicked.push({ label, changedUrl, newErrors });
      report.clickedTotal += 1;
      if (newErrors.apiErrors || newErrors.pageErrors || newErrors.requestFailures) {
        await saveScreenshot(page, routeReport, `${route}-${label}-error`);
      }
      await closeTransientUi(page);
      if (changedUrl) {
        await page.goBack({ waitUntil: "domcontentloaded", timeout: 10000 }).catch(() => {});
        await waitQuiet(page);
        if (new URL(page.url()).pathname !== route || (await isLoginPage(page))) {
          await gotoAuthenticatedRoute(page, route).catch(() => {});
        }
      }
      await page.waitForTimeout(actionDelayMs);
    } catch (error) {
      const message = error?.message || String(error);
      routeReport.clicked.push({ label, index: button.index, error: message });
      await saveScreenshot(page, routeReport, `${route}-${label}-click-failed`);
      await closeTransientUi(page);
      await gotoAuthenticatedRoute(page, route).catch(() => {});
      await page.waitForTimeout(actionDelayMs);
    }
  }

  routeReport.apiErrors = report.apiErrors.slice(baseline.apiErrors);
  routeReport.rateLimitErrors = report.rateLimitErrors.slice(baseline.rateLimitErrors);
  routeReport.pageErrors = report.pageErrors.slice(baseline.pageErrors);
  routeReport.requestFailures = report.requestFailures.slice(baseline.requestFailures);
  routeReport.consoleErrors = report.console.slice(baseline.console).filter((item) => item.type === "error");
  writeReport();
};

const main = async () => {
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
        body: (await response.text().catch(() => "")).slice(0, 500),
      });
    } else if (url.includes("/api/") && isHardApiStatus(status)) {
      report.apiErrors.push({
        url,
        status,
        method: response.request().method(),
        pageUrl: page.url(),
        body: (await response.text().catch(() => "")).slice(0, 500),
      });
    }
  });

  try {
    await ensureAuthenticated(page);
    for (const route of selectedRoutes) {
      await runRoute(page, route);
      if (routeDelayMs > 0) {
        await page.waitForTimeout(routeDelayMs);
      }
    }
  } finally {
    await browser.close().catch(() => {});
  }

  const file = writeReport();
  const hardErrorCount =
    report.apiErrors.length +
    report.pageErrors.length +
    report.requestFailures.length +
    report.console.filter(isHardConsoleError).length;
  const consoleErrorCount = report.console.filter(isHardConsoleError).length;
  const clickErrorCount = report.routes.reduce(
    (sum, route) => sum + route.clicked.filter((item) => item.error).length,
    0,
  );
  const authFailureCount = report.routes.filter((route) => route.authFailure).length;
  console.log(
    JSON.stringify(
      {
        file,
        routes: report.routes.length,
        clickedTotal: report.clickedTotal,
        skippedTotal: report.skippedTotal,
        hardErrorCount,
        clickErrorCount,
        authFailureCount,
        apiErrors: report.apiErrors.length,
        rateLimitErrors: report.rateLimitErrors.length,
        pageErrors: report.pageErrors.length,
        requestFailures: report.requestFailures.length,
        consoleErrors: consoleErrorCount,
        consoleItems: report.console.length,
      },
      null,
      2,
    ),
  );
  if (hardErrorCount > 0 || clickErrorCount > 0 || authFailureCount > 0) {
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
