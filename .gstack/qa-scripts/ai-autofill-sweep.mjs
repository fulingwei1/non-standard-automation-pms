// AI 智能表单填充（AutofillBar）真实浏览器验证：新建商机 + 新建客户对话框
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";

const require = createRequire(new URL("../../frontend/package.json", import.meta.url));
const { chromium } = require("playwright");

const ROOT = process.env.QA_ROOT || "http://127.0.0.1:5174";
const USERNAME = process.env.QA_USER || "fulingwei";
const PASSWORD = process.env.QA_PASSWORD || "Demo@12345";
const headless = process.env.QA_HEADLESS !== "0";
const stamp = new Date().toISOString().replace(/[-:TZ.]/g, "").slice(0, 14);
const reportDir = path.resolve(".gstack/qa-reports");
fs.mkdirSync(reportDir, { recursive: true });

const report = { stamp, root: ROOT, steps: [], consoleErrors: [], pageErrors: [], apiErrors: [] };
const step = (name, ok, detail = "") => {
  report.steps.push({ name, ok, detail });
  console.log(`${ok ? "✅" : "❌"} ${name}: ${detail}`);
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

  // 登录
  await page.goto(`${ROOT}/login`, { waitUntil: "domcontentloaded" });
  await page.locator('input[placeholder="请输入用户名"]').fill(USERNAME);
  await page.locator('input[placeholder="请输入密码"]').fill(PASSWORD);
  await page.getByRole("button", { name: /^登录$/ }).click();
  await page.waitForURL((u) => new URL(u).pathname !== "/login", { timeout: 20000 });
  step("登录", true, page.url());

  // ---- 新建商机对话框 ----
  await page.goto(`${ROOT}/sales/opportunities`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(1500);
  await page.getByRole("button", { name: /新建商机/ }).first().click();
  await page.waitForTimeout(500);
  const oppBar = page.locator('input[placeholder*="宁德时代"]');
  step("商机对话框含AI填充条", (await oppBar.count()) > 0);
  await oppBar.fill("给宁德时代做电池模组视觉检测线，节拍18秒，预算120万，2026年Q4交付，验收误判率低于0.3%");
  await page.getByRole("button", { name: "AI 填充" }).click();
  await page.waitForFunction(
    () => {
      const inputs = [...document.querySelectorAll("input")];
      return inputs.some((i) => i.placeholder === "请输入商机名称" && i.value.length > 0);
    },
    { timeout: 60000 }
  );
  const oppName = await page.locator('input[placeholder="请输入商机名称"]').inputValue();
  const estAmount = await page.locator('input[placeholder="请输入预估金额"]').inputValue();
  const ct = await page.locator('input[placeholder="如: 1"]').inputValue();
  step("商机字段已AI回填", oppName.length > 0 && estAmount.length > 0, `名称=${oppName} 金额=${estAmount} 节拍=${ct}`);
  await page.screenshot({ path: path.join(reportDir, `screenshots/ai-autofill-opp-${stamp}.png`) });
  await page.keyboard.press("Escape");

  // ---- 新建客户对话框 ----
  await page.goto(`${ROOT}/sales/customers`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(1500);
  await page.getByRole("button", { name: /新建客户|新增客户/ }).first().click();
  await page.waitForTimeout(500);
  const custBar = page.locator('input[placeholder*="比克动力"]');
  step("客户对话框含AI填充条", (await custBar.count()) > 0);
  await custBar.fill("深圳做锂电池PACK的比克动力，联系人王工");
  await page.getByRole("button", { name: "AI 填充" }).click();
  await page.waitForFunction(
    () => {
      const inputs = [...document.querySelectorAll("input")];
      return inputs.some((i) => i.placeholder === "请输入公司全称" && i.value.length > 0);
    },
    { timeout: 60000 }
  );
  const custName = await page.locator('input[placeholder="请输入公司全称"]').inputValue();
  step("客户字段已AI回填", custName.length > 0, `公司全称=${custName}`);
  await page.screenshot({ path: path.join(reportDir, `screenshots/ai-autofill-cust-${stamp}.png`) });

  await browser.close();
};

run()
  .catch((e) => {
    step("运行异常", false, String(e).slice(0, 300));
  })
  .finally(() => {
    const file = path.join(reportDir, `ai-autofill-sweep-${stamp}.json`);
    fs.writeFileSync(file, JSON.stringify(report, null, 2));
    console.log("report:", file);
    const failed = report.steps.filter((s) => !s.ok).length;
    console.log(`steps=${report.steps.length} failed=${failed} apiErrors=${report.apiErrors.length} consoleErrors=${report.consoleErrors.length} pageErrors=${report.pageErrors.length}`);
    process.exit(failed ? 1 : 0);
  });
