# P0 动态复现验收套件 (`tests/audit_p0`)

对 2026-07-03 功能审计报告（`~/Desktop/FUNCTIONAL_AUDIT.md` 第二节「全局 P0 问题清单」）
的 17 项 P0 做**动态复现**，并固化为 pytest 验收用例。

## 设计约定

- **断言的是「正确行为」**（例：作废发票 PUT 改回 ISSUED 应被拒绝）。因此在问题**未修复前，
  这些用例必然 FAIL**——FAIL = 问题仍在；修复后转 GREEN = 验收通过。
- **绝不碰真库**：所有用例运行在 `data/app.db` 的一次性沙箱副本上。conftest 会把真库复制到
  临时目录、改副本里的 admin 密码，并用 `DATABASE_URL` 指向副本另起一个 uvicorn 后端；
  测试结束 kill 该进程。真库全程只读。

## 运行方式

全量 pytest 会 OOM，请只跑本套件：

```bash
cd /Users/flw/non-standard-automation-pm
.venv/bin/python -m pytest tests/audit_p0 -m audit_p0
```

首次运行会冷启动一个沙箱后端（约 1 分钟）。若已有指向**沙箱**的后端在跑，可复用它跳过冷启动：

```bash
AUDIT_P0_BASE_URL=http://127.0.0.1:8123 .venv/bin/python -m pytest tests/audit_p0 -m audit_p0
```

（默认自起端口 8199，可用 `AUDIT_P0_PORT` 覆盖。）

## 用例与 P0 对应

| 文件 | P0 | 复现手段 |
|---|---|---|
| test_p0_01_approval_template_mismatch | 1 四条审批链模板错位 | DB：4 个业务 code 在 approval_templates 无命中 |
| test_p0_02_approval_template_no_seed | 2 模板无种子 | 子进程跑 init_db 后 approval_templates=0 |
| test_p0_03_quote_fund_trio | 3 报价资金三连 | API：状态直改自批 / 审批后改明细 / cost 漏乘 qty |
| test_p0_04_payment_no_reconciliation | 4 回款无勾稽 | API：超发票额回款成功（负数已被 schema 拦，记为偏差） |
| test_p0_05_cosign_reject_flip | 5 会签翻转 | 内存审批引擎：AND_SIGN 汇总失败、OR_SIGN 等待其他审批人、终态防复活 |
| test_p0_06_receipt_no_stock | 6 收货不入库 | 源码接线：receipts 不调 InboundService |
| test_p0_07_shortage_scan_500 | 7 缺料扫描崩溃 | API：POST scan 返回 500 |
| test_p0_08_closure_gate_and_change_baseline | 8 结项门禁+变更基线 | API 结项 + 源码变更审批不回基线 |
| test_p0_09_field_checkin_fake | 9 现场调试假实现 | API 签到成功但 field_checkins 无新增 |
| test_p0_10_stub_tasks | 10 stub 任务 | 导入调用 14 个 stub 返回 {"status":"stub"} |
| test_p0_11_notification_fake_success | 11 通知假成功 | 直调 email/sms send 返回 success=True；841 PENDING |
| test_p0_12_bom_workorder_broken | 12 BOM→工单断链 | 静态：工单模型无 bom 字段、WorkOrderBom 无业务读写 |
| test_p0_13_device_archive_missing | 13 售后无设备档案 | PRAGMA：缺列 |
| test_p0_14_dispatch_conflict | 14 派工冲突空转 | 依赖表缺失 + 端点恒 0 冲突 |
| test_p0_15_forecast_hardcoded | 15 预测硬编码 | API 返回写死常量 28500000/华南大区 |
| test_p0_16_invoice_gate | 16 发票门禁 | API：未审批可开票 + 作废可改回 ISSUED |
| test_p0_17_contract_withdraw_typeerror | 17 撤回 TypeError | 引擎签名 + 4 处调用点误传 user_id= |

说明：部分用例采用「源码接线 / PRAGMA / 导入直调」而非纯 HTTP 流。原因是这些 P0 的根因就在
「代码根本不接线 / 表/列缺失 / 函数是空壳」，此类复现比端到端造数更稳、更直指根因，且同样是对
运行期行为的判定（导入的是产品代码、查询的是运行库）。
