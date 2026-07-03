import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";

const require = createRequire(new URL("../../frontend/package.json", import.meta.url));
const { chromium } = require("playwright");

const ROOT = process.env.QA_ROOT || "http://127.0.0.1:5173";
const USERNAME = process.env.QA_USER || "admin";
const PASSWORD = process.env.QA_PASSWORD || "admin123";
const headless = process.env.QA_HEADLESS !== "0";
const stamp = new Date().toISOString().replace(/[-:TZ.]/g, "").slice(0, 14);
const runPrefix = `QA_FULL_${stamp}`;
const reportDir = path.resolve(".gstack/qa-reports");
const screenshotDir = path.join(reportDir, "screenshots");
fs.mkdirSync(screenshotDir, { recursive: true });

const report = {
  stamp,
  runPrefix,
  root: ROOT,
  headless,
  steps: [],
  created: {
    customers: [],
    leads: [],
    opportunities: [],
    quotes: [],
    contracts: [],
    invoices: [],
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
  const file = path.join(reportDir, `sales-full-crud-sweep-${stamp}.json`);
  fs.writeFileSync(file, JSON.stringify(report, null, 2));
  return file;
};

const normalizeText = (text) => String(text || "").replace(/\s+/g, " ").trim();

const parseJson = (text) => {
  try {
    return text ? JSON.parse(text) : null;
  } catch {
    return null;
  }
};

const saveScreenshot = async (page, label) => {
  const safe = label.replace(/[^a-z0-9\u4e00-\u9fa5_-]+/gi, "_").slice(0, 100);
  const file = path.join(screenshotDir, `sales-full-${safe}-${stamp}.png`);
  await page.screenshot({ path: file, fullPage: true }).catch(() => {});
  report.screenshots.push(file);
  return file;
};

const waitQuiet = async (page, settleMs = 450) => {
  await page.waitForLoadState("networkidle", { timeout: 2500 }).catch(() => {});
  await page.waitForTimeout(settleMs);
};

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

const unwrap = (payload) => payload?.data?.data ?? payload?.data ?? payload ?? {};
const listItems = (payload) => {
  const data = unwrap(payload);
  if (Array.isArray(data)) {
    return data;
  }
  return data.items || [];
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
      return {
        ok: response.ok,
        status: response.status,
        json,
        text,
      };
    },
    { method, apiPath, body },
  );

  if (!result.ok) {
    throw new Error(`${method} ${apiPath} -> ${result.status}: ${result.text?.slice(0, 300)}`);
  }
  return result.json;
};

const findByKeyword = async (page, apiPath, keyword) => {
  const separator = apiPath.includes("?") ? "&" : "?";
  const payload = await browserApi(
    page,
    "GET",
    `${apiPath}${separator}page=1&page_size=1000&keyword=${encodeURIComponent(keyword)}`,
  );
  return listItems(payload).find((item) =>
    JSON.stringify(item).toLowerCase().includes(String(keyword).toLowerCase()),
  );
};

const runStep = async (page, name, fn) => {
  const step = {
    name,
    startedAt: new Date().toISOString(),
    status: "running",
  };
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

const waitForApi = async (page, method, pattern, action) => {
  const responsePromise = page.waitForResponse(
    (response) =>
      response.url().includes(pattern) &&
      response.request().method().toUpperCase() === method.toUpperCase(),
    { timeout: 15000 },
  ).then(
    (response) => ({ response }),
    (error) => ({ error }),
  );
  await action();
  const { response, error } = await responsePromise;
  if (error) {
    throw error;
  }
  const body = await response.text().catch(() => "");
  if (!response.ok()) {
    throw new Error(`${method} ${pattern} -> ${response.status()}: ${body.slice(0, 300)}`);
  }
  return { status: response.status(), body };
};

const visibleDialog = (page, titleText) =>
  page.locator('[role="dialog"]').filter({ hasText: titleText }).last();

const selectAntdOption = async (page, container, placeholder, optionText) => {
  const select = container.locator(".ant-select").filter({ hasText: placeholder }).first();
  await select.click();
  await page.waitForTimeout(150);
  const input = select.locator('input[role="combobox"]').first();
  if (await input.isVisible().catch(() => false)) {
    await input.fill("");
    await input.fill(String(optionText).slice(0, 60));
  }
  const dropdown = page.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden)").last();
  await dropdown.waitFor({ state: "visible", timeout: 5000 });
  const option = dropdown
    .locator(".ant-select-item-option")
    .filter({ hasText: String(optionText).slice(0, 30) })
    .first();
  await option.click({ timeout: 5000 });
};

const createCustomerViaUi = async (page, customerName) => {
  await page.goto(`${ROOT}/sales/customers`, { waitUntil: "domcontentloaded", timeout: 20000 });
  await waitQuiet(page);
  await page.getByRole("button", { name: /新建客户/ }).first().click();
  const dialog = visibleDialog(page, "新建客户");
  await dialog.locator('input[placeholder="请输入公司全称"]').fill(customerName);
  await dialog.locator('input[placeholder="请输入公司简称"]').fill(customerName.slice(0, 18));
  await dialog.locator("select").nth(0).selectOption("B");
  await dialog.locator("select").nth(1).selectOption("智能制造");
  await dialog.locator('input[placeholder="请输入联系人姓名"]').fill("QA联系人");
  await dialog.locator('input[placeholder="请输入联系电话"]').fill("13800000000");
  await dialog.locator('input[placeholder="请输入公司地址"]').fill("QA自动化测试地址");
  await dialog.locator("textarea").fill(`自动化全量测试创建: ${customerName}`);
  await waitForApi(page, "POST", "/api/v1/customers/", async () => {
    await dialog.getByRole("button", { name: /创建客户/ }).click();
  });
  await waitQuiet(page);

  const created = await findByKeyword(page, "/customers/", customerName);
  if (!created?.id) {
    throw new Error(`客户创建后未能通过 API 查到: ${customerName}`);
  }
  report.created.customers.push({ id: created.id, name: customerName, deleted: false });
  return created;
};

const deleteCustomerViaUi = async (page, customer) => {
  await page.goto(`${ROOT}/sales/customers`, { waitUntil: "domcontentloaded", timeout: 20000 });
  await waitQuiet(page);
  await page.locator('button:has(svg[class*="lucide-list"])').first().click();
  await page.getByPlaceholder("搜索客户名称、联系人...").fill(customer.customer_name || customer.name);
  await page.waitForTimeout(500);

  const row = page.locator("tbody tr").first();
  if (!(await row.isVisible({ timeout: 5000 }).catch(() => false))) {
    throw new Error("客户表格中未找到待删除行");
  }
  await row.locator("button").last().click();
  await page.getByRole("menuitem", { name: /删除/ }).click();
  const confirm = visibleDialog(page, "确认删除客户");
  await waitForApi(page, "DELETE", `/api/v1/customers/${customer.id}`, async () => {
    await confirm.getByRole("button", { name: /^删除$/ }).click();
  });
  await waitQuiet(page);

  const remaining = await findByKeyword(page, "/customers/", customer.customer_name || customer.name);
  if (remaining?.id === customer.id) {
    throw new Error("UI 删除客户后 API 仍能查到该客户");
  }
  const tracked = report.created.customers.find((item) => item.id === customer.id);
  if (tracked) {
    tracked.deleted = true;
  }
};

const createLeadViaUi = async (page, customer, leadName) => {
  await page.goto(`${ROOT}/sales/leads`, { waitUntil: "domcontentloaded", timeout: 20000 });
  await waitQuiet(page);
  await page.getByRole("button", { name: /新建线索/ }).first().click();
  const dialog = visibleDialog(page, "新建线索");
  const customerSelect = dialog.locator("select").first();
  const hasCustomerOption = await customerSelect
    .locator("option")
    .filter({ hasText: customer.customer_name })
    .count();
  if (hasCustomerOption > 0) {
    await customerSelect.selectOption({ label: customer.customer_name });
  } else {
    await dialog.locator('input[placeholder="或输入新客户名称"]').fill(customer.customer_name);
  }
  await dialog.locator("select").nth(1).selectOption({ index: 1 });
  await dialog.locator('input[placeholder="请输入行业"]').fill("智能制造");
  await dialog.locator('input[placeholder="请输入联系人"]').fill("QA线索联系人");
  await dialog.locator('input[placeholder="请输入联系电话"]').fill("13900000000");
  await dialog.locator("textarea").fill(`${leadName} 需求摘要：FCT 自动化测试线体，节拍 1 秒，RS232/以太网接口，现场空间受限，按 FAT/SAT 验收。`);
  await waitForApi(page, "POST", "/api/v1/sales/leads", async () => {
    await dialog.getByRole("button", { name: /^创建$/ }).click();
  });
  await waitQuiet(page);

  const created = await findByKeyword(page, "/sales/leads", customer.customer_name);
  if (!created?.id) {
    throw new Error(`线索创建后未能通过 API 查到: ${customer.customer_name}`);
  }
  report.created.leads.push({ id: created.id, customer_name: customer.customer_name, deleted: false });
  return created;
};

const editLeadViaUi = async (page, customerName, updatedContact) => {
  await page.goto(`${ROOT}/sales/leads`, { waitUntil: "domcontentloaded", timeout: 20000 });
  await waitQuiet(page);
  await page.getByPlaceholder("搜索线索编码、客户名称、联系人...").fill(customerName);
  await page.waitForTimeout(500);
  await page.getByRole("button", { name: /^编辑$/ }).first().click();
  const dialog = visibleDialog(page, "编辑线索");
  await dialog.locator("input").nth(3).fill(updatedContact);
  await waitForApi(page, "PUT", "/api/v1/sales/leads/", async () => {
    await dialog.getByRole("button", { name: /^保存$/ }).click();
  });
  await waitQuiet(page);
};

const addLeadFollowUpViaUi = async (page, customerName, content) => {
  await page.goto(`${ROOT}/sales/leads`, { waitUntil: "domcontentloaded", timeout: 20000 });
  await waitQuiet(page);
  await page.getByPlaceholder("搜索线索编码、客户名称、联系人...").fill(customerName);
  await page.waitForTimeout(500);
  await page.getByRole("button", { name: /^跟进$/ }).first().click();
  const dialog = visibleDialog(page, "添加跟进记录");
  await dialog.locator("textarea").fill(content);
  await dialog.locator('input[placeholder="如：发送报价单"]').fill("发送 QA 自动化测试报价资料");
  await waitForApi(page, "POST", "/api/v1/sales/leads/", async () => {
    await dialog.getByRole("button", { name: /^保存$/ }).click();
  });
  await waitQuiet(page);
};

const convertLeadViaUi = async (page, customerName, customerId) => {
  await page.goto(`${ROOT}/sales/leads`, { waitUntil: "domcontentloaded", timeout: 20000 });
  await waitQuiet(page);
  await page.getByPlaceholder("搜索线索编码、客户名称、联系人...").fill(customerName);
  await page.waitForTimeout(500);
  await page.getByRole("button", { name: /转商机/ }).first().click();
  const dialog = visibleDialog(page, "线索转商机");
  await dialog.locator("select").selectOption(String(customerId));
  const confirm = visibleDialog(page, "确认快速转商机");
  await waitForApi(page, "POST", "/api/v1/sales/leads/", async () => {
    await confirm.getByRole("button", { name: /跳过并转换/ }).click();
  });
  await waitQuiet(page, 800);
};

const createQuoteViaUi = async (page, opportunity, customer, quoteName) => {
  await page.goto(
    `${ROOT}/sales/quotes/create?opportunity_id=${opportunity.id}&customer_id=${customer.id}`,
    { waitUntil: "domcontentloaded", timeout: 20000 },
  );
  await waitQuiet(page, 800);
  await page.locator('input[placeholder="报价名称"]').fill(quoteName);
  await page.getByRole("button", { name: /添加第一条明细|添加明细/ }).first().click();
  const row = page.locator("tbody tr").first();
  await row.locator('input[placeholder="编码"]').fill(`${runPrefix.slice(-8)}-ITEM`);
  await row.locator('input[placeholder="名称"]').fill("QA自动化测试设备");
  await row.locator('input[placeholder="规格"]').fill("FCT-1S-RS232");
  await row.locator('input[placeholder="单位"]').fill("套");
  const numberInputs = row.locator('input[type="number"]');
  await numberInputs.nth(0).fill("2");
  await numberInputs.nth(1).fill("100000");
  await numberInputs.nth(3).fill("50000");
  await numberInputs.nth(4).fill("5000");
  await numberInputs.nth(5).fill("5000");
  await row.locator('input[placeholder="备注"]').fill("QA 全流程报价明细");

  const response = await waitForApi(page, "POST", "/api/v1/sales/quotes", async () => {
    await page.getByRole("button", { name: /^保存$/ }).click();
  });
  await waitQuiet(page, 800);
  let quote = null;
  try {
    quote = JSON.parse(response.body || "{}");
  } catch {
    quote = null;
  }
  const quoteId = quote?.id || quote?.data?.id;
  if (!quoteId) {
    throw new Error(`报价创建响应未返回 id: ${response.body?.slice(0, 300)}`);
  }
  report.created.quotes.push({ id: quoteId, quote_code: quote.quote_code || quote?.data?.quote_code, deleted: false });
  return { id: quoteId, quote_code: quote.quote_code || quote?.data?.quote_code };
};

const createContractViaUi = async (page, opportunity, customer) => {
  await page.goto(`${ROOT}/sales/contracts`, { waitUntil: "domcontentloaded", timeout: 20000 });
  await waitQuiet(page, 1000);
  await page.getByRole("button", { name: /创建合同/ }).first().click();
  const dialog = visibleDialog(page, "创建合同");
  await dialog.waitFor({ state: "visible", timeout: 8000 });
  await waitQuiet(page, 1000);

  await dialog.locator('input[placeholder="客户侧合同编号"]').fill(`${runPrefix}-CNO`);
  await selectAntdOption(page, dialog, "选择商机", opportunity.opp_name || customer.customer_name);
  await selectAntdOption(page, dialog, "选择客户", customer.customer_name);
  await dialog.locator('input[placeholder="金额（元）"]').fill("220000");
  await dialog.locator('input[placeholder="YYYY-MM-DD"]').fill("2026-07-01");
  await dialog.locator('textarea[placeholder^="例如"]').fill("30%预付款，60%发货前，10%验收后");
  await dialog.locator('textarea[placeholder^="填写合同"]').fill("QA 自动化销售全流程合同，按 FAT/SAT 验收");

  const response = await waitForApi(page, "POST", "/api/v1/sales/contracts", async () => {
    await page.locator("button").filter({ hasText: /保\s*存/ }).last().click();
  });
  await waitQuiet(page, 1000);
  const contract = parseJson(response.body || "{}") || {};
  const contractId = contract?.id || contract?.data?.id;
  if (!contractId) {
    throw new Error(`合同创建响应未返回 id: ${response.body?.slice(0, 300)}`);
  }
  const tracked = {
    id: contractId,
    contract_code: contract.contract_code || contract?.data?.contract_code,
    deleted: false,
  };
  report.created.contracts.push(tracked);
  return tracked;
};

const createInvoiceViaUi = async (page, contract, amount, remark) => {
  await page.goto(`${ROOT}/invoices`, { waitUntil: "domcontentloaded", timeout: 20000 });
  await waitQuiet(page, 1000);
  await page.getByRole("button", { name: /新建发票/ }).first().click();
  const dialog = visibleDialog(page, "新建发票");
  await dialog.waitFor({ state: "visible", timeout: 8000 });

  const contractSelect = dialog.locator("select").first();
  await contractSelect.locator(`option[value="${contract.id}"]`).waitFor({ state: "attached", timeout: 8000 });
  await contractSelect.selectOption(String(contract.id));
  await dialog.locator('input[placeholder="请输入金额"]').fill(String(amount));
  await dialog.locator('input[placeholder="13"]').fill("13");
  await dialog.locator('input[type="date"]').nth(0).fill("2026-07-01");
  await dialog.locator('input[type="date"]').nth(1).fill("2026-07-31");
  await dialog.locator('textarea[placeholder="请输入备注"]').fill(remark);

  const response = await waitForApi(page, "POST", "/api/v1/sales/invoices", async () => {
    await dialog.getByRole("button", { name: /^创建$/ }).click();
  });
  await waitQuiet(page, 1000);
  const invoice = parseJson(response.body || "{}") || {};
  const invoiceId = invoice?.id || invoice?.data?.id;
  if (!invoiceId) {
    throw new Error(`发票创建响应未返回 id: ${response.body?.slice(0, 300)}`);
  }
  const tracked = {
    id: invoiceId,
    invoice_code: invoice.invoice_code || invoice.invoice_no || invoice?.data?.invoice_code,
    deleted: false,
  };
  report.created.invoices.push(tracked);
  return tracked;
};

const findInvoiceRow = async (page, invoice) => {
  await page.goto(`${ROOT}/invoices`, { waitUntil: "domcontentloaded", timeout: 20000 });
  await waitQuiet(page, 1000);
  const keyword = invoice.invoice_code || String(invoice.id);
  await page.locator('input[placeholder="搜索发票号、项目名、客户名..."]').fill(keyword);
  await waitQuiet(page, 700);
  const row = page.locator(".group").filter({ hasText: keyword }).first();
  await row.waitFor({ state: "visible", timeout: 8000 });
  return row;
};

const deleteDraftInvoiceViaUi = async (page, invoice) => {
  const row = await findInvoiceRow(page, invoice);
  await row.hover();
  await row.locator('button[title="删除"]').click();
  const confirm = visibleDialog(page, "确认删除");
  await waitForApi(page, "DELETE", `/api/v1/sales/invoices/${invoice.id}`, async () => {
    await confirm.getByRole("button", { name: /^删除$/ }).click();
  });
  await waitQuiet(page, 800);
  const tracked = report.created.invoices.find((item) => item.id === invoice.id);
  if (tracked) {
    tracked.deleted = true;
  }
};

const issueInvoiceViaUi = async (page, invoice) => {
  await browserApi(page, "PUT", `/sales/invoices/${invoice.id}`, { status: "APPROVED" });
  const row = await findInvoiceRow(page, invoice);
  await row.hover();
  await row.locator('button[title="开票"]').click();
  const dialog = visibleDialog(page, "开票");
  await dialog.waitFor({ state: "visible", timeout: 5000 });
  await dialog.locator('input[placeholder="请输入发票号码"]').fill(`${runPrefix.slice(-10)}-INV`);
  await dialog.locator('textarea[placeholder="请输入备注"]').fill("QA 自动化开票");
  await waitForApi(page, "POST", `/api/v1/sales/invoices/${invoice.id}/issue`, async () => {
    await dialog.getByRole("button", { name: /确认开票/ }).click();
  });
  await waitQuiet(page, 1000);
};

const receiveInvoicePaymentViaUi = async (page, invoice, amount) => {
  const row = await findInvoiceRow(page, invoice);
  await row.hover();
  await row.locator('button[title="记录收款"]').click();
  const dialog = visibleDialog(page, "记录收款");
  await dialog.waitFor({ state: "visible", timeout: 5000 });
  await dialog.locator('input[placeholder="请输入收款金额"]').fill(String(amount));
  await dialog.locator('textarea[placeholder="请输入备注"]').fill("QA 自动化收款");
  await waitForApi(page, "POST", `/api/v1/sales/invoices/${invoice.id}/receive-payment`, async () => {
    await dialog.getByRole("button", { name: /确认收款/ }).click();
  });
  await waitQuiet(page, 1000);
};

const cleanupCreatedData = async (page) => {
  for (const invoice of [...report.created.invoices].reverse()) {
    if (invoice.deleted) {
      continue;
    }
    try {
      const current = unwrap(await browserApi(page, "GET", `/sales/invoices/${invoice.id}`));
      if (current.status === "DRAFT") {
        await browserApi(page, "DELETE", `/sales/invoices/${invoice.id}`);
        invoice.deleted = true;
        report.cleanup.push({ type: "invoice", id: invoice.id, status: "deleted" });
      } else {
        await browserApi(page, "DELETE", `/sales/payments/records/${invoice.id}`).catch(() => {});
        await browserApi(page, "PUT", `/sales/invoices/${invoice.id}`, { status: "DRAFT" });
        await browserApi(page, "DELETE", `/sales/invoices/${invoice.id}`);
        invoice.deleted = true;
        report.cleanup.push({ type: "invoice", id: invoice.id, status: "reset-and-deleted" });
      }
    } catch (error) {
      report.cleanup.push({
        type: "invoice",
        id: invoice.id,
        status: "failed",
        error: error.message,
      });
    }
  }
  for (const contract of [...report.created.contracts].reverse()) {
    if (contract.deleted) {
      continue;
    }
    try {
      await browserApi(page, "DELETE", `/sales/contracts/${contract.id}`);
      contract.deleted = true;
      report.cleanup.push({ type: "contract", id: contract.id, status: "deleted" });
    } catch (error) {
      report.cleanup.push({ type: "contract", id: contract.id, status: "failed", error: error.message });
    }
  }
  for (const quote of [...report.created.quotes].reverse()) {
    if (quote.deleted) {
      continue;
    }
    try {
      await browserApi(page, "DELETE", `/sales/quotes/${quote.id}`);
      quote.deleted = true;
      report.cleanup.push({ type: "quote", id: quote.id, status: "deleted" });
    } catch (error) {
      report.cleanup.push({ type: "quote", id: quote.id, status: "failed", error: error.message });
    }
  }
  for (const opportunity of [...report.created.opportunities].reverse()) {
    if (opportunity.deleted) {
      continue;
    }
    try {
      await browserApi(page, "DELETE", `/sales/opportunities/${opportunity.id}`);
      opportunity.deleted = true;
      report.cleanup.push({ type: "opportunity", id: opportunity.id, status: "deleted" });
    } catch (error) {
      report.cleanup.push({ type: "opportunity", id: opportunity.id, status: "failed", error: error.message });
    }
  }
  for (const lead of [...report.created.leads].reverse()) {
    if (lead.deleted) {
      continue;
    }
    try {
      await browserApi(page, "DELETE", `/sales/leads/${lead.id}`);
      lead.deleted = true;
      report.cleanup.push({ type: "lead", id: lead.id, status: "deleted" });
    } catch (error) {
      report.cleanup.push({ type: "lead", id: lead.id, status: "failed", error: error.message });
    }
  }
  for (const customer of [...report.created.customers].reverse()) {
    if (customer.deleted) {
      continue;
    }
    try {
      await browserApi(page, "DELETE", `/customers/${customer.id}`);
      customer.deleted = true;
      report.cleanup.push({ type: "customer", id: customer.id, status: "deleted" });
    } catch (error) {
      report.cleanup.push({ type: "customer", id: customer.id, status: "failed", error: error.message });
    }
  }
};

const main = async () => {
  const browser = await chromium.launch({ headless });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });

  page.on("console", (msg) => {
    if (msg.type() === "error" || msg.type() === "warning") {
      report.console.push({
        type: msg.type(),
        text: msg.text(),
        url: page.url(),
        at: new Date().toISOString(),
      });
    }
  });
  page.on("pageerror", (error) => {
    report.pageErrors.push({ message: error.message, stack: error.stack, url: page.url() });
  });
  page.on("requestfailed", (request) => {
    const failure = request.failure()?.errorText;
    if (failure !== "net::ERR_ABORTED") {
      report.requestFailures.push({ url: request.url(), method: request.method(), failure, pageUrl: page.url() });
    }
  });
  page.on("response", async (response) => {
    const status = response.status();
    const url = response.url();
    if (url.includes("/api/") && status >= 400 && status !== 401 && status !== 403 && status !== 429) {
      report.apiErrors.push({
        url,
        status,
        method: response.request().method(),
        pageUrl: page.url(),
        body: (await response.text().catch(() => "")).slice(0, 500),
      });
    }
  });
  page.on("dialog", async (dialog) => {
    report.dialogs.push({
      type: dialog.type(),
      message: dialog.message(),
      url: page.url(),
      at: new Date().toISOString(),
    });
    await dialog.accept().catch(() => {});
  });

  const customerToDeleteName = `${runPrefix}_客户删除`;
  const customerFlowName = `${runPrefix}_客户主流程`;
  const leadFlowName = `${runPrefix}_线索主流程`;

  try {
    await ensureAuthenticated(page);

    let customerToDelete = null;
    await runStep(page, "客户-UI创建待删除客户", async () => {
      customerToDelete = await createCustomerViaUi(page, customerToDeleteName);
      return { id: customerToDelete.id, name: customerToDelete.customer_name };
    });

    await runStep(page, "客户-UI表格菜单删除客户", async () => {
      if (!customerToDelete) {
        throw new Error("缺少待删除客户");
      }
      await deleteCustomerViaUi(page, customerToDelete);
      return { id: customerToDelete.id };
    });

    let flowCustomer = null;
    await runStep(page, "客户-UI创建主流程客户", async () => {
      flowCustomer = await createCustomerViaUi(page, customerFlowName);
      return { id: flowCustomer.id, name: flowCustomer.customer_name };
    });

    let lead = null;
    await runStep(page, "线索-UI创建线索", async () => {
      lead = await createLeadViaUi(page, flowCustomer, leadFlowName);
      return { id: lead.id, customer_name: lead.customer_name };
    });

    await runStep(page, "线索-UI编辑线索", async () => {
      await editLeadViaUi(page, flowCustomer.customer_name, "QA线索联系人已更新");
      const updated = await browserApi(page, "GET", `/sales/leads/${lead.id}`);
      const data = unwrap(updated);
      if (data.contact_name !== "QA线索联系人已更新") {
        throw new Error(`线索编辑后联系人未更新，实际值: ${data.contact_name}`);
      }
      return { id: lead.id, contact_name: data.contact_name };
    });

    await runStep(page, "线索-UI添加跟进", async () => {
      const content = `${runPrefix} 跟进记录`;
      await addLeadFollowUpViaUi(page, flowCustomer.customer_name, content);
      const payload = await browserApi(page, "GET", `/sales/leads/${lead.id}/follow-ups`);
      const followUps = Array.isArray(unwrap(payload)) ? unwrap(payload) : [];
      if (!followUps.some((item) => item.content?.includes(runPrefix))) {
        throw new Error("跟进记录保存后未能查到");
      }
      return { id: lead.id, followUps: followUps.length };
    });

    await runStep(page, "线索-UI转商机", async () => {
      await convertLeadViaUi(page, flowCustomer.customer_name, flowCustomer.id);
      const updated = unwrap(await browserApi(page, "GET", `/sales/leads/${lead.id}`));
      if (updated.status !== "CONVERTED") {
        throw new Error(`线索转商机后状态不是 CONVERTED，实际: ${updated.status}`);
      }
      const opportunity = await findByKeyword(page, "/sales/opportunities", flowCustomer.customer_name);
      if (!opportunity?.id) {
        throw new Error("线索转商机后未找到关联商机");
      }
      report.created.opportunities.push({ id: opportunity.id, opp_name: opportunity.opp_name, deleted: false });
      return { leadId: lead.id, opportunityId: opportunity.id };
    });

    await runStep(page, "报价-UI创建报价并清理", async () => {
      const opportunity = report.created.opportunities.at(-1);
      if (!opportunity?.id) {
        throw new Error("缺少线索转出的商机");
      }
      const quote = await createQuoteViaUi(
        page,
        opportunity,
        flowCustomer,
        `${runPrefix}_销售报价`,
      );
      return quote;
    });

    let contract = null;
    await runStep(page, "合同-UI创建合同", async () => {
      const opportunity = report.created.opportunities.at(-1);
      if (!opportunity?.id) {
        throw new Error("缺少线索转出的商机");
      }
      contract = await createContractViaUi(page, opportunity, flowCustomer);
      return contract;
    });

    await runStep(page, "发票-UI创建草稿并删除", async () => {
      if (!contract?.id) {
        throw new Error("缺少合同");
      }
      const invoice = await createInvoiceViaUi(page, contract, 55000, "QA 自动化草稿发票删除测试");
      await deleteDraftInvoiceViaUi(page, invoice);
      return { id: invoice.id, invoice_code: invoice.invoice_code };
    });

    await runStep(page, "发票-UI创建开票并收款", async () => {
      if (!contract?.id) {
        throw new Error("缺少合同");
      }
      const invoice = await createInvoiceViaUi(page, contract, 66000, "QA 自动化开票收款测试");
      await issueInvoiceViaUi(page, invoice);
      await receiveInvoicePaymentViaUi(page, invoice, 66000);
      const updated = unwrap(await browserApi(page, "GET", `/sales/invoices/${invoice.id}`));
      if (updated.status !== "ISSUED" || updated.payment_status !== "PAID") {
        throw new Error(
          `发票收款后状态异常: status=${updated.status}, payment_status=${updated.payment_status}`,
        );
      }
      return { id: invoice.id, invoice_code: invoice.invoice_code, payment_status: updated.payment_status };
    });
  } finally {
    await cleanupCreatedData(page).catch((error) => {
      report.cleanup.push({ type: "fatal", status: "failed", error: error.message });
    });
    await browser.close().catch(() => {});
  }

  const file = writeReport();
  const failedSteps = report.steps.filter((step) => step.status === "failed").length;
  const cleanupFailures = report.cleanup.filter((item) => item.status === "failed").length;
  const hardConsoleErrors = report.console.filter(
    (item) => item.type === "error" && !/Warning:|429|Too Many Requests/.test(item.text),
  ).length;
  const summary = {
    file,
    runPrefix,
    steps: report.steps.length,
    failedSteps,
    apiErrors: report.apiErrors.length,
    pageErrors: report.pageErrors.length,
    requestFailures: report.requestFailures.length,
    consoleItems: report.console.length,
    hardConsoleErrors,
    cleanupFailures,
    cleanup: report.cleanup,
  };
  console.log(JSON.stringify(summary, null, 2));
  if (
    failedSteps > 0 ||
    report.apiErrors.length > 0 ||
    report.pageErrors.length > 0 ||
    report.requestFailures.length > 0 ||
    hardConsoleErrors > 0 ||
    cleanupFailures > 0
  ) {
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
