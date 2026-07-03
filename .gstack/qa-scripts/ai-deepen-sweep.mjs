// AI 需求解读/技术方案深化真实浏览器验证：需求缺口追问 → 配置式设计落库+历史坑 → 符合性矩阵
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";

const require = createRequire(new URL("../../frontend/package.json", import.meta.url));
const { chromium } = require("playwright");

const ROOT = process.env.QA_ROOT || "http://localhost:5175";
const OPP_ID = process.env.QA_OPP_ID;
const USERNAME = process.env.QA_USER || "fulingwei";
const PASSWORD = process.env.QA_PASSWORD || "Demo@12345";
const headless = process.env.QA_HEADLESS !== "0";
const stamp = new Date().toISOString().replace(/[-:TZ.]/g, "").slice(0, 14);
const reportDir = path.resolve(".gstack/qa-reports");
fs.mkdirSync(path.join(reportDir, "screenshots"), { recursive: true });

const report = { stamp, root: ROOT, oppId: OPP_ID, steps: [], consoleErrors: [], pageErrors: [], apiErrors: [] };
const step = (name, ok, detail = "") => {
  report.steps.push({ name, ok, detail });
  console.log(`${ok ? "✅" : "❌"} ${name}: ${detail}`);
};

const run = async () => {
  if (!OPP_ID) throw new Error("需要 QA_OPP_ID");
  const browser = await chromium.launch({ headless });
  const page = await browser.newPage();
  page.on("console", (m) => { if (m.type() === "error") report.consoleErrors.push(m.text().slice(0, 200)); });
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
  step("登录", true, "");

  await page.goto(`${ROOT}/sales/opportunities/${OPP_ID}`, { waitUntil: "domcontentloaded" });
  await page.getByRole("button", { name: /需求缺口追问/ }).waitFor({ timeout: 20000 });
  step("商机详情页含新按钮", true, "");

  // 需求缺口追问
  await page.getByRole("button", { name: /需求缺口追问/ }).click();
  await page.locator("text=/需求完备度 \\d+\\/100/").waitFor({ timeout: 120000 });
  const scoreTxt = await page.locator("text=/需求完备度 \\d+\\/100/").first().innerText();
  const hasQuestions = (await page.locator("text=下次拜访追问清单").count()) > 0;
  step("需求缺口面板+追问清单", hasQuestions, scoreTxt.trim().slice(0, 40));
  await page.screenshot({ path: path.join(reportDir, `screenshots/ai-deepen-gaps-${stamp}.png`), fullPage: false });

  // 配置式设计（落库 + 历史坑 + 自动覆盖矩阵）
  await page.getByRole("button", { name: /配置式设计/ }).click();
  await page.locator("text=/已落库 SOL-/").waitFor({ timeout: 180000 });
  const solTxt = await page.locator("text=/已落库 SOL-/").first().innerText();
  const hasRisk = (await page.locator("text=历史坑提醒").count()) > 0;
  step("配置设计落库+历史坑提醒", hasRisk, solTxt.trim());
  await page.locator("text=需求-方案符合性矩阵").waitFor({ timeout: 180000 });
  const covTxt = await page.locator("text=/覆盖率 /").first().innerText();
  step("符合性矩阵面板", true, covTxt.trim().slice(0, 50));
  await page.screenshot({ path: path.join(reportDir, `screenshots/ai-deepen-design-${stamp}.png`), fullPage: false });

  await browser.close();
};

run()
  .catch((e) => step("运行异常", false, String(e).slice(0, 300)))
  .finally(() => {
    const file = path.join(reportDir, `ai-deepen-sweep-${stamp}.json`);
    fs.writeFileSync(file, JSON.stringify(report, null, 2));
    console.log("report:", file);
    const failed = report.steps.filter((s) => !s.ok).length;
    console.log(`steps=${report.steps.length} failed=${failed} apiErrors=${report.apiErrors.length} consoleErrors=${report.consoleErrors.length} pageErrors=${report.pageErrors.length}`);
    process.exit(failed ? 1 : 0);
  });
