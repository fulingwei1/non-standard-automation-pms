// 命令栏执行动作真实浏览器验证：Cmd/Ctrl+K → "新建商机/客户 …" → 自动开对话框并 AI 预填
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";

const require = createRequire(new URL("../../frontend/package.json", import.meta.url));
const { chromium } = require("playwright");

const ROOT = process.env.QA_ROOT || "http://localhost:5175";
const USERNAME = process.env.QA_USER || "fulingwei";
const PASSWORD = process.env.QA_PASSWORD || "Demo@12345";
const headless = process.env.QA_HEADLESS !== "0";
const stamp = new Date().toISOString().replace(/[-:TZ.]/g, "").slice(0, 14);
const reportDir = path.resolve(".gstack/qa-reports");
fs.mkdirSync(path.join(reportDir, "screenshots"), { recursive: true });

const report = { stamp, root: ROOT, steps: [], consoleErrors: [], pageErrors: [], apiErrors: [] };
const step = (name, ok, detail = "") => {
  report.steps.push({ name, ok, detail });
  console.log(`${ok ? "✅" : "❌"} ${name}: ${detail}`);
};

const openCommandBar = async (page, text) => {
  const input = page.locator('input[placeholder*="输入指令或问题"]');
  for (const combo of ["Control+KeyK", "Meta+KeyK"]) {
    await page.locator("body").click({ position: { x: 5, y: 5 } }).catch(() => {});
    await page.keyboard.press(combo);
    const visible = await input.waitFor({ state: "visible", timeout: 3000 }).then(() => true).catch(() => false);
    if (visible) break;
  }
  await input.waitFor({ state: "visible", timeout: 3000 });
  await input.fill(text);
  await input.press("Enter");
};

const run = async () => {
  const browser = await chromium.launch({ headless });
  const page = await browser.newPage();
  page.on("console", (m) => {
    if (m.type() === "error") report.consoleErrors.push(m.text().slice(0, 200));
  });
  page.on("pageerror", (e) => report.pageErrors.push(String(e).slice(0, 200)));
  page.on("response", (r) => {
    if (r.url().includes("/api/") && r.status() >= 400)
      report.apiErrors.push(`${r.status()} ${r.request().method()} ${new URL(r.url()).pathname}`);
  });

  await page.goto(`${ROOT}/login`, { waitUntil: "domcontentloaded" });
  await page.locator('input[placeholder="请输入用户名"]').fill(USERNAME);
  await page.locator('input[placeholder="请输入密码"]').fill(PASSWORD);
  await page.getByRole("button", { name: /^登录$/ }).click();
  await page.waitForURL((u) => new URL(u).pathname !== "/login", { timeout: 20000 });
  step("登录", true, page.url());

  // ---- 动作1：新建商机 ----
  await openCommandBar(page, "新建商机 给宁德时代做电池模组视觉检测线，节拍18秒，预算120万，2026年Q4交付");
  await page.waitForURL((u) => new URL(u).pathname === "/sales/opportunities", { timeout: 60000 });
  step("命令栏动作→跳转商机页", true, page.url());
  await page.locator('text=新建商机').first().waitFor({ timeout: 15000 });
  await page.waitForFunction(
    () => {
      const inputs = [...document.querySelectorAll("input")];
      return inputs.some((i) => i.placeholder === "请输入商机名称" && i.value.length > 0);
    },
    { timeout: 90000 }
  );
  const oppName = await page.locator('input[placeholder="请输入商机名称"]').inputValue();
  const estAmount = await page.locator('input[placeholder="请输入预估金额"]').inputValue();
  step("对话框自动打开且AI预填", oppName.length > 0, `名称=${oppName} 金额=${estAmount}`);
  await page.screenshot({ path: path.join(reportDir, `screenshots/ai-cmd-action-opp-${stamp}.png`) });
  await page.keyboard.press("Escape");
  await page.waitForTimeout(400);

  // ---- 动作2：新建客户 ----
  await openCommandBar(page, "录入一个新客户：深圳做锂电池PACK的比克动力，联系人王工");
  await page.waitForURL((u) => new URL(u).pathname === "/sales/customers", { timeout: 60000 });
  step("命令栏动作→跳转客户页", true, page.url());
  await page.waitForFunction(
    () => {
      const inputs = [...document.querySelectorAll("input")];
      return inputs.some((i) => i.placeholder === "请输入公司全称" && i.value.length > 0);
    },
    { timeout: 90000 }
  );
  const custName = await page.locator('input[placeholder="请输入公司全称"]').inputValue();
  step("客户对话框自动打开且AI预填", custName.length > 0, `公司全称=${custName}`);
  await page.screenshot({ path: path.join(reportDir, `screenshots/ai-cmd-action-cust-${stamp}.png`) });
  await page.keyboard.press("Escape");

  // ---- 回归：导航意图仍工作 ----
  await openCommandBar(page, "打开PMO");
  await page.waitForURL((u) => new URL(u).pathname.startsWith("/pmo"), { timeout: 60000 });
  step("导航意图回归", true, page.url());

  await browser.close();
};

run()
  .catch((e) => step("运行异常", false, String(e).slice(0, 300)))
  .finally(() => {
    const file = path.join(reportDir, `ai-command-action-sweep-${stamp}.json`);
    fs.writeFileSync(file, JSON.stringify(report, null, 2));
    console.log("report:", file);
    const failed = report.steps.filter((s) => !s.ok).length;
    console.log(`steps=${report.steps.length} failed=${failed} apiErrors=${report.apiErrors.length} consoleErrors=${report.consoleErrors.length} pageErrors=${report.pageErrors.length}`);
    process.exit(failed ? 1 : 0);
  });
