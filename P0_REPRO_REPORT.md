# P0 动态复现验收报告

- 对象：`/Users/flw/non-standard-automation-pm`
- 依据：`~/Desktop/FUNCTIONAL_AUDIT.md`（2026-07-03 静态审计）第二节「全局 P0 问题清单」共 17 项
- 方法：在 `data/app.db` 的**一次性沙箱副本**上另起 uvicorn 后端（`DATABASE_URL` 覆盖），
  逐项动态复现，并固化为 pytest 验收用例（`tests/audit_p0/`，标记 `@pytest.mark.audit_p0`）
- 运行：`.venv/bin/python -m pytest tests/audit_p0 -m audit_p0`
  （首次自动冷启一个沙箱后端，约 1 分钟；结束自动 kill）
- 原始结果快照：**47 failed / 4 passed / 1 skipped**。全部 failed 即“正确行为”断言在当时代码上不成立
  = 问题复现；4 passed 为取证/守卫用例；1 skipped 为当时受限项（P0-5）。
- 2026-07-03 补充：P0-5/APPR-03 已改为稳定的内存审批引擎动态复现与回归用例，
  覆盖会签汇总失败、或签等待其他审批人、终态 REJECTED 禁止复活。
- 2026-07-03 补充：P0-7/PROD-02 已修复智能缺料预警扫描字段错配，`test_p0_07`
  从 HTTP 500 红灯转为回归通过；库存/在途数据真实性仍依赖 PROD-03/04。
- 2026-07-03 补充：P0-6/PROD-03 已接通采购收货质检合格后的入库链路，
  `test_p0_06` 从源码接线红灯转为回归通过；PO/POI 状态流转已由 PROD-11 补齐。
- 2026-07-03 补充：P0-6/PROD-11/PROD-22 已补齐采购收货创建后的
  PO/POI `PARTIAL_RECEIVED/RECEIVED` 状态流转、收货明细金额和订单已收金额；在途读侧口径仍归 PROD-04。

---

## 0. 安全核查事故与结论（应主会话要求插入）

主会话发现 `data/app.db` mtime 在 08:11 被触碰。核查结论：**真库内容未被本会话改动**，8123
沙箱后端确指向副本，非真库。三重证据：

1. **lsof/密码法**：8123 后端用“只在沙箱副本里改过的 admin 密码”登录成功（HTTP 200）；真库
   admin 的 `password_hash` 头部与沙箱不同（`$2b$12$/LKl50bN…` vs `$2b$12$f165EIX…`），
   若后端连真库该密码必失败。
2. **marker 法**：向沙箱副本 `users` 插入唯一用户 `audit_marker_zx9`；真库该用户数 **=0**；
   8123 以该 marker 用户登录 **HTTP 200** → API 读的是沙箱副本。
3. **写入取证**：本会话所有写操作（改密码、insert marker、造数）均以沙箱绝对路径为目标；
   复查真库 `select count(*) where username='audit_marker_zx9'` **=0**，无任何本会话写入。

**mtime 触碰的成因判定**：本机另有一个**先于本会话存在**的 dev uvicorn（pid 95459，端口 8002，
06:18 启动）指向真库 `data/app.db`，其正常运行/WAL checkpoint 会刷新 mtime；该进程非本会话
启动、本会话未与之交互。本会话自起的后端全程指向副本。结束时本会话启动的后端已全部 kill。

---

## 1. 复现结果总表

| # | P0 | 复现方式 | 观察结果 | 结论 | 测试用例 |
|---|----|---------|---------|------|---------|
| 1 | 4 条审批链模板错位 | DB：4 个业务 `template_code` 在 `approval_templates` 是否有命中 | `PURCHASE_ORDER_APPROVAL/OUTSOURCING_ORDER_APPROVAL/ACCEPTANCE_ORDER_APPROVAL/PROJECT_TEMPLATE` 全部缺失；库内只有 `TPL_PURCHASE/TPL_OUTSOURCING/TPL_ACCEPTANCE/TPL_PROJECT` | **已复现** | `test_p0_01_approval_template_mismatch.py::test_business_template_code_resolves_to_a_template` |
| 2 | 审批模板无种子 | 子进程对全新库跑 `scripts/init_db.py` 后统计 `approval_templates` | 新库 `approval_templates` 行数 = 0 | **已复现** | `test_p0_02_approval_template_no_seed.py::test_fresh_init_db_seeds_approval_templates` |
| 3a | 报价状态直改绕审批 | API：`POST /quotes/4/status` new_status 两跳 DRAFT→PENDING_APPROVAL→APPROVED | 两跳均 HTTP 200，任意登录用户自助批准 | **已复现** | `test_p0_03_quote_fund_trio.py::test_quote_status_endpoint_must_not_self_approve` |
| 3b | 审批后可改明细 | API：对 APPROVED 版本 `PUT /quotes/items/{id}` | HTTP 200「报价明细更新成功」，无状态门禁 | **已复现** | `test_p0_03_quote_fund_trio.py::test_items_of_approved_quote_must_be_locked` |
| 3c | 成本汇总漏乘 qty | API：`GET /quotes/{id}/cost-breakdown`，比对 total_cost 与 Σ(qty×cost) | 返回 6773243.39 = Σ(cost)，应为 Σ(qty×cost)=19040825.62 → 毛利虚高 | **已复现** | `test_p0_03_quote_fund_trio.py::test_cost_breakdown_multiplies_by_quantity` |
| 4 | 回款无勾稽 | API：对有 ISSUED 发票的合同 `POST 回款`，金额远超发票额 | 回款 9,999,999 记入 474,000 的发票，paid=9,999,999、unpaid=-9,525,999，HTTP 200 | **已复现（部分偏差）** | `test_p0_04_payment_no_reconciliation.py::test_overpayment_beyond_invoice_amount_is_rejected` |
| 5 | 会签驳回可翻转 APPROVED | 内存审批引擎构造两人 AND_SIGN/OR_SIGN 节点 + 终态实例待办 | 修复前：会签/或签一票拒立即 REJECTED，终态 REJECTED 可被 pending 任务 approve 翻成 APPROVED；修复后 3 用例通过 | **已复现并回归** | `test_p0_05_cosign_reject_flip.py`（3 用例） |
| 6 | 收货不入库 | 源码接线 + API 契约：`purchase/receipts.py` 是否调 InboundService / 写库存/写收货进度 | 修复前 receipts 全文无库存入库接线且 PO/POI 状态不流转；修复后质检合格量写 MaterialStock、MaterialTransaction 与 material.current_stock，创建收货单写 PO/POI 收货状态、明细金额和订单已收金额 | **已复现并回归** | `test_p0_06_receipt_no_stock.py`（2 用例）+ `test_purchase_receipts_workflow_contracts.py::test_goods_receipt_creates_purchase_in_stock_transaction` + `test_purchase_receipts_workflow_contracts.py::test_goods_receipt_updates_order_item_status_and_amounts` |
| 7 | 缺料引擎崩溃 | API：`POST /shortage/smart-alerts/scan` | 修复前 HTTP 500，`AttributeError: WorkOrder.is_critical_path`；修复后扫描端点不再 5xx | **已复现并回归** | `test_p0_07_shortage_scan_500.py::test_smart_alert_scan_does_not_500` |
| 8a | 结项无门禁 | API：对 readiness=False 的项目 `POST closure` | readiness 明确 ready=false（0/8 阶段、缺验收），仍 HTTP 201 建结项，项目 status 不变 | **已复现** | `test_p0_08_closure_gate_and_change_baseline.py::test_closure_blocked_when_not_ready` |
| 8b | 变更不回基线 | 源码：`approve_change_request` 是否写 Project 基线 | 函数体无 `planned_end_date/budget_amount/execute_linkage` 任何写入 | **已复现** | `test_p0_08_…::test_change_approval_writes_project_baseline` |
| 9 | 现场调试假实现 | API：`POST /field/tasks/1/checkin` 后查 `field_checkins` | 返回「签到已记录」HTTP 200，但行数 3→3 无新增 | **已复现** | `test_p0_09_field_checkin_fake.py::test_field_checkin_persists_a_row` |
| 10 | 14 个 stub 定时任务 | 导入直调 `scheduled_tasks.stub_tasks` 的 14 个函数 | 全部返回 `{"status":"stub"}`；且它们在 `SCHEDULER_TASKS` 中被注册为 enabled cron | **已复现** | `test_p0_10_stub_tasks.py`（14 参数 + 注册统计） |
| 11 | 通知假成功 | 导入直调 email/sms `send`（无 SMTP/网关） | 两渠道均 `success=True`；佐证 `alert_records` PENDING=841 | **已复现** | `test_p0_11_notification_fake_success.py`（email/sms 2 用例，+背景取证） |
| 12 | BOM→工单断链 | 静态：工单模型有无 bom 字段；`WorkOrderBom` 有无业务读写 | WorkOrder 模型无 bom_* 字段；`WorkOrderBom` 仅在 models/exports 出现，无业务读写 | **已复现** | `test_p0_12_bom_workorder_broken.py`（2 用例） |
| 13 | 售后无设备档案 | PRAGMA：`service_tickets`/`machines` 列 | `service_tickets` 无 machine 外键；`machines` 无 serial_no/customer_id/warranty | **已复现（设计级）** | `test_p0_13_device_archive_missing.py`（4 用例） |
| 14 | 派工冲突空转 | DB：依赖表是否存在 + API conflict-detect | `engineer_task_assignments` 表不存在；conflict-detect 恒返回 conflict_count=0 | **已复现** | `test_p0_14_dispatch_conflict.py`（表缺失=fail；恒0=取证 pass） |
| 15 | 预测硬编码 | API：`GET /sales/forecast/*` | actual_revenue 恒 28500000、团队恒「华南大区」，与沙箱库无关 | **已复现** | `test_p0_15_forecast_hardcoded.py`（2 用例） |
| 16a | 未审批可开票 | API：对无审批实例发票 `POST /issue` | HTTP 200「发票开票成功」 | **已复现** | `test_p0_16_invoice_gate.py::test_issue_requires_an_approved_instance` |
| 16b | 作废发票改回 ISSUED | API：`PUT /invoices/{id}` CANCELLED→ISSUED | 两步均 HTTP 200，作废发票被改回 ISSUED | **已复现** | `test_p0_16_invoice_gate.py::test_cancelled_invoice_cannot_be_revived_to_issued` |
| 17 | 撤回 TypeError | 引擎签名 + 4 处调用点参数名 | 引擎 `withdraw(instance_id, initiator_id, comment)` 无 user_id；4 处服务均传 `user_id=` → TypeError（用 `user_id=` 调用实测 raise TypeError） | **已复现** | `test_p0_17_contract_withdraw_typeerror.py`（引擎守卫 + 4 调用点） |

---

## 2. 与静态结论不符 / 需要注意的偏差项

> 静态审计 17 项 P0 **无假阳性**——每一项的核心危害都在运行期成立。仅有以下**范围性偏差**需标注：

1. **P0-4 回款「可负」已被 schema 拦截（部分收窄）**。静态报告称「金额可负可超额」。实测：
   `PaymentRecordCreate.amount` 现已带 `Field(gt=0)`，**负数在入参层被 422 拒绝**
   （`test_negative_amount_is_rejected` 现在就 PASS）。但**「超发票额无上限勾稽」仍成立**：
   9,999,999 记入 474,000 的发票导致 unpaid=-9,525,999。故 P0-4 定级不变，仅“负数”这一子路径
   已随 pydantic 校验收窄。报告结论主体属实。

2. **P0-5 会签翻转：已补稳定动态复现**。原先 ECN 端到端造数前置不稳定，现改为直接构造
   内存审批引擎场景：两人 AND_SIGN、两人 OR_SIGN、以及终态 REJECTED + pending task。用例已捕获
   `engine.reject()` 不尊重汇总裁决、`approve()` 不校验实例终态导致的复活路径，并在 APPR-03 修复后转绿。

3. **复现手段说明（非偏差，防误读）**：P0-1/2/6/8b/10/11/12/13/17 采用 **DB 断言 / 子进程 init /
   源码接线 / 导入直调** 而非纯 HTTP 端到端。原因是这些 P0 的根因就是「代码根本不接线 / 表列缺失 /
   函数是空壳 / 无种子」——此类复现比端到端造数更稳、更直指根因，且判定对象仍是**运行期产物**
   （运行库结构、被导入的产品代码、被注册的调度任务）。P0-3/4/7/8a/9/14/15/16 为真·HTTP 动态复现。

---

## 3. 4 个 PASS 用例说明（取证/守卫，非漏报）

| 用例 | 含义 |
|---|---|
| `test_p0_04::test_negative_amount_is_rejected` | 记录「负数已被 schema 拦」这一偏差，现状即应通过 |
| `test_p0_11::test_alert_records_backlog_documented` | 取证 PENDING 预警积压 841 条（>500） |
| `test_p0_14::test_conflict_detect_endpoint_reports_structure` | 取证 conflict-detect 恒返回 0 冲突（空转） |
| `test_p0_17::test_engine_withdraw_signature_has_no_user_id` | 守卫根因：引擎签名无 user_id，`user_id=` 调用实测 TypeError |

其余每个 P0 均至少有一个「正确行为」用例当前为 FAIL —— 即问题在。修复后对应用例转 GREEN 即验收通过。
