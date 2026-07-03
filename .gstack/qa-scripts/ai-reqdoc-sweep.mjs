// 一步式需求文档上传真实浏览器验证：传需求文档 → 抽取回填面板 → 自动缺口分析
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";

const require = createRequire(new URL("../../frontend/package.json", import.meta.url));
const { chromium } = require("playwright");

const ROOT = process.env.QA_ROOT || "http://localhost:5175";
const OPP_ID = process.env.QA_OPP_ID;
const DOC = process.env.QA_DOC;
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
  if (!OPP_ID || !DOC) throw new Error("需要 QA_OPP_ID 和 QA_DOC");
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
  await page.getByRole("button", { name: /传需求文档/ }).waitFor({ timeout: 20000 });
  step("商机详情页含上传按钮", true, "");

  await page.locator('input[type="file"]').setInputFiles(DOC);
  await page.locator("text=/需求文档已入库并完成 AI 需求抽取/").waitFor({ timeout: 180000 });
  const info = await page.locator("text=/提取 \\d+ 字/").first().innerText();
  step("上传+抽取面板", true, info.trim().slice(0, 60));
  const hasBackfill = (await page.locator("text=/抽取回填：/").count()) > 0;
  step("抽取回填摘要", hasBackfill, "");

  // 一步式自动触发缺口分析
  await page.locator("text=/需求完备度 \\d+\\/100/").waitFor({ timeout: 120000 });
  const scoreTxt = await page.locator("text=/需求完备度 \\d+\\/100/").first().innerText();
  step("自动缺口分析", true, scoreTxt.trim().slice(0, 40));
  await page.screenshot({ path: path.join(reportDir, `screenshots/ai-reqdoc-${stamp}.png`) });

  await browser.close();
};

run()
  .catch((e) => step("运行异常", false, String(e).slice(0, 300)))
  .finally(() => {
    const file = path.join(reportDir, `ai-reqdoc-sweep-${stamp}.json`);
    fs.writeFileSync(file, JSON.stringify(report, null, 2));
    console.log("report:", file);
    const failed = report.steps.filter((s) => !s.ok).length;
    console.log(`steps=${report.steps.length} failed=${failed} apiErrors=${report.apiErrors.length} consoleErrors=${report.consoleErrors.length} pageErrors=${report.pageErrors.length}`);
    process.exit(failed ? 1 : 0);
  });
