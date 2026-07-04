# 功能审计问题追踪台账（FUNCTIONAL AUDIT TRACKER）

## 头部说明

- **来源**：`/Users/flw/Desktop/FUNCTIONAL_AUDIT.md`（2026-07-03 功能审计汇总报告，含全局 P0 表 / 六域详表 / 跨域矩阵），及六域原始报告（销售 sales / 售前 presale / 项目 project / 生产 production / 售后 aftersales / 审批 approval）+ 并行会话合同发票补充结论（peer）。所有证据均为 file:line 级，静态代码走读 + `data/app.db` 只读 SELECT 证实。
- **状态字典**：`待修` / `修复中` / `已修待验` / `已验证` / `不修-有意为之` / `重复-合并`。
- **维护规则**：修复 PR **必须在标题或描述中引用问题 ID**（如 `fix(SALES-03): 报价成本汇总补乘数量`）；状态变更随 PR 同步更新本表；重复项只在主项上推进进度，被合并项状态锁定为 `重复-合并→主ID` 不再单独流转。
- **ID 规则**：`SALES-xx / PRE-xx / PROJ-xx / PROD-xx / AS-xx / APPR-xx / PEER-xx`，**编号与各域报告《功能清单总表》序号一致**。注意：售前域与项目域的"逐问题详述"编号与总表不同，本表一律以总表序号为准，备注中标注对应详述编号（`详#n`）。
- **验证方式**：初始一律填"静态已证"；P0 项另标"待动态复现"（修复前先动态复现、修复后动态回归）。
- **正面确认行**（原报告标"可用/—"）：状态记 `已验证`，表示静态审计证实功能真实可用，非缺陷，列入台账仅为总表序号完整。

**总量（第一轮）**：148 行（SALES 22 / PRE 24 / PROJ 26 / PROD 24 / AS 25 / APPR 22 / PEER 5）。其中 P0 19 行、P1 74 行、P2 42 行、P3 5 行、正面确认 8 行（重复合并行按原等级计入）。跨域重复合并 5 行（AS-01→PROD-01、APPR-05→PROD-08、APPR-06→AS-10、PEER-03→APPR-07、PEER-04→APPR-11）+ 域内合并 1 行（PRE-02→PRE-14）+ 子项合并 1 处（APPR-22①→PRE-21）。

**总量（第二轮：平台/支撑/边缘域）**：120 行（HR 25 / PERM 23 / ADMIN 23 / TEN 8 / RPT 17 / MISC 24）。二轮 P0：ADMIN-01/ADMIN-02/ADMIN-03（备份三层皆虚集群）、ADMIN-18（合同附件任意文件读取 · 安全）、MISC-01（竞品分析菜单展示虚构数据）、HR-10（工程师五维绩效零落库 · 域内最重）共 6 项标 P0。二轮最重三发现：ADMIN-18 任意文件读取（P0 安全）、多租户"现在不能给第二个客户开租户"（TEN-01~07）、约 14% 端点（~427/3104）+137 模块前端零调用是僵尸。二轮跨轮关联/合并见各子表备注：MISC-12→HR-15（同一 performance_contract 裸 sqlite3，MISC-12 重复-合并）、RPT-15→ADMIN-05（同一 admin_stats 占位，ADMIN-05 主）；互引不合并：HR-22↔MISC-23（culture_wall）、HR-23↔MISC-02↔AS-24（resource_conflicts 空表/双轨）、HR-21/RPT-03↔PROJ-11/PROJ-13（时薪多口径）、RPT-09/RPT-10↔AS-13（schema 契约断裂）、MISC-09↔PROJ-11（成本归集）、MISC-03↔APPR-17/AS-25（同为通知/升级链但不同源）。

**P0 动态复现（17 项全局 P0）**：17/17 已动态复现；P0-5（会签驳回翻转 = APPR-03）已补稳定内存审批引擎复现并回归；P0-4（SALES-04）金额可负已被 pydantic Field(gt=0) 拦截（守卫 PASS），超额无勾稽仍成立，定级不变、危害描述删"可负"。详见 P0_REPRO_REPORT.md 与主表验证方式列。

**2026-07-03 止血进展**：APPR-01/APPR-02 已修复审批模板 code、全失败 200 掩盖与新库审批种子；APPR-03 已补稳定复现并修复会签/或签驳回汇总与终态防复活；APPR-07 已修复并回归；PRE-16 已修复 qwen/百炼 live AI 判断；PRE-23 已修复立项关卡异常静默放行；PROJ-06 已修复结项 readiness 强制门禁；PROJ-10 已修复里程碑完成门禁异常吞掉和全局 complete 旁路；PROD-02/03/04/11/12/14/22 已完成库存入库、在途、领料扣库、调拨动库与缺料扫描 500 止血回归；PROD-13 已修复完工报工审批后回写；MISC-01 已下架竞品分析假数据菜单/路由并让直链接口返回 501；SALES-01/02/03/04 已完成报价资金三连与回款勾稽止血回归；SALES-09/APPR-10/APPR-11/PEER-05 已完成发票资金门禁止血回归；SALES-14 已修复付款审批前端 404 断链；SALES-15 已修复销售团队统计/排名恒 0 桩；AS-02/AS-15 已修复邮件/短信触达假成功与工时提醒 SMTP 配置错位；AS-03 已修复通知队列默认同步止血与 worker 导入断裂；AS-06 已修复 SLA 历史 NULL 策略兼容与定时预警扫描；AS-16 已修复 Header 通知铃铛未读数与跳转；AS-25 已修复预警订阅默认接收人、双 notification resolver 兼容与通用 Webhook URL；APPR-16 已修复 ECN 超期检查调度模块路径；APPR-17 已修复预警通知状态流转和最老优先出队，历史积压需随调度/运维逐批处置；MISC-03 已修复预警超时升级查询短路和 OPEN 状态漏扫；AS-19 已修复客服关单 payload/id 与质保工单兜底列表；RPT-06 已修复报表中心 xlsx 明细导出；RPT-09 已修复统一工作台统计卡 label/title 契约断裂；RPT-11 已移除驾驶舱营收/毛利前端封顶和净利润误标；RPT-16 已验证负荷瓶颈部门名兼容；HR-01 已修复员工 Excel 导入运行时导入崩溃；APPR-04 已完成 P0#10 全量回归与缺料预警/紧急采购/缺料日报 3 件套回填，维保计划独立留 AS-14；PERM-11 已先补组织员工/HR 档案权限小切口；奖金 payment 端点已补 bonus 权限，HR-17 主审批链仍待修；PRE-21 已修复 AI 后台任务重启恢复与轮询超时；PRE-10 已打通 AI 需求分析下游（方案/报价自动带出 + 确认回填商机需求）。

**2026-07-04 止血进展**：RPT-02 已修复 PROJECT_MONTHLY 项目月报成本恒 0；now 按报表期间汇总 `ProjectCost` ACTUAL 口径与 `FinancialProjectCost`。RPT-03 已修复 COST_ANALYSIS 人工成本按工时硬编码 ×100；now 旧 `report_data_generation` 与新 `report_framework` 成本分析均按工时人员+工作日期读取 `HourlyRateService` 配置。RPT-04 已修复财务报表空数据 demo 兜底和成本预算 ×1.08；now 四个报表端点无真实数据返回空列表，成本分析预算读取已审批启用预算明细。RPT-10 已修复决策驾驶舱活跃项目/交付准时率 KPI 绑定不存在字段恒 0；KPI now 优先使用 summary 显式字段，否则使用已拉取的 delivery-rate 数据和项目总数。RPT-12 已修复驾驶舱健康分布结果丢弃、成本/销售漏斗 state 无 setter 恒空；now 使用健康分布、summary 成本、销售漏斗真实接口。RPT-13 已修复采购看板“节省金额”后端硬编码 0；now 按来源采购申请预估金额与关联采购订单实际金额聚合正差。RPT-14 已修复成本看板图表配置保存/读取桩；now 配置落库、读取缺失返回 404，静态读取路由排在动态项目路由前。AS-09 已修复售后扩展表缺失导致质保/备件/满意度等端点 500；AS-13 已修复客户 360 四页签字段断链并接入服务工单。

**2026-07-04 追加进展**：RPT-01 已修复报表中心“待实现”桩静默空 200；now 报表类型配置和角色权限矩阵只展示真实可生成的 6 类报表，绕过前端直调未实现类型时返回 error，不再生成空报表记录。RPT-08 已修复 PPT 生成器硬编码 demo；now 主生成入口必须显式传入 `deck_spec`，生成内容完全来自调用方数据，旧硬编码营销文案已移除，并补齐 builder 兼容路径。RPT-07 已收敛 template_report 三套实现；now adapter、旧根服务、数据服务都走 `TemplateReportCore`，断链 import 已移除。RPT-05/SALES-17 已补报价版本、合同和财务报表含税/不含税建模；now 报价/报价版本保存 `amount_without_tax/tax_rate/tax_amount/amount_with_tax`，合同从报价继承税口径，财务月趋势/成本分析/项目盈利/现金流显式返回不含税、税额和含税字段。SALES-19 已修复已收款发票作废红冲链路；now 作废已开票单生成 `RED_CREDIT` 负票并保留原回款审计痕迹，合同累计开票额度排除红冲负票。ADMIN-18 已修复合同附件下载任意文件读取；now 新旧两个合同附件下载入口都把路径解析到 `UPLOAD_DIR` 内，绝对路径/路径穿越返回 403。AS-14 已修复设备保养提醒调度与终验转售后定期保养计划联动。HR-21 已修复时薪全级 miss 静默兜底与费率改删无留痕；now API 返回来源/兜底标记，PUT 生成新版本并到期旧版本，DELETE 软停用保留历史查询。HR-02 已修复离职审批后账号仍可登录；now 审批 resignation 会同步停用绑定 `User` 并返回停用账号数。HR-06/07 已完成考勤假数据止损；now `/admin/attendance` 返回显式空态，不再合成迟到/请假/出勤率，打卡/单条记录未接真实域时返回 501。

---

## 主表

### 一、销售域（SALES，22 项）

| ID | 功能/问题 | 等级 | 状态 | 证据位置 | 工作量 | 验证方式 | 备注/关联 |
|---|---|---|---|---|---|---|---|
| SALES-01 | 报价状态直改端点绕过审批（任意登录用户可自助批准） | P0 | 已验证 | sales/quote_status.py；tests/api/test_sales_quote_status_contracts.py | 0.5-1d | ✅已动态复现并回归（test_p0_03，2026-07-03） | 全局P0#3；资金急救包；状态直改端点不再允许 `PENDING_APPROVAL→APPROVED/REJECTED` |
| SALES-02 | 审批通过后仍可改报价明细，版本总额不重算 | P0 | 已验证 | sales/quote_items.py；models/sales/quotes.py；tests/api/test_sales_quote_item_contracts.py | 1-2d | ✅已动态复现并回归（test_p0_03，2026-07-03） | 全局P0#3；资金急救包；已审批/已提交/已发送等报价或版本冻结，草稿明细写入后重算版本金额 |
| SALES-03 | 报价成本汇总漏乘数量，毛利率虚高 | P0 | 已验证 | sales/quote_costs.py；tests/api/test_sales_quote_costs_quantity_contracts.py | 0.5d+存量重算0.5d | ✅已动态复现并回归（test_p0_03，2026-07-03） | 全局P0#3；资金急救包；成本汇总按 `Σ(qty*cost)`，本地有明细版本已重算 |
| SALES-04 | 回款登记无勾稽/无权限/错配发票（可超额） | P0 | 已验证 | sales/payments/payment_records.py；tests/api/test_sales_payment_record_contracts.py | 2-3d | ✅已动态复现并回归（test_p0_04，2026-07-03） | 全局P0#4；资金急救包；登记/更新拒绝超发票未收/总额，核销要求路径回款与发票一致，权限按合同负责人过滤 |
| SALES-05 | 商机赢/输单可非法跳转（LOST→WON），前端走的正是无守卫 PUT | P1 | 已验证 | sales/opportunity_crud.py；sales/opportunity_workflow.py；sales/opportunity_batch.py；sales/utils/stage_guard.py；tests/api/test_sales.py | 1d | 静态已证；✅已动态复现并回归（2026-07-03） | 通用 PUT、旧 /stage、旧 PUT /win 现已不能把 LOST 终态翻回 WON；批量阶段更新复用同一阶段守卫；前端 sales.js:46 |
| SALES-06 | 销售预测线上接口整文件硬编码，真算法服务是死代码 | P1 | 已验证 | sales/sales_forecast.py；services/sales_forecast_service.py；tests/unit/test_sales_forecast_wiring.py | 3-5d | 静态已证；✅契约+P0复现回归（2026-07-03）；✅复核通过（2026-07-04） | 全局P0#15；company-overview 已接线真服务（修模型漂移：Contract 小写状态/est_amount/终态阶段剔除）；其余 8 个零消费假端点 501 下架；团队/个人/驾驶舱做实待排期（ROADMAP F6） |
| SALES-07 | 目标预测页前端假数据兜底、AI 预测卡纯常量 | P1 | 已验证 | ForecastDashboard.jsx | 1-2d | 静态已证；✅构建+lint 通过（2026-07-03）；✅前端 build+eslint 复跑（2026-07-04） | AI 预测卡改调真接口（失败显式"暂不可用"）；漏斗改真实枚举键；目标/团队/个人假兜底全部改空态；驾驶舱 tab（整段编造数字）下架 |
| SALES-08 | 销售目标 actual_value 无自动回填，达成率口径未定义 | P1 | 已验证 | sales/targets.py；sales_team_service.calculate_target_performance；tests/unit/test_sales_target_actuals.py | 2d | 静态已证；✅契约测试回归（2026-07-03）；✅复核通过（2026-07-04） | 列表接口接线 calculate_target_performance 实时计算（LEAD/OPP 按 owner 计数、CONTRACT_AMOUNT 按合同负责人金额、COLLECTION 按发票实收；达成率=actual/target*100）；团队/部门级目标归集口径待定返回 0 |
| SALES-09 | 发票写操作只挂 finance:read + 未签署（草稿）合同可开票 | P1 | 已验证 | sales/invoices/basic.py；sales/invoices/operations.py；models/sales/invoices.py；tests/api/test_sales_invoice_gate_contracts.py | 1d | 静态已证；✅已动态回归（2026-07-03） | 资金急救包；写入口改为 finance:create/update/delete，未签署合同禁止开票，金额上限与状态字段门禁已补 |
| SALES-10 | 合同审批 F1 复核：模板数据已补，但 200 掩盖失败与种子缺口仍在 | P1 | 已验证 | sales/contracts/approval.py；api/v1/endpoints/approval_submit_guard.py；app/utils/init_approval_data.py；tests/api/test_approval_submit_error_contracts.py | 0.5-1d | 静态已证；✅已动态回归（2026-07-03） | 关联 APPR-01/APPR-02；合同审批全失败提交不再 200，新库审批模板种子已补 |
| SALES-11 | 线索转商机丢字段 + 前端写死 skip_validation 绕 G1 | P1 | 已验证 | leads/actions.py；LeadManagement.jsx；tests/unit/test_lead_convert_carryover.py | 1-2d | 静态已证；✅契约测试回归（2026-07-04）；✅复核通过（2026-07-04） | 北极星项；转商机自动承接 LeadRequirementDetail（对象/节拍/接口/验收/安全/成熟度/交期，显式传入优先只补空位）；前端默认走 G1，未通过展示缺口由人决定"带缺口转换"（不再默认绕门） |
| SALES-12 | 报价转合同前端断链（后端 from-quote 齐备、前端零入口，金额/版本ID手填） | P1 | 已验证 | QuoteDetailDialog.jsx；services/api/sales.js；__tests__/QuoteDetailDialog.fromQuote.test.jsx | 2d | 静态已证；✅组件测试回归（2026-07-04）；✅复跑 59 个前端用例+build（2026-07-04） | 北极星项；报价详情 APPROVED/ACCEPTED 显示"转合同"一键调 from-quote（客户/商机/金额/版本自动带出，G3 拦截缺口展示给人）；附注"报价明细不成交付物"=APPR-18（以 APPR-18 为主） |
| SALES-13 | 智能报价整页假实现（历史价/竞品/折扣/赢单率全硬编码） | P1 | 已验证 | sales/intelligent_quote.py；salesRoutes.jsx；tests/unit/test_intelligent_quote_stopgap.py | 下架0.5d/做实5d+ | 静态已证；✅契约测试回归（2026-07-04）；✅复核通过（2026-07-04） | historical-prices 已做实（WON 商机×已签合同真实成交价，兼容侧栏旧结构）；竞品/最优价/折扣/赢单率 5 端点 501 下架；/sales/intelligent-quote 与 /sales/win-rate-prediction 假页路由摘除（SalesFunnel 入口改跳商机详情）；做实排期 ROADMAP F5 |
| SALES-14 | 付款审批页前端调不存在接口，必 404 | P1 | 已验证 | frontend/src/services/api/paymentApproval.js；frontend/src/pages/PaymentApproval/hooks/usePaymentApproval.js；frontend/src/services/api/__tests__/paymentApproval.test.js；frontend/src/pages/PaymentApproval/hooks/__tests__/usePaymentApproval.test.js | 1d | 静态已证；✅已动态复现并回归（2026-07-03） | 付款审批服务改走统一审批 `/approvals/pending/*` 与 `/approvals/tasks/*`，清除 `/sales/payments/approvals` 404 断链 |
| SALES-15 | 销售团队统计/排名多维度恒 0 桩 | P1 | 已验证 | app/services/sales_team_service.py；app/services/sales_ranking_service.py；app/api/v1/endpoints/sales/team/utils.py；tests/services/test_sales_team_aggregation_contracts.py | 2-3d | 静态已证；✅已动态复现并回归（2026-07-03） | 个人目标、最近跟进、客户分布、跟进统计、线索质量、商机统计均改为真实聚合；/sales/team 与 /sales/team/ranking 消费同一真实 Session 数据 |
| SALES-16 | AI 销售助手降级罐头文本无标注；流失清单从不调 AI | P2 | 已验证 | sales_ai_assistant_service.py；tests/unit/test_sales_ai_degradation_marking.py；SalesAI/index.jsx | 1d | 静态已证；✅契约测试回归（2026-07-03）；✅复核通过（2026-07-04） | mock 集群（集群2）；5 方法降级统一标 ai_generated/degraded/degraded_reason，真 AI 标 ai_generated=true；流失清单定口径为规则批量扫描（scoring_method=rule_scan+每项 analysis_source），单客户深评走 predict_churn_risk 真 AI；前端 4 卡片显示降级横幅 |
| SALES-17 | 报价域无税率/含税建模 | P2 | 已验证 | quotes.py；quote_versions.py；contracts/basic.py；models/sales；schemas/sales；migrations/versions/20260704_add_sales_tax_basis.py；tests/unit/test_finance_reports_rpt05.py | 2-3d | 静态已证；✅已动态回归（2026-07-04） | 报价版本 now 保存不含税/税率/税额/含税额；报价转合同继承税口径；旧 `total_price/total_amount` 继续兼容总价 |
| SALES-18 | 报价"当前版本"口径不一致（versions[-1] vs current_version_id） | P2 | 已验证 | quote_costs.py；tests/api/test_sales_quote_costs_quantity_contracts.py | 0.5d | 静态已证；✅已动态复现并回归（2026-07-03） | 成本分析当前版本改为优先使用 Quote.current_version_id，与报价详情/统计一致；无 current_version_id 时才显式回退最新创建版本 |
| SALES-19 | 发票作废无红冲（需先删回款，审计链断） | P2 | 已验证 | sales/invoices/operations.py；sales/invoices/basic.py；tests/api/test_sales_invoice_gate_contracts.py | 2d | 静态已证；✅已动态复现并回归（2026-07-04） | 已收款已开票作废 now 生成 `RED_CREDIT` 负票并返回红冲单号，原票保留 paid_amount/备注审计链；合同累计开票额度排除红冲负票，关联 PEER-05 |
| SALES-20 | 报价数量/单价无 0/负数校验 | P2 | 已验证 | sales/utils/quote_item_validation.py；quotes.py；quote_versions.py；quote_items.py；schemas/sales/quotes.py；QuoteItemsTable.jsx；tests/api/test_sales.py；QuoteCreateEdit.test.jsx | 0.5d | 静态已证；✅已动态复现并回归（2026-07-03） | 首版创建、版本创建、明细新增/更新均拒绝数量/单价 0 或负数；本地 data/app.db 发现 8 条历史空明细，价格无法无损推回，未自动改历史数据 |
| SALES-21 | 商机阶段词表两套不一致（ON_HOLD vs CLOSING） | P2 | 已验证 | sales/utils/stage_guard.py；sales/statistics_core.py；sales/statistics_reports.py；opportunity_batch.py；frontend OpportunityManagement/OpportunityDetail/SalesStatistics；migrations/20260703_sales_opportunity_stage_vocab_sqlite.sql | 0.5d | 静态已证；✅已动态复现并回归（2026-07-03） | 商机阶段写入口、统计桶、前端下拉/展示统一到 OpportunityStageEnum；旧 QUALIFIED/ON_HOLD 等存量值有清洗迁移 |
| SALES-22 | check_sales_data_permission 同文件重复定义 | P3 | 已验证 | core/sales_permissions.py；tests/unit/test_sales_scope_expansion.py | 0.25d | 静态已证；✅已动态复现并回归（2026-07-03） | 删除后置重复定义与重复导出，保留单一记录级权限入口；FINANCE_ONLY 对普通销售记录恢复拒绝，财务域仍走专用 finance scope |

### 二、售前域（PRE，24 项）

| ID | 功能/问题 | 等级 | 状态 | 证据位置 | 工作量 | 验证方式 | 备注/关联 |
|---|---|---|---|---|---|---|---|
| PRE-01 | 商机一键申请售前支持 request-presale-support | — | 已验证 | presale/tickets/crud.py:126-183 | — | 静态已证（正面确认） | 无缺陷 |
| PRE-02 | 售前工单主链路（接单→进度→交付物→完成→评分） | P2 | 重复-合并→PRE-14 | 见 PRE-14 | — | 静态已证 | 主链路本体可用，唯一缺陷即状态字典分裂（PRE-14），域内合并 |
| PRE-03 | 技术评估打分/否决/风险生成（evaluate） | — | 已验证 | — | — | 静态已证（正面确认） | 无缺陷 |
| PRE-04 | 立项关卡 PMO_REQUIRE_PRESALE_ASSESSMENT 可被"自动空评估"绕过 | P1 | 已验证 | presale_assessment_completion.py；technical_assessment_service.py；pmo_initiation/service.py；project_workspace_service.py；20260704_presale_assessment_auto_generated_sqlite.sql；tests/unit/test_presale_assessment_completion_pre04.py；test_pmo_initiation_service.py | 1.5d | 静态已证；✅已动态回归（2026-07-04） | 详#1；自动补建评估 now 标 `auto_generated=True`，真实 evaluate 标回 False；PMO 关卡要求 COMPLETED 且有评分/维度/风险/条件/AI分析等实质内容，空评估不再满足立项 |
| PRE-05 | 三档报价金额梯度倒挂（BASIC>STANDARD，DB 实证两例） | P1 | 已验证 | presale_ai_quotation_service.py；tests/unit/test_presale_ai_quotation_pre05_06.py | 1d | 静态已证；✅已动态回归（2026-07-04） | 三档生成后 now 强制标准档小计 >= 基础档 1.18 倍、高级档小计 >= 标准档 1.22 倍，覆盖 AI 低报导致的 basic/standard/premium 总价倒挂 |
| PRE-06 | 三档报价静态回退项是"ERP软件"报价，领域错配 | P2 | 已验证 | presale_ai_quotation_service.py；tests/unit/test_presale_ai_quotation_pre05_06.py | 0.5d | 静态已证；✅已动态回归（2026-07-04） | 静态兜底 now 改为非标自动化检测工作站/夹治具/视觉检测/数据追溯/自动上下料/现场调试，不再输出 ERP/进销存/移动端 APP 明细 |
| PRE-07 | update_quotation 税额/折扣不随明细重算 | P2 | 已验证 | presale_ai_quotation_service.py；tests/unit/test_presale_ai_quotation_pre07.py | 0.5d | 静态已证；✅已动态回归（2026-07-04） | 更新明细 now 按旧有效税率/折扣率重算税额、折扣和总额；同时修复 update 分支 Decimal 直接写 JSON 的提交失败 |
| PRE-08 | ai-enrich-requirement 整行覆盖清空已有需求；mock 回退破坏性写入 | P1 | 已验证 | opportunity_workflow.py；tests/unit/test_sales_opportunity_ai_mock_guard_pre08_09.py | 1d | 静态已证；✅已动态回归（2026-07-04） | 端点 now 拒绝 `model.endswith("-mock")` 并返回 502；需求表回填改为只覆盖 AI 非空字段，保留人工已填 product/ct/interface/site/acceptance/safety |
| PRE-09 | ai-quote-estimate mock 回退静默返回垃圾 200 | P2 | 已验证 | opportunity_workflow.py；tests/unit/test_sales_opportunity_ai_mock_guard_pre08_09.py | 0.5d | 静态已证；✅已动态回归（2026-07-04） | 修复并入 PRE-08：报价估算 now 在解析 JSON 前拦截 `-mock` 模型响应，避免 mock/演示数据以 200 返回 |
| PRE-10 | AI 需求分析结果无下游消费（数据孤岛，北极星断点） | P1 | 已验证 | presale/requirement_analysis_bridge.py；presale_ai_service.py；presale_ai_quotation_service.py；tests/unit/test_presale_requirement_bridge.py | 3d | 静态已证；✅契约测试回归（2026-07-03、2026-07-04） | 详#8；方案生成/三档报价支持 requirement_analysis_id 自动带出；新增 POST /presale/ai/analysis/{id}/confirm 确认后增量回填商机需求（不覆盖人工值，extra_json 溯源） |
| PRE-11 | 方案生成 mock 方案可入库（confidence 0.8）+ BOM 成本硬编码 10000 元 | P1 | 已验证 | presale_ai_service.py；tests/unit/test_presale_ai_mock_guard.py | 2d | 静态已证；✅已动态回归（2026-07-04） | `generate_solution` now 拒绝 mock 方案入库；BOM 单价 now 查物料库/标准模块库，查无价标“待询价”，不再写死 10000/推荐供应商A/30天 |
| PRE-12 | 方案导出 PDF 是纯文本桩、Word/Excel 为 pass 缺失 | P1 | 已验证-旧链路下线 | api.py:269-278；源文件 `presale_ai_export_service.py`/`presale_ai_routes.py` 已不存在 | 2-3d | 静态已证；✅路由对账（2026-07-04） | 老 AI 方案导出栈未再注册，未复活旧 PDF/Word/Excel 假成功路由；方案统一走 `/presale/proposals`，后续如要导出需在新方案栈重新设计 |
| PRE-13 | AI 使用报告 export-report 返回不存在的文件 URL | P2 | 已验证 | presale_ai_integration.py；tests/unit/test_presale_ai_export_report_pre13.py | 1d | 静态已证；✅已动态回归（2026-07-04） | `/presale/ai/export-report` now 生成真实 CSV/XLSX/PDF 文件，返回非零 file_size 和 `/downloads/{file_name}` 下载路由 |
| PRE-14 | 售前工单状态字典分裂（PROCESSING vs IN_PROGRESS / REVIEW 无路可走） | P2 | 已验证 | presale/core.py；tickets/crud.py；tickets/operations.py；tickets/utils.py；migrations/20260704_presale_ticket_status_normalization_sqlite.sql；tests/unit/test_presale_ticket_status_pre14.py | 1d | 静态已证；✅已动态回归（2026-07-04） | 工单状态 now 规范为 `IN_PROGRESS`，兼容 `PROCESSING→IN_PROGRESS`、`REVIEW→PENDING`；新建 SOLUTION_REVIEW 直接 PENDING；迁移脚本清洗存量 |
| PRE-15 | 售前移动端整域假实现（AI问答/语音/拜访/估价/快照全硬编码，前端零消费） | P1 | 已验证-路由下线 | api.py；tests/unit/test_presale_mobile_downline_pre15.py | 下架0.5d/做实4-5d | 静态已证；✅已动态回归（2026-07-04） | `/presale-mobile` now 不再挂载；保留源码但不暴露假 AI/语音/估价/快照接口，真实生产移动端仍走 `/mobile/*` |
| PRE-16 | 知识库 _has_live_ai 漏判 qwen，AI 提取/问答永走规则模板 | P1 | 已验证 | presale_ai_knowledge_service.py:681-687 | 0.1d | 静态已证；✅已修复并回归（2026-07-03） | 详#15；Quick-win 闸门包；_has_live_ai 已纳入 qwen_api_key |
| PRE-17 | 知识库/模板"语义搜索"实为字符哈希/Jaccard，非语义 RAG | P2 | 已验证(短期) | utils/text_similarity.py；presale_ai_knowledge_service.py；presale_ai_service.py；tests/unit/test_text_similarity_retrieval.py | 短期1d/中期3-5d | 静态已证；✅契约测试回归（2026-07-04） | 详#16；短期方案已落：中文 bigram 余弦替换空格 Jaccard；哈希向量改 bigram+稳定哈希（顺带修内建 hash() 进程随机化导致存量向量失配的隐藏 bug）；中期 qwen embedding 需标准百炼密钥（Coding Plan 端点 /embeddings 404 已实测），ROADMAP F4 |
| PRE-18 | 相似案例检索为 equipment_type 精确匹配 SQL，非语义 | P2 | 已验证 | opportunity_workflow.py similar_cases；tests/unit/test_text_similarity_retrieval.py | 并入 PRE-17 | 静态已证；✅契约测试回归（2026-07-04） | 详#16；改双向 LIKE 粗召回（词表分裂容错）+ bigram 相似度精排（WON 加权），空设备类型不再全库互配，返回带 similarity 分 |
| PRE-19 | 方案 AI 评审 ai-solution-review / 验收标准生成 | — | 已验证 | — | — | 静态已证（正面确认） | 无缺陷；ai-acceptance-criteria 真回填 |
| PRE-20 | AI 工作流编排只建状态壳无执行器（DB 中 20 行 status 全空） | P2 | 已验证-止损 | presale_ai_integration.py；tests/unit/test_presale_ai_workflow_pre20.py | 做实3d/下架0.5d | 静态已证；✅已动态回归（2026-07-04） | `auto_run=true` now 返回 501/ValueError，不再落 RUNNING 空壳；仅 `auto_run=false` 可创建全 PENDING 待执行计划 |
| PRE-21 | AI 后台任务重启后 PENDING/RUNNING 永久卡死（无恢复无超时） | P2 | 已验证 | ai_job_service.py；main.py startup；tests/unit/test_ai_job_recovery.py | 0.5d | 静态已证；✅已动态回归（2026-07-03） | 详#18；**主项**：APPR-22① 同问题并入本项（互为引用）；startup recover_stale_jobs + 轮询惰性超时（AI_JOB_MAX_RUNTIME_SECONDS 默认1800s）；`import app.main` 路由加载成功 |
| PRE-22 | 模块库 ai-modules（挖掘/列表/标准化建议，DB 7 模块） | — | 已验证 | — | — | 静态已证（正面确认） | 无缺陷 |
| PRE-23 | 立项提交关卡异常静默放行（except 后 missing=[]） | P2 | 已验证 | pmo_initiation/service.py:363-371 | 0.25d | 静态已证；✅已修复并回归（2026-07-03） | 详#19；Quick-win 闸门包；handover 构建异常 now raises ValueError，不再静默提交 |
| PRE-24 | 遗留脏数据字典（quotation_type 非法枚举 / assessment_status 两套值报表漏 93%） | P3 | 已验证 | presale_ai_quotation_service.py；assessment_status.py；opportunity_workflow.py；ai_copilot.py；20260704_presale_legacy_dictionary_cleanup_sqlite.sql；tests/unit/test_presale_legacy_dictionary_pre24.py | 0.5d | 静态已证；✅已动态回归（2026-07-04） | 详#20；报价历史读取 now raw SQL 归一化非法枚举，售前支持申请写入 PENDING，不再新增 REQUESTED；缺评统计兼容 PENDING/IN_PROGRESS/REQUESTED；迁移脚本清洗 AUTO/MANUAL/NORMAL 与 ASSESSMENT_* |

### 三、项目/PMO 域（PROJ，26 项）

| ID | 功能/问题 | 等级 | 状态 | 证据位置 | 工作量 | 验证方式 | 备注/关联 |
|---|---|---|---|---|---|---|---|
| PROJ-01 | 立项链路（草稿→提交→审批→建项目）+ 售前评估关卡 | — | 已验证 | pmo_initiation/service.py:358-371 | — | 静态已证（正面确认） | 无缺陷；但关卡可被空评估绕过见 PRE-04、异常静默放行见 PRE-23 |
| PROJ-02 | 立项审批未选 PM 则静默不建项目（APPROVED 但无项目无报错） | P2 | 已验证 | pmo_initiation/service.py；ReviewInitiationDialog.jsx；tests/unit/test_pmo_initiation_service.py；ReviewInitiationDialog.test.jsx | 0.5d | 静态已证；✅已动态回归（2026-07-04） | 详#15；审批通过 now 必须指定 `approved_pm_id`，否则 400/ValueError 且不改 APPROVED、不提交；前端审批弹窗也拦截空 PM |
| PROJ-03 | 合同→立项字段带入偷懒：占位文本冒充需求（商机/售前路径可用） | P2 | 已验证 | ContractManagement.jsx；ContractDetail.jsx；InitiationManagement/index.jsx；pmoInitiations.js；ContractManagement.test.jsx；ContractDetail.test.jsx；InitiationManagement.test.jsx | 2-3d | 静态已证；✅前端链路回归（2026-07-04） | 详#17；北极星主项；合同入口 now 查重后跳转 `handoff=contract` 立项表单，带出真实需求/金额/交期，不再创建占位需求立项；关联 APPR-14（交付日期幽灵字段） |
| PROJ-04 | 项目状态机无转移守卫，可任意非法跳转（S1→S9 直跳） | P1 | 已验证 | projects/status/status_crud.py；stage_advance_service.py；tests/unit/test_project_status_guard_proj04.py；test_stage_advance_service.py；test_service_edge_cases.py | 2d | 静态已证；✅单元回归（2026-07-04） | 详#3；direct PUT 阶段/状态 now 只能走下一步，`stage-advance` 也拒绝 S1→S9 跨级跳；存量脏状态仍留给 PROJ-05 清洗 |
| PROJ-05 | 项目 status 三套词汇表并存，过滤逻辑实际失效 | P2 | 已验证 | project_status_normalization.py；project_crud/service.py；project_scheduled_tasks.py；archive.py；ai_delivery.py；20260704_project_status_normalization_sqlite.sql；tests/unit/test_project_status_normalization_proj05.py | 2-3d | 静态已证；✅单元+迁移回归（2026-07-04） | 详#4；项目状态 now 统一读写为 stage+STxx，旧 `EXECUTING/COMPLETED/archived` 读侧兼容；归档不再写入 status；存量清洗脚本已在临时 SQLite 验证；PROJ-25 扫描改按 stage S2-S8 |
| PROJ-06 | 结项无强制门禁——未验收可直接结项（readiness 真校验未接线） | P0 | 已验证 | pmo/closure.py:80-155；closure_readiness_service.py | 1-2d | ✅已动态复现并回归（test_p0_08，2026-07-03） | 全局P0#8；Quick-win 闸门包；创建结项 now requires readiness.ready=True |
| PROJ-07 | 阶段门两条旁路：终验收直写 S9 绕回款门 + superuser 静默跳门 | P1 | 已验证 | acceptance_completion_service.py；acceptance/acceptance_service.py；stage_advance_service.py；projects/status/stages.py；stage_transition_checks.py；test_acceptance_completion_service.py；test_stage_advance_service.py；test_acceptance_service.py | 1-2d | 静态已证；✅单元回归（2026-07-04） | 详#14；终验收 now 必须走 S8→S9 阶段门，回款不达标不写 S9；旧 async 验收服务不再直推 S9；superuser 不再隐式免检，只有显式 `skip_gate_check=true` 才可跳门且写入响应/日志 |
| PROJ-08 | 任务进度→项目进度"加权汇总"实为简单平均，真加权函数死代码 | P2 | 已验证 | progress_service.py；test_progress_service_branches.py；test_progress_service.py；test_progress_service_extended.py | 1d | 静态已证；✅单元回归（2026-07-04） | 详#13；`aggregate_task_progress` now 复用真实 `ProgressAggregationService` 加权结果写回项目进度；阶段聚合同步按 `project_stage + estimated_hours` 加权，低工时任务不再与高工时任务等权 |
| PROJ-09 | 甘特依赖不影响排期（仅画线+CPM 长度，无级联重排） | P1 | 已验证 | gantt_dependency.py；tests/unit/test_gantt_dependency_proj09.py | 4-6d | 静态已证；✅单元回归（2026-07-04） | 详#6；新增依赖 now 按 FS/SS/FF/SF + lag_days 推迟后继计划日期并继续级联；关键路径计算 now 使用依赖类型语义，不再把 SS/FF/SF 全按串行 FS 长度计算 |
| PROJ-10 | 里程碑完成闸门被自身 except 吞掉，三条路径口径不一 | P1 | 已验证 | core/state_machine/milestone.py:91-118；endpoints/milestones.py:183-226 | 1-2d | 静态已证；✅已修复并回归（2026-07-03） | 详#5；Quick-win 闸门包；HTTPException 已重抛，全局 complete 端点已接 MilestoneStateMachine |
| PROJ-11 | 成本归集非实时（D2 确认）、退货不冲减、在制工单入账、日期归错月 | P1 | 已验证 | cost/cost_collection_service.py；purchase/receipts.py；tests/services/test_cost_collection_business_docs.py；tests/unit/test_cost_collection_n3.py | 4-5d | 静态已证；✅单元回归（2026-07-04） | 详#11；采购成本 now 按已收货金额/收货日期实时归集；收货作废 now 冲减订单已收数量并删除/更新采购实际成本；在制工单不入账，已完工工单按 Worker.hourly_rate；ECN 负向成本 now 作为冲减记录入账；归集流程 now 规范历史 `project_costs` 空 `cost_type/category/basis` 并重算项目 actual_cost |
| PROJ-12 | 工时填报→审批→撤回（统一引擎，模板已入库） | — | 已验证 | — | — | 静态已证（正面确认） | 无缺陷；附带 P3：工时提醒 REST 端点占位桩（详#22，timesheet_reminders.py:7-25），调度器仍 MemoryJobStore（F3） |
| PROJ-13 | 工时→人工成本/超支分析联动不过滤审批状态（时薪已走费率服务） | P1 | 已验证 | cost/cost_overrun_analysis_service.py；tests/unit/test_cost_overrun_analysis_service.py | 1d | 静态已证；✅单元回归（2026-07-04） | 详#12；人工成本、实际工时、归责分析 now 统一只读取 `Timesheet.status == APPROVED`；DRAFT/PENDING 不再计入成本和归责；第二轮已确认“时薪写死100”半项此前已修 |
| PROJ-14 | 预算超支只预警不拦截，预警链路"哑炮"（富版通知服务不在链路） | P1 | 已验证 | cost/cost_collection_service.py；budget_alert_service.py；purchase/orders_refactored.py；tests/services/test_cost_collection_business_docs.py；tests/unit/test_budget_alert_config_proj14.py | 3-4d | 静态已证；✅单元回归（2026-07-04） | 详#10；成本归集 now 调 `BudgetAlertService.check_and_alert()` 富版预警链路；预算阈值 now 从 `AlertRule.threshold_value/min/max` 配置黄/橙/红；采购订单创建前 now 做预算软拦截，预计触红默认 409，显式 `budget_override=true` 可继续并回传 `budget_guard` |
| PROJ-15 | 预算/成本预警调度口径含计划成本（把 BOM 计划当实际，误报超支） | P2 | 已验证 | project_scheduled_tasks.py；tests/unit/test_project_scheduled_tasks.py | 0.5d | 静态已证；✅单元回归（2026-07-04） | 详#21；定时成本超支扫描 now 使用 `actual_project_cost_filter()`，只统计 ACTUAL/旧 NULL 兼容实际成本，PLAN/BOM 计划成本不再触发误报 |
| PROJ-16 | EVM 挣值：引擎真、PV/EV/AC 全手填（data_source=MANUAL，仅 3 行数据） | P1 | 已验证 | evm_service.py；projects/costs/evm.py；tests/unit/test_evm_system_data_proj16.py；tests/unit/test_evm_calculator.py | 3-4d | 静态已证；✅单元回归（2026-07-04） | 详#7；EVM now 可从项目预算、计划起止日期、progress_pct、actual_cost 自动推导 SYSTEM 快照；`/evm` 与 `/evm/trend` 无手工快照时不再 404，`/evm/metrics` 可不传 pv/ev/ac/bac 自动计算；保留手工快照与手工公式计算 |
| PROJ-17 | 项目健康度主计算器（H1-H4）无成本维、无数据即绿 | P2 | 已验证 | health_calculator.py；health_trend_service.py；tests/unit/test_health_calculator.py；test_health_calculator_branches.py | 2d（与 PROJ-19 打包） | 静态已证；✅单元回归（2026-07-04） | 详#9；主计算器 now 将预算缺失但有实际成本、预算使用率 >100%、待处理 `COST_OVERRUN` 纳入 H2 风险；完全缺少计划/进度/成本基线时不再默认 H1 |
| PROJ-18 | 四维趋势健康度成本维恒满分（幽灵字段 + 枚举错位双 bug） | P1 | 已验证 | health_trend_service.py；tests/unit/test_health_trend_service.py | 0.5-1d | 静态已证；✅单元回归（2026-07-04） | 详#8；成本维 now 从 `Project.actual_cost / budget_amount` 推算预算使用率，并按真实 `COST_OVERRUN` 待处理告警扣分，不再依赖幽灵字段/旧枚举字符串 |
| PROJ-19 | 健康度快照维度字段写死 0（四分维写同一总值） | P2 | 已验证 | health_calculator.py；project_scheduled_tasks.py；project_health_tasks.py；tests/unit/test_project_scheduled_tasks.py；tests/unit/test_project_health_tasks.py | 与 PROJ-17 打包 | 静态已证；✅单元回归（2026-07-04） | 详#9；快照 now 调四维趋势得分落 `schedule/cost/resource/quality_health`，并写入真实 `budget_used_pct/cost_variance/schedule_variance` 等指标，不再全 0/全等于综合 |
| PROJ-20 | 变更请求审批通过不回写项目基线（真联动引擎只绑 ECN） | P0 | 已验证 | project_change_requests/service.py；tests/unit/test_project_change_baseline_proj20.py；tests/unit/test_project_change_notifications_proj21.py | 3-5d | ✅已动态复现；✅单元回归（2026-07-04） | 全局P0#8；批准 ChangeRequest now 在同一事务回写项目计划结束日、受影响里程碑、变更实际成本和 `Project.actual_cost`，拒绝不改基线；`impact_details.baseline_application` 记录执行痕迹并防二次入账 |
| PROJ-21 | 变更/立项审批通知均未实现（TODO/pass） | P2 | 已验证 | project_change_requests/service.py；tests/unit/test_project_change_notifications_proj21.py | 1-2d | 静态已证；✅已动态回归（2026-07-03） | 详#16；F3 扩围候补已收口；变更提交 now 通知项目 PM，审批结果 now 通知提交人，均走真实站内通知 |
| PROJ-22 | 验收全流程 + 报告生成（真 reportlab PDF） | — | 已验证 | acceptance/report_utils.py:75-208 | — | 静态已证（正面确认） | 无缺陷 |
| PROJ-23 | 验收通过后无售后/ITR 移交联动（售后需人工重建） | P2 | 已修待验 | acceptance_service.py _handover_to_after_sales；tests/unit/test_acceptance_aftersales_handover.py | 2d | 静态已证；✅契约测试回归（2026-07-04） | 详#18；SAT 验收通过自动移交：ACTIVE 质保建档（项目质保月数缺省12）+ 项目/机台质保期与客户归属回填（只补空）+ 幂等；机台字段依赖 AS-10 已修 |
| PROJ-24 | 项目复盘可用，但 AI 降级 mock 语义错配（预售文案进复盘） | P3 | 待修 | ai_client_service.py:406-422 | 1-2d | 静态已证 | 详#19；附带：change_impact_ai_service.py 653 行死代码无端点 |
| PROJ-25 | 交付风险 AI（ai_delivery，规则真算） | — | 已验证 | — | — | 静态已证（正面确认） | 无缺陷；但只认 EXECUTING，ST 码项目不进扫描（随 PROJ-05 清洗解决） |
| PROJ-26 | 团队组建未接入立项；经验维度写死 20 分 | P3 | 待修 | team_generation_service.py:234-235 | 1-2d | 静态已证 | 详#20 |

### 四、生产/供应链域（PROD，24 项）

| ID | 功能/问题 | 等级 | 状态 | 证据位置 | 工作量 | 验证方式 | 备注/关联 |
|---|---|---|---|---|---|---|---|
| PROD-01 | 现场调试 field_commissioning 假实现（签到/进度/问题/完工只回成功不写库） | P0 | 已验证 | field_commissioning.py；models/field_commissioning.py；tests/audit_p0/test_p0_09_field_checkin_fake.py；tests/api/test_field_commissioning_persistence_prod01.py | 6-8d | ✅已动态复现并回归（test_p0_09，2026-07-04）；✅端点级持久化回归覆盖签到/进度/问题/完工 | 全局P0#9；**主项**：AS-01 同问题并入本项；`field_tasks/field_checkins/field_issues` now 有模型和真实接口，签到/进度/问题/完工均落库 |
| PROD-02 | 智能缺料预警扫描引用不存在字段，扫描端点必 500 | P0 | 已验证 | services/shortage/smart_alert_engine.py；tests/audit_p0/test_p0_07_shortage_scan_500.py；tests/unit/test_smart_alert_engine.py | 1-2d | ✅已动态复现并回归（test_p0_07，2026-07-03） | 全局P0#7；F1 扩围；扫描字段错配 500 已消除，预警/齐套算法口径仍归 PROD-05 |
| PROD-03 | 收货→库存断链（inbound_service 全仓零调用，current_stock 只减无增） | P0 | 已验证 | purchase/receipts.py；inventory/inbound_service.py；inventory/stock_update_service.py；tests/api/test_purchase_receipts_workflow_contracts.py；tests/audit_p0/test_p0_06_receipt_no_stock.py | 2-3d | ✅已动态复现并回归（test_p0_06，2026-07-03） | 全局P0#6；F1 扩围；质检合格增量入库，写 MaterialStock/MaterialTransaction 并同步 Material.current_stock |
| PROD-04 | 在途量计算全线死数据（读侧状态字典无任何写入点，在途恒 0） | P1 | 已验证 | services/purchase/in_transit.py；kit_rate_service.py；tests/api/test_purchase_receipts_workflow_contracts.py | 1.5d | 静态已证；✅已动态回归（2026-07-03） | F1 扩围；采购在途读侧统一为 PO 生效状态 + 订单行剩余数量；PROD-05 齐套算法口径仍待修 |
| PROD-05 | 齐套率口径错误（在途计入已齐套/双算/无跨项目预留，四套实现互异） | P1 | 已验证 | kit_rate_service.py 及齐套域 7 处调用点 | 3-4d | 静态已证；✅45 用例回归（2026-07-03，见 PROJECT_NOTES）；✅复跑 83 用例（2026-07-04） | F1 扩围；当前齐套只按可用库存（MaterialStock.available_quantity 优先），在途单列为预计口径，received_qty 双算清除 |
| PROD-06 | BOM 版本管理假实现（bom_no unique 与版本模型矛盾，永远单版本） | P1 | 已验证 | models/material.py；bom/bom_versions.py；bom_release.py；tests/unit/test_bom_version_management.py；migrations/20260703_bom_versioning_sqlite.sql | 3d | 静态已证；✅单元回归（2026-07-04） | `bom_no` now 可多版本，`bom_no+version` 唯一；已发布 BOM 可创建 DRAFT 修订版并复制明细，发布修订版时旧版 `is_latest=False` |
| PROD-07 | ECN 审批通过不自动应用到 BOM（sync_to_bom 仅手工端点可调） | P1 | 已验证 | ecn_integration_service.py；approval_engine/adapters/ecn.py；ecn/execution.py；ecn/state_machine.py；tests/unit/test_ecn_bom_auto_sync_prod07.py | 2d | 静态已证；✅单元回归（2026-07-04） | ECN 审批通过和开始执行 now 自动调用 BOM 同步，`EcnAffectedMaterial(PENDING)` 会落到 `BomItem` 并写 `EcnBomChange` 留痕；采购 MODIFY 仍归 PROD-20 |
| PROD-08 | 工单不关联/不快照 BOM（无 bom_id 字段，WorkOrderBom 零业务读写） | P1 | 已验证 | models/production/work_order.py；services/production/work_order_service.py；models/shortage/requirements.py；tests/audit_p0/test_p0_12_bom_workorder_broken.py；tests/unit/test_work_order_bom_snapshot.py | 4d | ✅已动态复现并回归（test_p0_12，2026-07-04）；✅工单创建/更新 BOM 快照单元回归 | 全局P0#12（汇总定 P0，域内总表 P1）；**主项**：APPR-05 并入本项；工单 now 绑定 `bom_id/bom_no/bom_version`，创建/更新时写入 `mat_work_order_bom` 快照 |
| PROD-09 | ECN 状态机可跳步（SUBMITTED→APPROVED）且通用转换接口无权限 | P1 | 已验证 | ecn/state_machine.py；tests/api/test_ecn_state_machine_contracts.py | 1.5d | 静态已证；✅红后绿回归（2026-07-03）；✅复跑 75 用例（2026-07-04） | 通用状态机不再允许 SUBMITTED 直写 APPROVED/REJECTED，写入口补 `ecn:update` 权限；审批结果必须走 ECN 审批流程 |
| PROD-10 | 采购申请→订单转换绕审批、可重复生成、不回写 ordered_qty | P1 | 已验证 | purchase/purchase_service.py；tests/unit/test_purchase_service_generate_orders.py | 1.5d | 静态已证；✅25 用例回归（2026-07-03）；✅复跑 25 用例（2026-07-04） | 转单要求 APPROVED、按 source_request_id 防重复、回写 ordered_qty/auto_po_created；顺带修 2 处模型字段错配 |
| PROD-11 | 收货后 PO/POI 状态永不流转（PARTIAL_RECEIVED/RECEIVED 无写入点） | P1 | 已验证 | purchase/receipts.py；tests/api/test_purchase_receipts_workflow_contracts.py | 1d | 静态已证；✅已动态回归（2026-07-03） | F1 扩围；收货后刷新 PO/POI 到 PARTIAL_RECEIVED/RECEIVED，并累计订单已收金额 |
| PROD-12 | 生产领料不扣库存、无创建入口（前端调用必 404；OutboundService 真实现零调用） | P1 | 已验证 | production/material_requisitions.py；inventory/outbound_service.py；tests/api/test_production_compat_endpoints.py | 3d | 静态已证；✅已动态回归（2026-07-03） | F1 扩围；新增领料创建入口，审批后发料扣减库存并写 ISSUE 流水 |
| PROD-13 | 报工审批装饰性（未审批即回写产量，驳回不回滚） | P1 | 已验证 | production/work_reports.py；tests/api/test_production_write_smoke.py | 2d | 静态已证；✅已动态回归（2026-07-03） | Quick-win 闸门包；完工报工提交阶段只落 PENDING，审批通过后回写产量/工时/完成状态，驳回不回写 |
| PROD-14 | 物料调拨假实现（ProjectMaterial NameError 被吞、执行不动库存） | P1 | 已验证 | shortage/handling/transfers.py；inventory/transfer_service.py；material_transfer_service.py；tests/api/test_shortage_transfers.py | 2d | 静态已证；✅已动态回归（2026-07-03） | F1 扩围；调拨执行 now 源库扣减、目标库增加，并写 ISSUE/TRANSFER_IN 流水 |
| PROD-15 | 现场缺料→紧急采购断链（只建 DRAFT 申请即止，替代/调拨方案 return []） | P1 | 已验证 | shortage/handling/reports.py；urgent_purchase_from_shortage_service.py；smart_alert_engine.py | 3-4d | 静态已证；✅回归通过（2026-07-03，见 PROJECT_NOTES）；✅复跑 108 passed/11 skipped（2026-07-04） | 紧急采购生成 SUBMITTED 并按 source 去重；替代方案查 material_alternatives、调拨查 MaterialStock；APPR-04 的自动触发任务可随后解禁 |
| PROD-16 | 发货单无明细行、无齐套/质检门禁、不联动项目状态 | P1 | 已验证 | models/business_support/delivery.py；schemas/business_support/delivery.py；delivery_orders/crud.py；tests/unit/test_delivery_order_detail_gate_prod16.py；migrations/20260704_delivery_order_items_sqlite.sql | 5-7d | 静态已证；✅单元回归（2026-07-04） | 北极星项；发货单 now 有 `delivery_order_items` 明细，创建时从销售订单明细复制/校验剩余数量；发货前要求明细、项目齐套和 FQC/OQC PASS；发货/签收推进项目到 S8/ST24/ST25；关联 AS-10（发货→设备档案断链） |
| PROD-17 | AI 智能排程/优化纯模板填充（工期系数/节省天数/复用率全写死） | P1 | 已验证 | schedule_generation_service.py；schedule_optimization_service.py；schedule_generation.py；tests/unit/test_ai_schedule_stopgap_prod17.py | 标注0.5d/做实5-8d | 静态已证；✅止损回归（2026-07-04） | 止损包；样本不足（<3 个相似已完成项目）时返回 `status=unavailable`/422，不再生成默认 60 天排程、固定节省天数或复用率；有足够样本时标明 `data_source=historical_projects` 和样本数；完整 AI 优化算法仍待后续做实 |
| PROD-18 | 排产主算法真实但无工序依赖（单工序工单模型，dependencies=[]） | P2 | 待修 | production_schedule_service.py:185-269,1317 | 4-6d | 静态已证 | — |
| PROD-19 | 委外：超交无校验、无收货确认端点、订单不挂工单 | P2 | 待修 | outsourcing/deliveries.py:191-195；models/outsourcing.py:32-33,165-166 | 3-4d | 静态已证 | — |
| PROD-20 | ECN 影响传导到采购靠手工（受影响记录手建、MODIFY 分支空 pass） | P2 | 待修 | ecn/impacts.py:86,249；integration_service.py:176-178 | 3d | 静态已证 | 关联 PROD-07 |
| PROD-21 | 车间移动端无离线队列、扫码 iOS 不兼容 | P2 | 待修 | MobileScanStart.jsx:111-134,142 | 4-5d | 静态已证 | 报工闭环本体可用（正面） |
| PROD-22 | 收货明细金额不计算（amount 恒空，无对账基础） | P2 | 已验证 | purchase/receipts.py；tests/api/test_purchase_receipts_workflow_contracts.py | 0.5d | 静态已证；✅已动态回归（2026-07-03） | 修复并入 PROD-11；收货明细金额与订单已收金额同步更新 |
| PROD-23 | 状态机治理双轨（采购两套并行审批改 PO.status；报工内联判断不走状态机） | P2 | 待修 | orders_refactored.py:319-367 vs purchase/workflow.py；work_reports.py:132,227 | 2d | 静态已证 | 集群6 |
| PROD-24 | 委外成本归集口径偏差（审批即全额入账，不随质检合格量冲减） | P3 | 待修 | outsourcing_workflow_service.py:69-78 | 2d | 静态已证 | — |

### 五、售后/客服域（AS，25 项）

| ID | 功能/问题 | 等级 | 状态 | 证据位置 | 工作量 | 验证方式 | 备注/关联 |
|---|---|---|---|---|---|---|---|
| AS-01 | 现场调试签到/进度/完工回执全链路假实现 | P0 | 重复-合并→PROD-01 | field_commissioning.py:43,67,76-111 | — | 静态已证 | 与 PROD-01 同一 field_commissioning 问题，保留 PROD-01 为主项 |
| AS-02 | 邮件触达全链路不可用（假桩 success=True + 配置键错位双重故障） | P0 | 已验证 | notification/channels/email_handler.py；timesheet/reminder/notification_sender.py；tests/audit_p0/test_p0_11_notification_fake_success.py；tests/unit/test_notification_sender_coverage.py | 2d | ✅已动态复现并回归（test_p0_11 + sender，2026-07-03） | 全局P0#11；统一邮件通道必须真实 SMTP 成功才返回 success；工时提醒改读 EMAIL_* 配置；APPR-17 预警积压另修 |
| AS-03 | 通知 Redis 队列有生产者无消费者（配置 Redis 即通知黑洞） | P0 | 已验证 | app/core/config.py；notification/notification_queue.py；scripts/notification_worker.py；tests/audit_p0/test_p0_11_notification_fake_success.py；tests/unit/test_notification_queue_service_standalone.py | 1-2d | ✅已动态复现并回归（test_p0_11，2026-07-03） | 全局P0#11；Redis 存在时默认同步 dispatch，只有显式 `NOTIFICATION_QUEUE_ENABLED=true` 才入队；worker 导入路径已修；APPR-17 预警积压另修 |
| AS-04 | 工程师派工冲突检测空转（依赖表不存在静默返回 0 冲突，assign 零校验） | P0 | 已验证 | engineer_scheduling_service.py；engineer_scheduling.py；installation_dispatch/workflow.py；migrations/20260704_engineer_task_assignments_sqlite.sql；tests/audit_p0/test_p0_14_dispatch_conflict.py；tests/unit/test_dispatch_conflict_guard_as04.py | 4d | ✅已动态复现并回归（test_p0_14，2026-07-04）；✅派工入口冲突拦截单测 | 全局P0#14；集群3（算法真接线假）；`engineer_task_assignments` 已建表并接入冲突检测/派工前校验 |
| AS-05 | 服务工单状态机无转移矩阵：未派工可直接关单 | P1 | 已验证 | service/tickets/status.py；models/service/enums.py；tests/unit/test_service_ticket_state_machine_as05.py | 1.5d | 静态已证；✅单元回归（2026-07-04） | 状态矩阵 now 限定 `PENDING→IN_PROGRESS→RESOLVED→CLOSED`；未派工不可直跳解决/关闭，关闭必须先 RESOLVED；历史脏枚举仍需数据清洗专项处理 |
| AS-06 | SLA 计时真、超时预警/升级从不运行（零调度 + 策略 is_active 全 NULL） | P1 | 已验证 | sla_service.py；scheduled_tasks/alert_tasks.py；scheduler_config/alerting.py；tests/unit/test_sla_as06.py | 2.5d | 静态已证；✅已动态回归（2026-07-03） | F3 扩围；历史 `is_active NULL` 策略按启用兼容，新增 `check_sla_warnings` 调度同步未关闭工单 SLA monitor 并生成去重 AlertRecord |
| AS-07 | 项目级售后模块 create-only、前端只读、与服务工单双轨割裂 | P1 | 已验证 | after_sales.py；AfterSalesCenter.jsx；tests/unit/test_after_sales_as07.py；AfterSalesCenter.test.jsx；test_service_ticket_crud_contracts.py | 3d | 静态已证；✅红后绿单元+前端契约+相邻回归（2026-07-04） | 项目售后中心 now 支持工单走统一 `/service/tickets`，legacy after-sales 创建入口写入 `ServiceTicket`；反馈/保养补状态更新和前端动作；AS-18 已后续收口 |
| AS-08 | 备件管理假实现：无领用扣减、无库存联动、parts_cost 是 String | P1 | 已验证 | after_sales.py；models/after_sales.py；migrations/20260704_after_sales_tables_sqlite.sql；tests/unit/test_after_sales_spare_parts_as08.py | 4d | 静态已证；✅红后绿单元+相邻回归+迁移脚本验证（2026-07-04） | 备件创建 now 同步 `inventory` 售后备件仓；新增领用接口扣减 after-sales 数量与库存可用量；现场服务 `parts_cost/total_cost` 和备件单价改为 `Numeric(12,2)` 并按领用成本累计 |
| AS-09 | 六张售后表在运行库不存在，质保/备件/满意度等端点即调即 500 | P1 | 已验证 | after_sales.py；models/__init__.py；migrations/20260704_after_sales_tables_sqlite.sql；tests/unit/test_after_sales_tables_as09.py | 1-2d | 静态已证；✅红后绿单元+相邻回归+迁移脚本验证（2026-07-04） | 质保/备件/现场/SLA/满意度/知识库表 now 有端点 checkfirst 兜底 + `app.models` 注册；迁移脚本已验证、真实库待发布/执行；现场服务派工已在 AS-18 收口 |
| AS-10 | 无客户侧设备档案（Machine 无 SN/客户/保修字段），验收/发货不建档 | P1 | 已验证 | project/core.py；service/ticket.py；service/record.py；service/tickets/crud.py；service/records.py；tests/audit_p0/test_p0_13_device_archive_missing.py；tests/unit/test_device_archive_as10.py | 4d | ✅已动态复现并回归（test_p0_13，2026-07-04）；✅服务工单/服务记录机台绑定单元回归 | 全局P0#13（汇总定 P0）；**主项**：APPR-06 并入本项；`machines` now 有 `customer_id/serial_no/warranty`，服务工单/服务记录 now 可绑定 `machine_id` |
| AS-11 | 售后工单无设备外键；机台"服务历史"坏连接恒空（String vs Integer） | P1 | 已验证 | machine_custom/service.py；service_tickets/service_records schema；tests/unit/test_device_archive_as10.py | 3d | 静态已证；✅机台服务历史 machine_id 回归（2026-07-04） | 全局P0#13 同包；服务历史 now 优先按 `ServiceRecord.machine_id` 查询，并兼容旧 `machine_no` 文本 |
| AS-12 | 售后→ECN/质量闭环完全缺失；ITR 自我导入占位（925 行死代码） | P1 | 已验证 | service/tickets/issues.py；itr.py；itr_service.py；tests/unit/test_service_ticket_escalation_as12.py | 4d | 静态已证；✅单元回归（2026-07-04） | 服务工单 now 可升级质量 Issue/ECN，ECN 写 `source_type=SERVICE_TICKET`；ITR now 接真实 timeline/related/dashboard 路由并纳入 QUALITY 问题 |
| AS-13 | 客户360 四页签绑定不存在字段恒空；售后工单不入 360 | P1 | 已验证 | customer_360_service.py；customers/view360.py；schemas/project/customer.py；tests/unit/test_customer_360_as13.py | 3d | 静态已证；✅红后绿单元+API 回归（2026-07-04） | 客户 360 now 返回 `orders/payments/satisfactions/services` 前端页签字段；`services` 接入真实 `ServiceTicket`，满意度接 `CustomerSatisfaction`，订单接 `SalesOrder` |
| AS-14 | 维保计划周期调度 pass 桩 + 幽灵表，生成靠手动、验收不联动 | P1 | 已验证 | equipment_maintenance_service.py；equipment_maintenance_tasks.py；acceptance_completion_service.py；order_workflow.py；tests/unit/test_equipment_maintenance_reminder_as14.py | 3d | 静态已证；✅动态回归（2026-07-04） | 设备保养提醒任务移出 stub，扫描 `equipment.next_maintenance_date` 生成去重 `EQUIPMENT_MAINTENANCE` AlertRecord 并指派车间主管；调度解禁 8:30 且依赖真实表；FINAL 验收通过 now 调 `ProjectDataFlowService.transfer_to_after_sales()` 自动生成 1/3/6/12 月定期保养计划 |
| AS-15 | 短信渠道假发送（日志即 success），阿里云真实现是死代码 | P1 | 已验证 | notification/channels/sms_handler.py；tests/audit_p0/test_p0_11_notification_fake_success.py；tests/unit/test_notification_channels_sms.py | 1d | 静态已证；✅已动态回归（2026-07-03） | 全局P0#11；短信通道缺网关配置/SDK/网关成功响应时返回失败，不再 logger 即 success；APPR-17 预警积压另修 |
| AS-16 | Header 铃铛纯装饰（无 onClick、红点无条件渲染、badge 写死 5） | P1 | 已验证 | Header.jsx；sidebarConfig/default.js；Header.test.jsx | 0.5d | 静态已证；✅已动态回归（2026-07-03） | Quick-win 闸门包；Header 读取真实未读数，0 不显示角标，点击进入 `/notifications`，侧栏通知中心移除写死 badge |
| AS-17 | 工程师调度前端 4 接口后端不存在必 404；模块请求时现场 DDL 建表 | P1 | 已验证 | engineerScheduling.js；engineer_scheduling.py；engineer_scheduling_service.py；routeContracts.test.js；migrations/20260704_engineer_task_assignments_sqlite.sql；tests/unit/test_engineer_scheduling_as17.py | 2d | 静态已证；✅红后绿单元+前端契约+相邻回归（2026-07-04） | 前端 4 接口 now 注册并可用：`workload-board`、`availability`、`PUT/DELETE assignments/{id}`；`engineer_task_assignments` 有迁移脚本，建表保障集中到 `EngineerSchedulingService.ensure_task_assignment_table()`，不再端点散落现场 DDL |
| AS-18 | 售后现场服务记录孤立记事本（is_warranty 写死、无流转、不建派工单、表不存在） | P1 | 已验证 | after_sales.py；models/after_sales.py；migrations/20260704_after_sales_field_service_dispatch_sqlite.sql；tests/unit/test_after_sales_field_service_as18.py | 3d | 静态已证；✅红后绿单元+售后/派工相邻回归+迁移脚本验证（2026-07-04） | 现场服务 now 生成 `InstallationDispatchOrder`，保存 `dispatch_order_id`；`is_warranty` 按有效质保判断/可显式覆盖；现场服务状态流转同步派工单状态、进度、实际工时 |
| AS-19 | 客服工作台"关闭工单"按钮必 422（payload 字段名错）；质保页签恒空 | P1 | 已验证 | CustomerServiceDashboard.jsx；CustomerServiceDashboard/utils.js；schemas/service.py:56-63 | 0.5d | 静态已证；✅已修复并回归（2026-07-03） | Quick-win 闸门包；close payload now uses solution，后端兼容 resolution，质保页签用真实质保类工单兜底；AS-09 缺表 500 已于 2026-07-04 验证收口，真实库迁移脚本待发布/执行 |
| AS-20 | 保修在保/过保判断缺失，无过保收费（ProjectWarranty 自述未启用） | P2 | 已验证 | project/extensions.py:145-202；after_sales.py；models/after_sales.py；migrations/20260704_after_sales_warranty_billing_sqlite.sql；tests/unit/test_after_sales_warranty_as20.py | 2.5d | 静态已证；✅红后绿单元+售后相邻回归+迁移脚本验证（2026-07-04） | 售后质保 now 统一识别 `AfterSalesWarranty`、`ProjectWarranty` 和 `Project.warranty_*`；现场服务创建自动写入 `is_warranty/warranty_source`，过保服务支持 `service_fee/travel_cost/parts_cost/total_cost` 与 `charge_required/charge_status` |
| AS-21 | 关单不触发回访；调查"发送"不触达、前端 submit 接口 404；评分员工代填 | P2 | 已验证 | service/tickets/status.py；service/surveys.py；schemas/service.py；frontend/src/services/api/service.js:236；tests/unit/test_service_ticket_surveys_as21.py | 3d | 静态已证；✅红后绿单元+服务工单相邻回归+路由注册验证（2026-07-04） | 服务工单关单 now 自动创建并发送 `SERVICE` 满意度调查；调查发送 now 创建真实站内通知；新增 `/service/surveys/{id}/submit` 客户提交入口，写回 `COMPLETED/response_date/overall_score/feedback`，避免继续靠员工 update 代填 |
| AS-22 | 故障诊断 AI 真调 LLM 但零上下文（历史工单/知识库未注入）；降级语义错位 | P2 | 已验证 | ai_engineering.py；FaultDiagnosis.jsx；tests/unit/test_ai_engineering_fault_as22.py | 2.5d | 静态已证；✅红后绿单元+静态检查+前端 lint（2026-07-04） | 故障诊断 prompt now 注入相似历史服务工单与已发布服务知识库；返回 `context_sources/ai_generated/degraded`；AI 不可用时返回带 `degraded_reason=AI_DIAGNOSIS_UNAVAILABLE` 的规则降级建议，前端展示降级和上下文来源计数 |
| AS-23 | 售后事件通知产生端缺失：12 端点零通知；派工 CC 直写 notified_at 造假 | P2 | 已验证 | after_sales.py；service/tickets/assignment.py；service/tickets/crud.py；service/tickets/status.py；service_ticket_notifications.py；tests/unit/test_service_ticket_notifications_as23.py | 1d | 静态已证；✅已动态回归（2026-07-03） | F3 扩围；集群4（假成功）；服务工单创建/派工/状态变更/关闭已发真实站内通知，CC `notified_at` 改为发送成功后写；`after_sales.py` 反馈/保养/support ticket/质保/备件/现场服务/满意度/知识库/升级写端已通知项目 PM/创建人 |
| AS-24 | 双轨派工占用账不同步；派工完工工时不生成 Timesheet（外勤成本消失） | P2 | 已验证 | installation_dispatch/workflow.py；state_machine/installation_dispatch.py；tests/unit/test_installation_dispatch_as24.py | 4d | 静态已证；✅红后绿单元+派工/调度/售后相邻回归（2026-07-04） | 安装派工 start/complete/cancel now 同步 `EngineerTaskAssignment` 状态、实际日期和实际工时；complete now 生成关联 `Timesheet(assign_id/task_id)`，外勤工时进入工时台账；同时修复完工自动创建 `ServiceRecord` 的错误 import |
| AS-25 | 订阅默认接收人 TODO 返回空（双 resolver 口径不一）；webhook 仅企微 | P2 | 已验证 | alert_subscription_service.py；notification_utils.py；notification_service.py；channels/webhook_handler.py；tests/unit/test_notification_utils_as25.py | 2.5d | 静态已证；✅已动态回归（2026-07-03） | F3 扩围；默认接收人 now 取处理人/项目 PM 等业务负责人；旧 `app.services.notification_utils`/`notification_service` 路径恢复；Webhook 支持 `WEBHOOK_URL` 并兼容企微 URL |

### 六、审批引擎/状态机/跨域（APPR，22 项）

| ID | 功能/问题 | 等级 | 状态 | 证据位置 | 工作量 | 验证方式 | 备注/关联 |
|---|---|---|---|---|---|---|---|
| APPR-01 | 采购/外协/验收/立项 4 条审批链 template_code 与 DB 错位，提交必失败且 HTTP 200 掩盖 | P0 | 已验证 | purchase_workflow/service.py；outsourcing_workflow_service.py；acceptance_approval/service.py；projects/approvals/submit_new.py；api/v1/endpoints/approval_submit_guard.py；tests/audit_p0/test_p0_01_approval_template_mismatch.py | 1.5d | ✅已动态复现并回归（test_p0_01，2026-07-03） | 全局P0#1；审批链救活包；4 条业务链统一到 `TPL_*` 模板 code，全失败提交回滚并返回 400 |
| APPR-02 | 审批模板无任何种子/迁移，新环境全部审批不可用（F1/ECN1 根因） | P0 | 已验证 | scripts/init_db.py；app/utils/init_approval_data.py；app/utils/init_data.py；tests/audit_p0/test_p0_02_approval_template_no_seed.py | 1d | ✅已动态复现并回归（test_p0_02，2026-07-03） | 全局P0#2；审批链救活包；新库幂等种子 10 模板+13 flow+30 节点+3 路由规则 |
| APPR-03 | 会签/或签驳回语义破坏：REJECTED 实例可被翻转回 APPROVED | P0 | 已验证 | services/approval_engine/engine/approve.py；services/approval_engine/engine/core.py；tests/audit_p0/test_p0_05_cosign_reject_flip.py | 2d | ✅已动态复现并回归（test_p0_05，2026-07-03） | 全局P0#5；审批链救活包；AND_SIGN 汇总失败保持 REJECTED，OR_SIGN 拒绝后等待其他审批人，终态实例禁止 pending 任务复活 |
| APPR-04 | 14/56 定时任务 stub 假实现且监控记成功（含缺料预警 3 件套） | P0 | 已验证 | scheduled_tasks/shortage_tasks.py；stub_tasks.py；tests/unit/test_shortage_alert_task_backfill.py；tests/unit/test_equipment_maintenance_reminder_as14.py | 0.5d标记+3-5d回填 | ✅已动态复现（test_p0_10）；✅P0#10 全量回归通过（2026-07-04）；✅缺料 3/3 + 维保调度回填已回归 | 全局P0#10；F3 扩围；stub 标记/失败计数/禁用已完成；**缺料 3/3 件套已回填**：generate_shortage_alerts（接 SmartAlertEngine，每日 7:00）、auto_trigger_urgent_purchase（接 PROD-15 做实后的触发服务，SUBMITTED 进审批池人审为闸，每日 7:30）、generate_shortage_daily_report（写入/更新 ShortageDailyReport，每日 5:15）；维保计划已随 AS-14 收口 |
| APPR-05 | BOM→生产工单断链，WorkOrderBom 中间表零业务读写 | P0 | 重复-合并→PROD-08 | models/shortage/requirements.py:25；bom/bom_release.py:105-118 | — | 静态已证 | 与 PROD-08 同一结构性断链（全局P0#12），保留 PROD-08 为主项 |
| APPR-06 | 售后无设备档案表，机台级溯源断链（machine_no 手填文本） | P0 | 重复-合并→AS-10 | delivery_orders/crud.py:326-390；service/records.py:260 | — | 静态已证 | 与 AS-10 同一结构性缺失（全局P0#13），保留 AS-10 为主项 |
| APPR-07 | 撤回审批 TypeError：合同/验收/报价/ECN 4 域传错参数名（CONFIRMED），撤回必 500 | P1 | 已验证 | contract_approval/service.py:399；acceptance_approval/service.py:360；quote_approval_service.py:378；ecn/approval/service.py:394 | 0.5d | ✅已动态复现（test_p0_17）；✅已修复并回归（2026-07-03） | 全局P0#17（汇总定 P0，域内总表 P1）；**主项**：PEER-03 并入本项；4 域均改为 initiator_id 并传 comment=reason |
| APPR-08 | 加签（前/后加签）假实现：加签人永收不到可办任务或原审批人被跳过 | P1 | 已验证 | services/approval_engine/executor.py；services/approval_engine/engine/core.py；tests/unit/test_approval_add_sign_appr08.py | 2d | 静态已证；✅单元回归（2026-07-04） | 前加签 now 加签人先办、通过后恢复原审批人待办；后加签 now 原审批人通过后激活加签任务，后加签完成前实例不提前通过 |
| APPR-09 | 审批超时机制（REMIND/AUTO_PASS/AUTO_REJECT/ESCALATE）零调度死代码 | P1 | 已验证 | approval_engine/executor.py；approval_engine/engine/timeout.py；scheduled_tasks/approval_tasks.py；scheduler_config/approval.py；tests/unit/test_approval_timeout_task_appr09.py | 2d | 静态已证；✅动态回归（2026-07-04） | 集群3；新增通用审批超时/预超时调度，扫描 `approval_tasks.due_at`；REMIND 真实催办，AUTO_PASS/AUTO_REJECT 复用 `process_approval()` 并推进实例流转，ESCALATE 生成直属上级待办；`notify_timeout_warning` 已接入预警扫描 |
| APPR-10 | 发票开票门禁读旧轨空表（查不到即放行）——未审批可开票 | P1 | 已验证 | sales/invoices/operations.py；services/approval_engine/adapters/invoice.py；tests/api/test_sales_invoice_gate_contracts.py；tests/audit_p0/test_p0_16_invoice_gate.py | 1d | 静态已证；✅已动态回归（2026-07-03） | 全局P0#16（汇总定 P0）；资金急救包；开票前要求发票状态与统一审批实例均为 APPROVED |
| APPR-11 | update_invoice 任意改金额/状态：绕 F3 上限、绕审批与状态机 | P1 | 已验证 | sales/invoices/basic.py；models/sales/invoices.py；tests/api/test_sales_invoice_gate_contracts.py | 1d | 静态已证；✅已动态回归（2026-07-03） | 全局P0#16；资金急救包；**主项**：PEER-04 并入本项；update 禁止改 status，并重跑合同累计开票上限 |
| APPR-12 | 合同审批三轨并存，旧轨 /contracts/enhanced/* 可绕统一引擎自审自过 | P1 | 已验证 | sales/contracts/enhanced.py；services/contract_approval/service.py；tests/unit/test_contract_enhanced_approval_appr12.py | 1.5d | 静态已证；✅单元回归（2026-07-04） | 集群6；F2 前置；旧增强 `/submit` now 桥接统一审批 `SALES_CONTRACT_APPROVAL` 并生成 `ApprovalInstance/ApprovalTask`，旧增强 `/approve`/`/reject` 明确 400，必须走 `/sales/contracts/approval/action` |
| APPR-13 | 合同无中央状态机：15+ 直接赋值点、大小写两套状态值库中混存 | P1 | 已验证 | status_service.py；contracts.py；approval_engine/adapters/contract.py；data_sync_service.py；contracts/basic.py；contracts/sign_project.py；contract_status_normalization_sqlite.sql；tests/unit/test_contract_status_machine_appr13.py | 2-3d | 静态已证；✅红后绿单元+相邻回归+迁移脚本验证（2026-07-04） | 集群1/集群5；合同状态 now 统一写入 uppercase canonical，生产代码 `contract.status =` 仅剩状态服务写入口；历史 `ACTIVE/voided/approving/signed` 读侧折桶兼容；`data_sync` 只允许 `EXECUTING→COMPLETED`；通用 PUT 状态绕过由 PEER-01/02 已验证收口；已补存量清洗脚本，未直接改本地真实库 |
| APPR-14 | 合同→项目交付日期幽灵字段 delivery_deadline，自动立项项目全部无计划完工日期 | P1 | 已验证 | status_handlers/contract_handler.py；tests/unit/test_contract_project_delivery_date_appr14.py | 0.5-1d | ✅单元回归（2026-07-04） | 合同签订自动建项目/更新已关联项目 now 从 `QuoteVersion.delivery_date` 回填 `Project.planned_end_date`，兼容旧 `delivery_deadline` |
| APPR-15 | 发货款（默认 40%）回款计划无任何触发器，最大回款节点靠人工盯 | P1 | 已验证 | payment_plan_service.py trigger_delivery_payment_plan；delivery_orders/crud.py；tests/api/test_delivery_payment_plan_trigger_contracts.py | 1-2d | 静态已证；✅回归通过（2026-07-03）；✅复核通过（2026-07-04） | 资金急救包；发货确认同事务触发：收款计划日期对齐实际发货日 + 自动创建发货款开票申请（防重复） |
| APPR-16 | ECN 超期检查 job 模块路径错误，注册失败被静默吞掉 | P1 | 已验证 | scheduler_config/other.py；tests/unit/test_scheduler_utils.py | 0.5d | 静态已证；✅已动态回归（2026-07-03） | F3 扩围；check_ecn_overdue 模块路径改为 `app.services.ecn.ecn_scheduler`，resolver 契约锁定可导入 |
| APPR-17 | 预警通知永不流转状态：841 条 PENDING 积压 4 个月饿死 | P1 | 已验证 | alert_tasks.py；tests/audit_p0/test_p0_11_notification_fake_success.py | 1-1.5d | 静态已证；✅已动态回归（2026-07-03） | 全局P0#11；F3 扩围；worker 导入断裂已随 AS-03 修复；通知尝试后 AlertRecord `PENDING→OPEN`，扫描改最老优先；历史 841 条未直接改库，需随调度/运维逐批处置 |
| APPR-18 | 报价明细不复制为合同交付物，G4 门禁逼人工重录 | P1 | 已验证 | contracts/basic.py；tests/unit/test_contract_from_quote_deliverables_appr18.py；utils/gate_validation.py | 1d | 静态已证；✅单元回归（2026-07-04） | from-quote now 将报价明细复制为 `contract_deliverables`（名称/类型/付款必需/quote_item 溯源），普通合同创建带 `quote_version_id` 且未手填交付物时同样自动带出；SALES-12 附注已收口 |
| APPR-19 | 大额审批路由规则挂孤儿模板：≥50 万报价不再经总经理 | P2 | 已验证 | init_approval_data.py；approval_engine/adapters/quote.py；approval_engine/engine/core.py；tests/unit/test_approval_quote_routing_appr19.py | 1d | 静态已证；✅红后绿单元+相邻回归（2026-07-04） | 大额报价阈值修正为 ≥50 万；旧 QuoteApprovalAdapter now 走 `SALES_QUOTE_APPROVAL` + 报价 ID，并补 `total_price/gross_margin` 路由字段；节点推进 now 补回 adapter entity_data，条件分支可读 `entity.*` |
| APPR-20 | legacy 兼容端点创建的审批实例无节点无任务，永久 PENDING | P2 | 已验证 | approvals/legacy_compat.py；tests/unit/test_approval_legacy_compat_appr20.py | 0.5d | 静态已证；✅单元+相邻回归（2026-07-04） | legacy 端点 now 要求审批人、校验有效用户、补兼容模板/节点后走统一 `ApprovalEngineService.submit()`，避免无节点无任务空实例；历史 entity_type 空实例仍走数据清洗 |
| APPR-21 | 角色型 SINGLE 节点审批人取"全库第一个"，与业务上下文无关 | P2 | 已验证 | approval_engine/router.py；tests/unit/test_approval_role_context_appr21.py | 1.5d | 静态已证；✅单元+router 相邻回归（2026-07-04） | ROLE 审批 now 有 `project_id` 时优先按 `project_members.role_code` 解析项目成员并优先负责人，找不到项目成员才回退全局角色 |
| APPR-22 | 后台机制综合：①AI job 无重启恢复 ②备份 4 个月未自动执行 ③禁用任务重启复活 ④第二调度器不进监控 ⑤调度器 except ImportError 全静默 | P2 | 已验证 | scheduler.py；main.py startup；backup_service.py；scheduled_tasks/backup_tasks.py；scheduler_config/other.py；scheduler_progress.py；scheduler/status.py；tests/unit/test_ai_job_recovery.py；tests/unit/test_scheduler_utils.py；tests/unit/test_backup_scheduler_appr22.py；tests/unit/test_scheduler_progress_metrics_appr22.py | 0.5d起（分项） | 静态已证；✅子项①/②/③/④/⑤已动态回归（2026-07-03） | F3 扩围；**①与 PRE-21 重复并已验证**；②已修：新增 enabled `daily_database_backup`，SQLite 环境直接生成压缩 SQL dump+md5；③已修：DB `is_enabled=false` 不再重启复活；④已修：`scheduler_progress` 注册 job 包统一 metrics，`/scheduler/status` 与 `/scheduler/jobs` 汇总主/进度两个 scheduler；⑤已修：任务解析/注册失败写入 scheduler failure metrics，`main.py` scheduler 整体导入失败记录错误日志 |

### 七、并行会话补充：合同+发票状态流（PEER，5 项）

| ID | 功能/问题 | 等级 | 状态 | 证据位置 | 工作量 | 验证方式 | 备注/关联 |
|---|---|---|---|---|---|---|---|
| PEER-01 | 已取消（CANCELLED）合同可经通用 PUT 改回 SIGNED，绕过签署校验 | P1 | 已验证 | contracts/basic.py；tests/unit/test_contract_status_update_guard_peer01_02.py | 0.5-1d（status 剔出 field_map） | ✅单元回归（2026-07-04） | 通用合同更新 now 拒绝 `status` 字段，状态变更必须走签署/作废/审批等专用流程；关联 APPR-13 |
| PEER-02 | 审批中合同可被通用 update 改状态，与 ApprovalInstance 脱钩 | P1 | 已验证 | contracts/basic.py；tests/unit/test_contract_status_update_guard_peer01_02.py | 并入 PEER-01 修复 | ✅单元回归（2026-07-04） | 同 PEER-01：`pending_approval` 不能经通用 PUT 改成 SIGNED；审批状态仍归 APPR-13 全量状态机收口 |
| PEER-03 | 合同审批撤回必 500 / 状态永卡 PENDING_APPROVAL（user_id 参数名错） | P1 | 重复-合并→APPR-07 | contract_approval/service.py:399；engine/actions.py:73-77 | — | 静态已证（主会话 CONFIRMED） | 与 APPR-07 同一缺陷，APPR-07 覆盖 4 域为主项 |
| PEER-04 | 作废发票可经 update_invoice 改回 ISSUED/PAID，金额随意改 | P1 | 重复-合并→APPR-11 | invoices/basic.py:302,334-338 | — | 静态已证 | 与 APPR-11 同一端点同一根因，保留 APPR-11 为主项 |
| PEER-05 | 作废发票可被 /issue 重新开票（只查审批记录不校验当前 status） | P1 | 已验证 | sales/invoices/operations.py；tests/api/test_sales_invoice_gate_contracts.py | 0.5d | 静态已证；✅已动态回归（2026-07-03） | 候选 P0；资金急救包；作废/取消等非 APPROVED 当前状态不能重新开票 |

---

## 主表（第二轮：平台/支撑/边缘域）

> 第二轮覆盖 HR / 权限(PERM) / 平台运维(ADMIN) / 多租户(TEN) / 报表(RPT) / 边缘业务(MISC) 六域，来源为 audit2/ 下 6 份原始报告（hr.md/perm.md/admin.md/tenant_report.md/misc.md）。列结构、状态字典、验证方式口径与第一轮主表一致；等级列将 PERM 报告的"高/中/低"归一为 P1/P2/P3。二轮 P0 项验证方式仅"静态已证"（本轮未做动态复现，动态复现见第一轮 17 项）。

### 七、人力资源/组织域（HR，25 项）

| ID | 功能/问题 | 等级 | 状态 | 证据位置 | 工作量 | 验证方式 | 备注/关联 |
|---|---|---|---|---|---|---|---|
| HR-01 | 员工 Excel 导入端点必崩（运行时 import 不存在的 validate_excel_file） | P1 | 已验证 | employee_import_service.py；organization/employee_import.py；tests/unit/test_employee_import_service.py；tests/api/test_organization.py | 0.1d(Quick-win) | 静态已证；✅已动态回归（2026-07-03） | 新增 `validate_excel_file()`，非 Excel 上传返回 400，不再运行时 ImportError；空姓名清洗恢复为 `None`，导入时跳过空姓名行 |
| HR-02 | 离职处理仅置状态位，无交接不停账号（不联动 User.is_active） | P1 | 已验证 | hr_management/transactions.py；tests/unit/test_hr_resignation_user_deactivation_hr02.py | 3-4d | 静态已证；✅红后绿单元+贴近回归（2026-07-04） | resignation 审批 now 将员工置离职并停用所有绑定 `User.employee_id` 的 active 账号，响应返回 `deactivated_user_count`；完整交接 workflow 未扩展 |
| HR-03 | 数据权限绑部门名字符串，组织变动不随动 | P1 | 待修 | data_scope/generic_filter.py:121-135 | 2-3d+清洗0.5d | 静态已证 | 关联 PERM-15/17；调岗员工永远看旧部门数据 |
| HR-04 | 部门/员工删除前端调不存在端点（405/404） | P2 | 待修 | services/api/hr.js:19；organization 目录无 delete | 1d | 静态已证 | — |
| HR-05 | 员工-部门无外键、双主数据字符串关联（同义词并存） | P2 | 待修 | organization.py:76 department=String(50) | 2-3d | 静态已证 | 数据清洗专项 |
| HR-06 | 考勤统计是取模公式伪造（迟到人数由序号取模决定） | P1 | 已验证 | admin_attendance.py；tests/unit/test_admin_attendance_hr06_07.py | 止损0.5d/做实8-10d | 静态已证；✅止损回归+路由契约（2026-07-04） | `/admin/attendance` now 200 空态 + `attendance_data_available=false/source=attendance-not-configured/employee_total`，不再根据部门人数取模编造迟到/请假/缺勤/出勤率；完整考勤域仍待做实 |
| HR-07 | 打卡不落库、"我的考勤"硬编码 | P1 | 已验证 | admin_attendance.py；tests/unit/test_admin_attendance_hr06_07.py | 并入 HR-06 | 静态已证；✅止损回归（2026-07-04） | “我的考勤”now 返回显式空态；admin clock-in/clock-out/单条记录未接真实考勤域时返回 501，不再假成功或硬编码 08:27/18:04 |
| HR-08 | 请假缺失、加班僵尸模型、补卡缺失 | P1 | 待修 | timesheet.py:265-268；AttendanceManagement.jsx:38,310 | 5-8d/摘Tab0.5d | 静态已证 | 请假缺失致排产无输入 |
| HR-09 | 节假日双轨、DB 模型零消费（真消费的是硬编码字典） | P3 | 待修 | holiday.py:20；holiday_utils.py:13 | 1d | 静态已证 | DB 33 行真数据零消费 |
| HR-10 | 工程师五维绩效：算得出存不下读全空（PerformanceResult 零写入） | P0 | 已验证 | result_evaluation.py:24；performance_calculator.py:50；engineer_performance_service.py；engineer.py；tests/unit/test_engineer_performance_result_persistence_hr10.py | 3-4d | ✅已动态复现并回归（2026-07-04） | `calculate_and_save_result` now 计算五维/总分/等级并 upsert `performance_result`，刷新部门/公司排名；新增单人/批量计算落库接口，奖金 HR-16 上游已疏通 |
| HR-11 | 绩效评分维度写死常量（五维至少两维对全岗恒定） | P1 | 待修 | performance_calculator.py:108,111,187-188 | 3-5d(与HR-10打包) | 静态已证 | collector 与 calculator 互不调用 |
| HR-12 | 绩效采集器与算分器双轨不联通（空数据回落 75） | P2 | 待修 | aggregator.py:33；data_sync.py:171-184 | 并入 HR-11 | 静态已证 | — |
| HR-13 | 绩效申诉缺失（模型完整但零写入无端点） | P2 | 待修 | appeal_adjustment.py:13 | 2d | 静态已证 | 挂审批引擎 |
| HR-14 | 三套绩效体系并行隔绝、服务大面积复制粘贴 | P2 | 待修 | evaluation.py:76,127；calculation.py:20 | 3d | 静态已证 | 谁是正式绩效说不清 |
| HR-15 | 绩效合同绕 ORM 用裸 sqlite3（连接串写死） | P2 | 待修 | performance/contract.py:11,28,35 | 2-3d | 静态已证 | **主项**：MISC-12 同一 performance_contract 裸 sqlite3，MISC-12 标重复-合并→HR-15 |
| HR-16 | 绩效→奖金串联空转（北极星断链，从未算出一分钱奖金） | P1 | 已验证 | bonus/calculation.py:73；services/bonus/base.py；services/bonus/performance.py；tests/unit/test_performance_bonus_chain_hr16.py | 0d(依赖HR-10)+0.5d | ✅单元回归（2026-07-04） | HR-10 上游已疏通；绩效奖金 now 兼容 `PERFORMANCE/PERFORMANCE_BASED/PERFORMANCE_BONUS` 规则、S/A/B/C/D 系数、幂等写 `bonus_calculations`；审批/发放仍归 HR-17 |
| HR-17 | 奖金审批无权限无引擎，可自审可绕过（Excel 导入直 APPROVED） | P1 | 已验证 | sales_calc.py；bonus_distribution_service.py；tests/unit/test_bonus_approval_gate.py | 2-3d | 静态已证；✅契约测试回归（2026-07-04）；✅复核通过（2026-07-04） | 审批端点挂 bonus:manage + 防自审（受益人 403）+ 状态前置（仅 CALCULATED 可流转）；Excel 导入保留 APPROVED（发放前有财务/HR/总经理三方线下确认闸）但补审批留痕（操作人/时间/意见）；接统一审批引擎待后续（当前单级审批+权限门已闭合最大风险） |
| HR-18 | 团队奖金分配无"合计=100%/总额"校验 | P2 | 已验证 | bonus_allocation_parser.py；test_bonus_allocation_totals_hr18.py | 0.5d | 静态已证；✅Excel 合计校验回归（2026-07-04） | 同一团队分配/计算记录的发放金额合计必须等于团队总奖金/计算金额；不符时整组行退回，不再把 1 万分出 3 万 |
| HR-19 | 奖金系数硬编码非规则驱动（等级/角色/售前系数全写死） | P2 | 待修 | services/bonus/base.py:96-125；presale.py:60-73 | 1-2d | 静态已证 | 规则表 DB 仅 3 行假种子 |
| HR-20 | 时薪费率体系：本体真实，旁路 14 处写死 | P1 | 待修 | hourly_rate_service.py:30-157；labor_cost_detail.py:15；sales/cost/cost_calculator.py:28 等 | 2-3d | 静态已证 | 更正 PROJ-13：时薪写死已部分修复（cost_overrun_analysis_service.py:338-350 已走费率服务），仅剩不过滤审批状态 |
| HR-21 | 费率兜底口径混乱（全级 miss 静默返 100）、变更无留痕 | P2 | 已验证 | hourly_rate_service.py；hourly_rate/query.py；hourly_rate/crud.py；tests/unit/test_hourly_rate_hr21.py | 兜底0.5d/版本化1-2d | 静态已证；✅红后绿单元+相邻回归（2026-07-04） | 全级 miss now 记录 warning，查询 API 返回 `source/config_id/is_fallback/fallback_reason`；PUT now 到期旧版本并创建新版本，历史日期按旧费率；DELETE now 软停用保留历史查得旧费率；旧 Decimal 服务接口兼容 |
| HR-22 | 文化墙：配置端点坏 shim、无审核、前端 405 | P2 | 已验证 | culture_wall_config.py；contents.py；culture_wall.py schema；admin.js；tests/unit/test_culture_wall_hr22.py | 2d | 静态已证；✅已动态回归（2026-07-04） | **主项**：配置 CRUD 已由 MISC-23 修实；内容创建/编辑 now 不能自带 `is_published` 上墙，必须走 `/culture-wall/contents/{id}/review`；列表 `is_read` 改查真实阅读记录；前端补 `contents.review` |
| HR-23 | 冲突调解：真算法架在无写入者的空表上（resource_conflicts 零写入） | P2 | 待修 | conflict_mediation_service.py:60-461；analytics/resource_conflicts.py:89-143 | 检测落库1d/收敛2-3d | 静态已证 | 与 MISC-02、AS-24 同 resource_conflicts 空表/双轨病灶互引 |
| HR-24 | 协作评价自动补齐默认分污染（缺评一键填 3 分/75 分无标记） | P3 | 已验证 | collaboration_rating/ratings.py；statistics.py；engineer_performance/common.py；20260704_collaboration_rating_auto_completion_sqlite.sql | 0.5d | 静态已证；✅自动补齐打标+降权回归（2026-07-04） | 自动补齐 now 写 `is_auto_completed/auto_completed_at/reason`，权重降为 0.50；协作平均分按 `rating_weight` 加权，旧数据无权重按 1.00 |
| HR-25 | HR 域数据被通用填充脚本污染（假数据掩盖 HR-10 零写入断链） | P3 | 待修 | DB：hr_project_performance 70 行评分全 NULL；monthly_work_summary 含 task4_demo_seed | 0.5d | 静态已证 | 数据清洗专项 |

**HR 域小结**：骨架真、血肉假、串联断——用户/部门/时薪/奖金链路/协作评价 CRUD 骨架可用；考勤域是演示壳（HR-06/07/08）、工程师绩效"算得出存不下读全空"（HR-10）；绩效→奖金空转、组织变动→数据权限不随动、员工导入入口必崩。DB 侧 HR 域无任何真实业务数据流过。核心约 25-35 人天。

### 八、权限/认证域（PERM，23 项）

| ID | 功能/问题 | 等级 | 状态 | 证据位置 | 工作量 | 验证方式 | 备注/关联 |
|---|---|---|---|---|---|---|---|
| PERM-01 | JWT 签发/过期/签名/类型校验 | — | 已验证 | auth.py（真校验） | — | 静态已证（正面确认） | 无缺陷 |
| PERM-02 | Refresh Token 刷新+旋转（校验会话+黑名单旧 token） | — | 已验证 | auth.py | — | 静态已证（正面确认） | 无缺陷 |
| PERM-03 | Token 撤销黑名单无 Redis 降级（多 worker/重启即失效） | P1 | 已验证 | auth.py；20260704_jwt_token_blacklist_sqlite.sql；test_core_auth.py | 1-2d | 静态已证；✅Redis 缺失持久 fallback 回归（2026-07-04） | Redis 可用仍优先写 Redis；Redis 失败/未配置时写 `jwt_token_blacklist` 数据库兜底 + 本进程内存兼容，重启/多 worker 可按 JTI 识别撤销；历史过期记录惰性清理 |
| PERM-04 | 账号锁定 core 内存版是死代码（全仓无 import） | P2 | 待修 | account lockout core 版 | 0.5d | 静态已证 | 真正登录走 Service 版 |
| PERM-05 | 账号锁定 Service 版 DB 降级（阈值真生效） | P2 | 已验证 | AccountLockoutService | — | 静态已证（正面确认） | 无 Redis 走 DB 窗口统计 |
| PERM-06 | 账号解锁 API 缺失（account_unlock.py 占位桩） | P1 | 已验证 | account_unlock.py；account_lockout_service.py；tests/unit/test_account_unlock_api_perm06.py | 1-2d | 静态已证；✅单元/路由回归（2026-07-04） | 占位桩已替换为真实锁定列表/状态/历史/解锁 API；`unlock_account` now 同时清 Redis 与 DB 降级失败计数，无 Redis 时不再只能等窗口 |
| PERM-07 | 审计日志写入：用户/角色/权限有留痕，业务操作大面积无 | P2 | 待修 | sales_operation_logs 表不存在 | 2-3d | 静态已证 | — |
| PERM-08 | 审计日志查询 API 缺失（audits.py 占位桩） | P2 | 已验证 | audits.py；permission_audits；test_audits_api_perm08.py | 1d | 静态已证；✅列表/详情/路由挂载回归（2026-07-04） | 占位 shim 已替换为真实 `permission_audits` 查询；支持分页、operator/target/action/date 筛选，详情 404；主 app 已确认 `/api/v1/audits/` 与 `/{audit_id}` 挂载 |
| PERM-09 | RBAC 角色继承递归 CTE（SQL 支持但 DB 0 角色有 parent） | P3 | 已验证 | 递归 CTE | — | 静态已证（正面确认） | 数据未用，机制真 |
| PERM-10 | require_permission 装饰器机制（双模式实现正确） | — | 已验证 | require_permission | — | 静态已证（正面确认） | 无缺陷 |
| PERM-11 | require_permission 覆盖率 34.6%，142 个 NONE 端点裸奔 | P1 | 修复中 | 2026-07-04 AST 重扫 2980 路由：PERMISSION 1030/AUTH_ONLY 1808/NONE 142 | 3-5d | 静态已证；组织员工/HR 档案小切口已回归（2026-07-03）；覆盖率 JSON 已重生成（2026-07-04） | 已补 organization/employees 与 organization/hr_profiles 的 hr:* 权限；其余 NONE 端点仍待系统性收口 |
| PERM-12 | is_active=0 权限码静默过滤（禁用即从所有用户消失无告警） | P2 | 已验证 | permission_engine.py；test_permission_engine.py | 0.5d | 静态已证；✅禁用权限码告警回归（2026-07-04） | 禁用权限码仍不授予，但角色仍引用 inactive 权限时 now 记录 warning，包含 user/tenant/permission codes，避免静默消失 |
| PERM-13 | 权限缓存进程隔离+反查断链（改权限不重启不全生效） | P1 | 已验证 | permission_engine.py；permission_cache_service.py；role_management/service.py；roles.py；users/utils.py；20260704_permission_cache_revisions_sqlite.sql；test_permission_cache_perm13.py | 2d | 静态已证；✅反查用户+跨 worker 修订号回归（2026-07-04） | 角色权限变更 now 直接查 `user_roles` 并失效受影响用户；权限缓存 payload 带 DB 修订号，权限/角色关系变更 bump `permission_cache_revisions`，Redis 缺失时其他 worker 也会丢弃旧内存缓存 |
| PERM-14 | :read/:view 别名在鉴权路径未生效（精确串匹配） | P2 | 已验证 | auth.py；permission_engine.py；permission_codes.py；test_permission_alias_perm14.py | 1d | 静态已证；✅read/view 别名鉴权回归（2026-07-04） | `auth.check_permission` 与 permission engine now 使用 canonicalized 权限比较；DB/缓存/对象图里旧 `*:view` 可满足 `*:read`，反向同理 |
| PERM-15 | 数据权限 ALL/DEPT/OWN 过滤大量静默降级；CUSTOMER 恒 True | P1 | 待修 | generic_filter.py:218-221 | 3-5d | 静态已证 | 关联 HR-03；三系统性根因② |
| PERM-16 | RoleDataScope 配置层坏死（无 API、DB 垃圾种子 is_active 全 NULL） | P1 | 待修 | RoleDataScope 模型无 API；get_user_data_scopes 死代码 | 3-5d | 静态已证 | 实际生效的是 roles.data_scope 单字段 |
| PERM-17 | 数据权限挂载率：制造/供应链/财务全域 0 行级过滤 | P1 | 待修 | production(0/32)/procurement/bom/ecn/inventory/budget/cost/finance_reports/timesheet | 与 15/16 打包 | 静态已证 | acceptance(1/21)/presale(1/20) 近零 |
| PERM-18 | 超级管理员判定（is_superuser+tenant_id IS NULL 统一） | P2 | 已验证 | — | — | 静态已证（正面确认） | 库中有异常超管数据待清洗 |
| PERM-19 | 角色删除后残留会话（删角色不失效在线会话，靠 TTL 过期） | P2 | 已验证 | roles.py；SessionService；test_role_delete_perm19.py | 1d | 静态已证；✅角色删除撤销会话回归（2026-07-04） | 删除角色 now 收集受影响用户，删除 `user_roles` 后 bump 权限缓存修订号并撤销这些用户全部活跃会话；返回 affected/revoked 计数；关联 PERM-13 |
| PERM-20 | 密码修改/重置流程（改密撤销当前 token；重置不撤销目标会话） | P3 | 已验证 | user_sync_service.py；test_password_reset_sessions_perm20.py | 0.5d | 静态已证；✅重置密码撤销目标会话回归（2026-07-04） | 改密仍撤销当前 token；管理员重置目标用户密码 now 通过 `SessionService.revoke_all_sessions()` 撤销目标用户全部活跃会话 |
| PERM-21 | 全局认证中间件默认拒绝（白名单外强制 Bearer；可 env 一键关闭） | P2 | 已验证 | 中间件 | — | 静态已证（正面确认） | 可被 env 一键关闭为隐患 |
| PERM-22 | 前端路由/菜单/按钮权限：system/hr/finance 路由零守卫 | P2 | 待修 | 前端路由；401 回落 mock | 1-2d | 静态已证 | mock 掩盖越权 |
| PERM-23 | PERMISSION_COVERAGE_AUDIT.json 过时（数字与本轮接近） | P3 | 已验证 | PERMISSION_COVERAGE_AUDIT.json（2026-07-04 15:36 重生成） | 0.1d | ✅`scripts/audit_permission_coverage.py --json-only` | 当前基线：2980 端点，PERMISSION 1030（34.6%）/AUTH_ONLY 1808/NONE 142；用于继续推进 PERM-11 |

**PERM 域小结**：三个系统性根因——①Redis 未配曾导致撤销/会话/权限缓存等安全机制降级（PERM-03、PERM-13 已补数据库兜底/修订号）；②鉴权与数据权限"写了没挂"（覆盖率 34.6%、配置层坏死、整域裸奔 PERM-11/15/16/17，PERM-14 read/view 别名已接入鉴权）；③占位桩冒充功能已开始收口（账号解锁 PERM-06、审计查询 PERM-08 已验证）。最关键待修：给 142 个 NONE 端点补权限；继续收口数据权限过滤。

### 九、平台管理/运维域（ADMIN，23 项）

| ID | 功能/问题 | 等级 | 状态 | 证据位置 | 工作量 | 验证方式 | 备注/关联 |
|---|---|---|---|---|---|---|---|
| ADMIN-01 | 备份 API 路由自 import 自己必 ImportError，落占位路由 | P0 | 已验证 | endpoints/backup.py；tests/unit/test_backup_admin01_03.py | 备份三层合计 4-5d | 静态已证；✅已动态回归（2026-07-04） | `backup.py` 改为真实 router，提供列表、创建、数据库备份、验证、恢复、清理、统计端点 |
| ADMIN-02 | 备份恢复 restore 产品内不存在（BackupService 无 restore 方法） | P0 | 已验证 | backup_service.py；tests/unit/test_backup_admin01_03.py | 并入 ADMIN-01 | 静态已证；✅已动态回归（2026-07-04） | `BackupService.restore_backup()` 支持 SQLite gzip SQL dump 恢复，需 `confirm=True`，恢复前自动生成 `before_restore` 备份 |
| ADMIN-03 | 备份/校验脚本技术栈错位（MySQL vs 实际 SQLite） | P0 | 已验证 | scripts/backup_database.sh；scripts/verify_backup.sh；scripts/restore_database.sh；tests/unit/test_backup_admin01_03.py | 并入 ADMIN-01 | 静态已证；✅已动态回归（2026-07-04） | 三个数据库脚本改为 `DATABASE_URL=sqlite:///...` 口径，测试覆盖脚本级备份、校验、恢复闭环 |
| ADMIN-04 | 备份文件完整性校验部分实现可绕过 | P2 | 已验证 | verify_backup.sh；test_backup_admin01_03.py | 0.5d | 静态已证；✅checksum 必需回归（2026-07-04） | 校验脚本 now 强制要求 `.md5` sidecar；缺失/空 checksum/MD5 不匹配均失败，再继续 gzip+SQLite restore+integrity_check |
| ADMIN-05 | admin_stats 路由死壳 fallback 占位 | P2 | 已验证 | endpoints/admin_stats.py；tests/unit/test_admin_stats_admin05_06.py | 0.5d | 静态已证；✅已动态回归（2026-07-04） | `admin_stats.py` now 提供真实 `/stats` route；RPT-15 同一 admin_stats 占位随本项消除 |
| ADMIN-06 | /admin/stats 系统指标关键指标全硬编码（99.9%/0 错误率/从未备份） | P1 | 已验证 | admin_stats.py；admin_compat.py；tests/unit/test_admin_stats_admin05_06.py | 1d | 静态已证；✅已动态回归（2026-07-04） | `/admin/stats` now 聚合用户/角色/权限/登录/审计、备份元数据、数据库与存储体积；admin_compat 复用同一采集器 |
| ADMIN-07 | 行政管理（用品/车辆/资产/费用）全硬编码+写端点缺失（404） | P1 | 待修 | admin_compat.py:18-186,254 | 2-3d | 静态已证 | 前端 admin.js:123-160 POST 必 404 |
| ADMIN-08 | Prometheus/Grafana 监控栈装饰性（无 /metrics 端点） | P1 | 已验证 | app/main.py；auth_middleware.py；monitoring/prometheus.yml；tests/unit/test_prometheus_metrics_admin08.py | 2-3d | 静态已证；✅/metrics+认证白名单+配置回归（2026-07-04） | 根 `/metrics` now 返回 Prometheus text/plain 指标并白名单放行；Prometheus 配置不再直接抓 `mysql:3306`/`redis:6379`，数据库/Redis exporter 待部署时单独加 job |
| ADMIN-09 | 健康检查常量返回不查依赖 | P2 | 已验证 | app/main.py；tests/unit/test_health_check_admin09.py | 0.5d | 静态已证；✅已动态回归（2026-07-04） | `/health` 与 `/api/health` 返回数据库、调度器、Redis 状态；数据库/配置 Redis 异常会降级为 `degraded` |
| ADMIN-10 | 调度器指标/状态页真采集但内存态+不可抓取（重启清零） | P2 | 待修 | utils/scheduler_metrics.py:1-13 | 1d | 静态已证 | 关联 ADMIN-20 取证能力 |
| ADMIN-11 | 项目缓存层安慰剂（内存模式零命中） | P2 | 待修 | projects/project_crud.py:150 | 1d | 静态已证 | — |
| ADMIN-12 | 缓存管理端点调不存在的方法基本不可用（clear 会 flushdb 整库） | P1 | 已验证 | projects/cache.py；tests/unit/test_projects_cache_admin12.py | 0.5d | 静态已证；✅已动态回归（2026-07-04） | `/projects/cache/clear` now 只清 project 命名空间/白名单 pattern；不调用 `clear/flushdb`，前端 `pattern=project:detail:*` 已兼容 |
| ADMIN-13 | 数据导入执行字段与模型不符→假失败真入库 | P1 | 已验证 | data_import_export/import_upload.py；tests/unit/test_data_import_upload_admin13_14.py | 0.5d | 静态已证；✅已动态回归（2026-07-04） | 导入数据与 `DataImportTask` 改为同一事务提交；任务字段对齐真实模型字段 `task_no/import_type/file_name/imported_by` |
| ADMIN-14 | 导入错误回执明细被丢弃任务表不落错误 | P2 | 已验证 | data_import_export/import_upload.py；schemas/data_import_export.py；tests/unit/test_data_import_upload_admin13_14.py | 并入 ADMIN-13 | 静态已证；✅已动态回归（2026-07-04） | `failed_rows` 同步写入 `validation_errors/error_message` 并随 `ImportUploadResponse` 返回 |
| ADMIN-15 | 导入部分失败/幂等：逐行容错+工时查重符合设计 | P3 | 已验证 | timesheet_importer.py:169 | — | 静态已证（正面确认） | 无缺陷 |
| ADMIN-16 | 导出水印 watermark_service 死代码全仓零调用 | P1 | 待修 | services/export/watermark_service.py | 1-2d | 静态已证 | 且中文渲染黑方块需注册 CID 字体 |
| ADMIN-17 | 统一文件上传服务孤儿；无内容校验/AV | P2 | 待修 | services/file_upload_service.py | 1-2d | 静态已证 | — |
| ADMIN-18 | 合同附件上传/下载任意文件读取漏洞 | P0(安全) | 已验证 | sales/contracts/enhanced_attachments.py；sales/contracts/enhanced.py；attachment_security.py；tests/unit/test_contract_attachment_security_admin18.py | 1d | 静态已证；✅已动态回归（2026-07-04） | 新旧两个下载入口 now 统一使用上传根目录路径校验；绝对路径/路径穿越返回 403，合法相对路径映射到 `UPLOAD_DIR` |
| ADMIN-19 | 附件-单据串联删单不删文件 343 孤儿文件 | P2 | 待修 | documents/operations.py:148 | 1-2d | 静态已证 | project_documents file_path 全 /demo/ 假路径 |
| ADMIN-20 | 日志管理/轮转不存在（仅 stdout，logs/ 空） | P2 | 待修 | core/logging_config.py:145 | 1d | 静态已证 | 配合 ADMIN-10 故障后几乎零取证能力 |
| ADMIN-21 | debug_issue/design_review 两 sync 真实现 | P3 | 已验证 | debug_issue_sync_service.py | — | 静态已证（正面确认） | 无缺陷 |
| ADMIN-22 | 编码规则生成器无统一功能，分散硬编码+并发撞号 | P2 | 待修 | business_support_utils/service.py:180-204 | 1-2d | 静态已证 | — |
| ADMIN-23 | 运维自助度：多数运维操作必须进服务器/改库 | P1(汇总) | 待修 | 见 ADMIN-01/06/12/20/22 | 汇总 | 静态已证 | 正面项：调度热 reschedule/导入模板/excel_export |

**ADMIN 域小结**：本域"真实现"比例各域最低。备份 API / restore / SQLite 脚本口径已完成动态回归（ADMIN-01/02/03）；admin_stats 占位与系统统计硬编码已修复（ADMIN-05/06）；Prometheus `/metrics` 与抓取配置已修复（ADMIN-08）；健康检查已接入依赖状态（ADMIN-09）；数据导入假失败与错误明细丢失已修复（ADMIN-13/14）；ADMIN-18 合同附件任意文件读取已修复。剩余重点仍包括行政管理硬编码与写端点缺失、缓存管理调不存在方法、日志轮转缺失。约 9-12 人日，ADMIN-04/07/12/20 可作为下一批。

### 十、多租户域（TEN，8 项）

| ID | 功能/问题 | 等级 | 状态 | 证据位置 | 工作量 | 验证方式 | 备注/关联 |
|---|---|---|---|---|---|---|---|
| TEN-01 | 租户管理 API 全 404（四路盲猜 import 全不存在落空路由） | P1 | 已验证 | endpoints/tenants.py；services/tenant_service.py；tests/unit/test_tenant_management_routes_ten01.py | 1d | 静态已证；✅单元/路由回归（2026-07-04） | 空 shim 已替换为真实 `/tenants` CRUD/init/stats 路由并接 `TenantService`；超级管理员门禁已直测；TEN-02/03/04/06 的隔离/列/上下文问题仍待单独收口 |
| TEN-02 | TenantQuery 在 SQLA 2.0 形同虚设（只重写 __iter__，.all() 走 _iter 绕过） | P1 | 待修 | 全局 sessionmaker TenantQuery | 2-3d | 静态已证 | 改 with_loader_criteria+do_orm_execute 事件 |
| TEN-03 | 96.8% 业务表无 tenant_id；projects.tenant_id 是幽灵列 | P1 | 待修 | DB 实测 557 表仅 18 表有 tenant_id | 先 Project 3-4d/全量 2-3 周 | 静态已证 | customers/sales_orders/contracts/invoices 全无 |
| TEN-04 | 业务域查询层租户过滤≈0（项目/销售/采购/财务/报表 0 处） | P1 | 待修 | 显式 filter 仅 15 文件~65 处全在角色/权限/用户/库存 | 并入 02/03 | 静态已证 | — |
| TEN-05 | 隔离装饰器/工具全家 0 使用死代码 | P2 | 待修 | 隔离装饰器 | 删 0.5d | 静态已证 | — |
| TEN-06 | 无租户上下文全链 fail-open+存量违反自身不变量 | P1 | 待修 | 中间件无 user 置 None 放行；TenantQuery 无 tenant 仅 warning | 1-2d | 静态已证 | DB 178/195 用户 tenant_id=NULL 且 163 非超管畅通；修 fail-closed |
| TEN-07 | 配额/套餐/生命周期全不执行（暂停/过期租户照常登录） | P2 | 待修 | max_users/SUSPENDED/expired_at 无调用方 | 1-2d | 静态已证 | — |
| TEN-08 | 租户上下文注入机制（中间件已注册顺序正确） | — | 已验证 | TenantContextMiddleware，main.py:70 | — | 静态已证（正面确认） | 作 F11 复用基座 |

**TEN 域小结**：上下文注入机制真（TEN-08），其余全假——无管理 API（404）、97% 表无列、查询 0 过滤、框架过滤被 SQLA 2.0 绕过、全链 fail-open、配额不执行。**现在不能给第二个客户开租户。** 最短路径 = TEN-01 补路由→TEN-06 数据归户+fail-closed→TEN-02 换 with_loader_criteria→TEN-03 按域加列（先 Project）。ROADMAP F11 判断成立且比想象更严重。

### 十一、报表/经营分析域（RPT，17 项）

| ID | 功能/问题 | 等级 | 状态 | 证据位置 | 工作量 | 验证方式 | 备注/关联 |
|---|---|---|---|---|---|---|---|
| RPT-01 | 报表中心 8+ 类型返回"待实现"桩但权限矩阵照常展示 | P1 | 已验证 | report_data_generation/core.py；router.py；report_center/configs.py；tests/unit/test_report_center_rpt01.py | 做实/下架 | 静态已证；✅已动态回归（2026-07-04） | 报表中心 now 只展示/授权真实可生成的 6 类；未实现类型直调返回 error，不再空 200 |
| RPT-02 | PROJECT_MONTHLY 成本恒 0 | P2 | 已验证 | project_reports.py；tests/unit/test_project_monthly_report_rpt02.py | 1d | 静态已证；✅已动态回归（2026-07-04） | 月报 now 汇总报表期间内 `ProjectCost` ACTUAL 口径 + `FinancialProjectCost`，并计算预算差额/差额率；不再 `actual_cost` 恒 0 |
| RPT-03 | WORKLOAD/COST_ANALYSIS 人工成本=工时×硬编码 100 | P2 | 已验证 | report_labor_cost.py；analysis_reports.py；report_framework/generators/analysis.py；tests/unit/test_analysis_reports_rpt03.py | 0.5d | 静态已证；✅已动态回归（2026-07-04） | COST_ANALYSIS now 按每条工时的 `user_id + work_date` 读取 `HourlyRateService`；同一工程师跨日期变更时薪可正确分段，旧/新报表入口均覆盖 |
| RPT-04 | 财务报表 4 端点无数据静默降级硬编码 demo，预算=成本×1.08 | P1 | 已验证 | finance_reports.py；tests/unit/test_finance_reports_rpt04.py | 2-3d | 静态已证；✅已动态回归（2026-07-04） | 月趋势/成本分析/项目盈利/现金流 no-data 不再返回 demo；成本预算 now 汇总 `ProjectBudgetItem`（APPROVED+active），预算-only 类目也返回 |
| RPT-05 | 财务报表含税/不含税口径不分 | P2 | 已验证 | finance_reports.py；tests/unit/test_finance_reports_rpt05.py | 与 SALES-17 打包 | 静态已证；✅已动态回归（2026-07-04） | 月趋势/成本分析/项目盈利/现金流 now 显式输出不含税、税额、含税字段；成本旧键保留不含税，收入/现金旧总额键保持兼容 |
| RPT-06 | report_center xlsx 导出明细恒"无数据"（双键名+data 键不匹配） | P1 | 已验证 | report_center/generate/export.py；excel_renderer.py；tests/unit/test_report_center_export_rpt06.py | 0.5d(Quick-win) | 静态已证；✅已动态回归（2026-07-03） | 旧导出分支 now 将 details 转为 renderer 需要的 `data + columns`；同时修复 CSV 分支局部 `datetime` 导入导致 xlsx 更新 exported_at 500 的作用域问题 |
| RPT-07 | template_report 三套并存两 orphan+一断链 import | P2 | 已验证 | template_report/core.py；template_report_service.py；report_framework/adapters/template.py；tests/unit/test_template_report_rpt07.py | 1-2d | 静态已证；✅已动态回归（2026-07-04） | 旧根服务 now 仅兼容转发到 `TemplateReportCore`；adapter 不再 import 断链符号；package 旧路径保留懒加载代理 |
| RPT-08 | PPT 生成器真产 pptx 但内容 100% 硬编码+0 调用方 | P3 | 已验证 | ppt_generator/generator.py；ppt_generator/builders/*；tests/unit/test_ppt_generator_rpt08.py；tests/unit/test_ppt_generator.py | 下架/做实 | 静态已证；✅已动态回归（2026-07-04） | 主入口 now 必须显式传入 `deck_spec`，内容来自调用方数据；硬编码营销 deck 已移除，builder 兼容路径补齐 |
| RPT-09 | 8 个工作台适配器统计卡因 label= vs 必填 title= 全部恒空（~46 张卡） | P1 | 已验证 | schemas/dashboard.py；tests/unit/test_dashboard_stat_card_rpt09.py；unified.py:66 静默吞 | 1-1.5d | 静态已证；✅已动态回归（2026-07-03） | `DashboardStatCard.title` 已兼容旧 `label` 输入且输出仍为 `title`；保留旧 adapter 的 `icon/color`；8 个旧 `label=` adapter 空库 smoke 均能产出标题 |
| RPT-10 | 决策驾驶舱 4 处 KPI 绑不存在字段恒 0 | P1 | 已验证 | useExecutiveDashboard.js；useExecutiveDashboard.test.js | 1d | 静态已证；✅已动态回归（2026-07-04） | 活跃项目无 `project_growth` 时显示项目总数，不再假写较上月 0%；交付准时率读取 `delivery-rate` 归一化后的 `rate/on_time_projects/total_projects`，memo 依赖补 `deliveryData` |
| RPT-11 | 驾驶舱营收/利润前端 Math.min(×0.3) 封顶+目标写死+毛利冒充净利润 | P1 | 已验证 | useExecutiveDashboard.js；useExecutiveDashboard.test.js | 删封顶 0.5d | 静态已证；✅已动态回归（2026-07-03） | 前端 KPI now 显示真实合同额，不再按全年目标 30% 裁剪；利润卡改为“项目毛利”，口径为合同额减实际成本或后端显式 gross_profit |
| RPT-12 | 驾驶舱成本页签/销售漏斗恒空（useState 无 setter），健康度结果丢弃 | P2 | 已验证 | useExecutiveDashboard.js；useExecutiveDashboard.test.js | 1d | 静态已证；✅已动态回归（2026-07-04） | 健康分布接口结果 now 写入 `healthData`；成本数据从 summary 生成已用/剩余预算；销售漏斗接 `/sales/statistics/funnel` 真实数据；`costData/salesFunnelData` 已补 setter |
| RPT-13 | 采购看板"节省金额"写死 0 | P2 | 已验证 | dashboard/stats.py；tests/unit/test_dashboard_procurement_stats_rpt13.py | 0.5d(Quick-win) | 静态已证；✅已动态回归（2026-07-04） | 采购统计 now 按来源采购申请预估金额 - 关联采购订单实际金额聚合正差；含税金额优先，含税为 0 回退 `total_amount`，不再硬写 0 |
| RPT-14 | 成本看板图表配置保存/读取为桩 | P3 | 已验证 | dashboard/cost_dashboard.py；models/dashboard_chart_config.py；schemas/dashboard.py；tests/unit/test_cost_dashboard_chart_config_rpt14.py | 1d | 静态已证；✅已动态回归（2026-07-04） | 图表配置 now 持久化到 `dashboard_chart_configs`；保存返回 id，读取按 id 查库，缺失 404；`/chart-config/{config_id}` 已排在 `/{project_id}` 前 |
| RPT-15 | admin_stats 整体占位 fallback | P2 | 重复-合并→ADMIN-05 | admin_stats.py:7-23 | — | 静态已证 | 与 ADMIN-05 同一文件同一占位，ADMIN-05 为主 |
| RPT-16 | 负荷瓶颈接口 dept.name 字段不存在必 500（模型只有 dept_name） | P2 | 已验证 | workload.py:373；organization.py:59-62 | 0.1d(Quick-win) | 静态已证；✅已补回归验证（2026-07-03） | 当前 Department.name 兼容属性返回 dept_name；已新增超载部门 API 合约测试 |
| RPT-17 | 报表框架主干（引擎/17 适配器/YAML/Excel·Word 渲染/销售域导出） | — | 已验证 | engine.py:126；excel_export_service.py:106-235 | — | 静态已证（正面确认） | 无缺陷 |

**RPT 域小结**：框架和大部分聚合真（RPT-17）；"待实现"桩静默返回空 200（RPT-01）、demo 硬编码兜底/前端封顶（RPT-04/11）、schema 契约断裂（RPT-06/09/10）、template_report 三套并存（RPT-07）、PPT 硬编码孤岛（RPT-08）、含税/不含税口径混用（RPT-05/SALES-17）已先后收口。RPT 域当前无独立待修项。

### 十二、边缘业务模块域（MISC，24 项）

| ID | 功能/问题 | 等级 | 状态 | 证据位置 | 工作量 | 验证方式 | 备注/关联 |
|---|---|---|---|---|---|---|---|
| MISC-01 | 竞品分析菜单页展示虚构数据（后端硬编码+前端 0 次 API 调用） | P0 | 已验证 | competitor_analysis.py；salesRoutes.jsx；sidebarConfig/default.js；tests/api/test_competitor_analysis_stopgap_contracts.py；salesCompetitorAnalysisStopgap.test.jsx | 下架 0.5d | 静态已证；✅已下架止血并回归（2026-07-03） | 菜单与 `/sales/competitor-analysis` 路由已移除；后端直链返回 501，不再吐“竞品A/宁德时代”等硬编码假数据 |
| MISC-02 | 资源总览 PMO 可达页恒空白 | P1 | 已验证 | resource_overview.py；pmo_cockpit_service.py；pmo.py；ResourceOverview.jsx；resourceOverview.js；tests/unit/test_resource_overview_misc02.py；ResourceOverview.test.jsx | 聚合 1d/摘菜单 0.5h | 静态已证；✅已动态回归（2026-07-04） | 前端 now 调真实 `/pmo/resource-overview`，旧 `/resource-overview` 占位挂载已下架为 501；PMO 响应补 `employees/avg_utilization/conflicts`，无 allocation 时展示真实资源总数和部门汇总，不再吃 placeholder 空页 |
| MISC-03 | 预警超时升级任务坏死（对 Column 取布尔导致查询短路） | P1 | 已验证 | alert_escalation_task.py；tests/unit/test_utils_missing.py | 0.5d | 静态已证；✅已动态回归（2026-07-03） | 与 APPR-17/AS-25 的 841 饿死不同源，是升级任务本身崩；未升级判断改 SQL 表达式并纳入 OPEN/PENDING/ACKNOWLEDGED/PROCESSING |
| MISC-04 | best_practice(P0 优化 4 端点) 僵尸+半成品（从未注册、0 commit、无认证） | P2 | 已验证 | best_practice.py；projects/__init__.py；tests/unit/test_best_practice_legacy_misc04.py | 0.5d | 静态已证；✅已动态回归（2026-07-04） | 旧 `best_practice.py` 仍未挂载主路由；潜在写端点已补 `material:update/supplier:update/project:update`；真实前端路径继续走已挂载 `/projects/best-practices` |
| MISC-05 | endpoints/knowledge 僵尸三无（表不存在挂载即 500，硬编码冒充 AI） | P2 | 已验证 | endpoints/knowledge/__init__.py；api.py；api_lazy.py；knowledge.js；knowledgeBase.js；tests/unit/test_knowledge_legacy_misc05.py | 下架 0.5d | 静态已证；✅已动态回归（2026-07-04） | 旧 `endpoints/knowledge` 自动沉淀聚合路由已下架为 501 stopgap，不再聚合依赖 `knowledge_entries/knowledge_alerts` 的 extraction/induction/alerts/search；主路由当前未挂 legacy `/knowledge`，前端继续走 `/knowledge-base` 或 `/service/knowledge-base` |
| MISC-06 | documents 文档中心上传端到端不可用（无 multipart 端点前端必 422） | P1 | 已验证 | documents/crud_refactored.py；projects.js；Documents.test.jsx；routeContracts.test.js；tests/unit/test_documents_upload_misc06.py | 1d | 静态已证；✅已动态回归（2026-07-04） | 新增 `/documents/upload` multipart 上传端点；`documentApi.create(FormData)` now 走上传路由；项目级创建权限改 `document:create`；列表层过滤 `/demo/` 假文件路径，避免 60 行 demo 文档继续冒充真实文件 |
| MISC-07 | advantage_products 133 行真数据不可达（前端组件孤儿无入口） | P1 | 已验证 | AdvantageProducts.jsx；presalesRoutes.jsx；sidebarConfig/default.js；presales.js；import_excel.py；tests/unit/test_advantage_products_misc07.py | 0.5d | 静态已证；✅已动态回归（2026-07-04） | 已新增 `/presales/advantage-products` 路由和侧边栏“优势产品”入口；导入接口前后端默认 `clear_existing=false`，避免误清库；搜索框不再默认显示 unknown |
| MISC-08 | change_impact 占位上线真路由未挂 | P2 | 已验证 | api.py；change_impact.py；projects/change_impact.py；tests/unit/test_change_impact_misc08.py | 0.5d | 静态已证；✅已动态回归（2026-07-04） | 主 `api.py` now 挂载真实 `/project-change-impacts/*`；旧 `/change-impact` shim 下架为 501 stopgap，不再返回 `change_impact module placeholder`；默认库存在 `project_change_impacts` 表 |
| MISC-09 | cost_collection POST/collect 缺 RBAC（任何用户可全量触发写库归集） | P1 | 已验证 | cost_endpoints/collection.py；tests/unit/test_cost_collection_permissions_misc09.py | 0.5d | 静态已证；✅已动态回归（2026-07-04） | `/cost-collection/collect` now 要求 `cost:manage`；读侧 status/by-project 仍为登录可读；与 PROJ-11 成本归集口径问题互引但权限漏洞已收口 |
| MISC-10 | cost_variance 成本偏差真功能·隐身（无菜单入口，无数据权限） | P2 | 已验证 | cost_endpoints/variance_analysis.py；tests/unit/test_cost_variance_misc10.py | 0.5d | 静态已证；✅已动态回归（2026-07-04） | `/cost-variance` 三端点 now 要求 `project:read`；`/{project_id}` 不存在抛 404；`summary` 成本类型 breakdown 改为一次 grouped 查询，消除逐项目 N+1 |
| MISC-11 | solution_credits 僵尸+刷分漏洞（自退任意积分） | P2 | 已验证 | solution_credits/internal.py；tests/unit/test_solution_credits_permissions_misc11.py | 0.5h | 静态已证；✅已动态回归（2026-07-04） | `/solution-credits/internal/refund` now 要求 `solution_credit:manage`；退款数量 Query 加 `ge=1/le=1000` 边界；用户自助查询/检查仍保持登录可用 |
| MISC-12 | performance_contract 裸 sqlite3+import 期 DDL | P1 | 重复-合并→HR-15 | contract.py:28,140 | — | 静态已证 | 与 HR-15 同一 performance_contract 裸 sqlite3，HR-15 为主 |
| MISC-13 | project_contributions 闭环断裂（前端仅 getReport 接了页面，报告页永远空） | P2 | 已验证 | ProjectContributionReport.jsx；project_contribution_service.py；tests/unit/test_project_contributions_misc13.py；ProjectContributionReport.test.jsx | 1d | 静态已证；✅已动态回归（2026-07-04） | 报告页默认不再强塞当前月 period，改为全周期读取以避免默认库 `pr30222` 脏周期导致空页；页面 now 接 calculate 和 PM rate；后端报告行补 `period`，全周期视图能按行评分 |
| MISC-14 | pm_involvement 零鉴权+数据源桩致误判（6 端点全无 auth 含写语义） | P1 | 已验证 | performance/pm_involvement.py；pm_involvement_service.py；presale/tickets/crud.py；tests/unit/test_pm_involvement_misc14.py | 1d | 静态已证；✅已动态回归（2026-07-04） | 6 端点已补鉴权：POST 判断/自动判断/通知生成需 `presale:manage`，GET 查询/示例需登录；相似项目/失败数查 `Project`，标准方案查启用模板库，工单创建和 auto-judge 不再固定 0/False |
| MISC-15 | relationship_maturity 假数据+必崩（improvement-plan 引用未定义变量 NameError 500） | P1 | 已验证 | relationship_maturity.py；RelationshipMaturity.jsx；relationshipMaturity.js；tests/unit/test_relationship_maturity_misc15.py | 1d | 静态已证；✅已动态回归（2026-07-04） | 客户评估 now 查真实客户并调用 `RelationshipScoringService`；缺失客户 404；improvement-plan 修复 `gap` NameError 且移除固定人名；portfolio 读取 `customer_relationship_scores` 最新记录；前端不再内置宁德/比亚迪样例，改走真实 API |
| MISC-16 | RequirementSurvey 前端孤儿+后端 404 僵尸 | P2 | 已验证 | api.js；RequirementSurvey/index.jsx；RequirementSurvey.test.jsx；routeContracts.test.js | 0.5d | 静态已证；✅已动态回归（2026-07-04） | 当前活页已接 `presaleApi.tickets` 售前工单上下文；已删除旧 `surveyApi`、`useRequirementSurvey` hook 和 `/requirement-surveys` barrel export，避免继续调用无后端路由 |
| MISC-17 | resource_scheduling 占位+完全僵尸 | P2 | 已验证 | api.py；resource_scheduling.py；engineer_scheduling.py；tests/unit/test_resource_scheduling_misc17.py | 下架 0.5h | 静态已证；✅已动态回归（2026-07-04） | 主 `api.py` 已移除 legacy `/resource-scheduling` 挂载；旧 shim 下架为 501 stopgap；真实 `/engineer-scheduling` 保留且前端契约回归通过 |
| MISC-18 | business_support 前缀丢失 5 组 API 全 404 | P1 | 已验证 | api.py:824；business_support/__init__.py；dashboard.py；contract_review.py；payment_reminders.py；tests/unit/test_business_support_prefix_misc18.py | 0.5d | 静态已证；✅已动态回归（2026-07-04） | 主路由 now 挂 `/business-support`；dashboard/bidding/contract-review/payment-reminder/todos 前端路径全部注册；旧 contracts/payment-reminders 兼容保留 |
| MISC-19 | business_support_orders 发货审批绕过统一引擎 | P2 | 已验证 | delivery_orders/crud.py；approval_engine/adapters/delivery_order.py；init_approval_data.py；DeliveryDetail.jsx；tests/unit/test_business_support_delivery_approval_misc19.py | 1d | 静态已证；✅已动态回归（2026-07-04） | 现场校正：开票/对账等已有真实表/路由，不按“全僵尸”处理；发货审批已补 `DELIVERY_ORDER` 适配器、`TPL_DELIVERY_ORDER` 模板/迁移、`submit-approval`，旧 approve 入口必须先有统一审批实例和当前待办任务才会落状态 |
| MISC-20 | budget 写操作权限全配成 budget:read（接前端即越权） | P2 | 已验证 | budgets.py；items.py；allocation_rules.py；tests/unit/test_budget_permissions_misc20.py | 0.5d | 静态已证；✅已动态回归（2026-07-04） | 预算 update/submit→`budget:update`，delete→`budget:delete`；明细写操作→`budget:update`；分摊规则 create/update/delete→对应权限，读接口保留 `budget:read` |
| MISC-21 | budget 整体审批自闭环+前端僵尸+脏数据（total≠Σitems） | P2 | 已验证 | budgets.py；approval_engine/adapters/budget.py；init_approval_data.py；BudgetManagement.jsx；tests/unit/test_budget_approval_flow_misc21.py；20260704_project_budget_approval_sqlite.sql | 1d | 静态已证；✅已动态回归（2026-07-04） | 预算 submit/approve now 接 `PROJECT_BUDGET` 统一审批实例/待办；`TPL_PROJECT_BUDGET` 种子和迁移已补；创建/提交/审批按明细重算总额，迁移临时库验证 60 条 mismatch→0；预算页优先读 `budgetApi.list`，无预算单再回退项目预算看板 |
| MISC-22 | alerts 自定义规则 CRUD 是摆设（通用引擎无生产调用方） | P2 | 已验证 | alerts/rules.py；init_permissions_data.py；usePermission.js；tests/unit/test_alert_rules_misc22.py | 降级 0.5d | 静态已证；✅已动态回归（2026-07-04） | 降级止血：读规则/模板 now 要求 `alert:read`，create/update/toggle/delete now 要求 `alert:manage`；补权限种子和前端常量。生产调度接入仍不宣称已完成，实际产警继续走各域硬编码链路 |
| MISC-23 | culture_wall config 占位+goals 前端 404+空播 | P2 | 已验证 | culture_wall_config.py；contents.py；admin.js；ChairmanWorkstation.jsx；GeneralManagerWorkstation.jsx；tests/unit/test_culture_wall_misc23.py | 1d | 静态已证；✅已动态回归（2026-07-04） | `culture_wall_config` placeholder 已替换为真实配置 CRUD；`/culture-wall/contents/{id}` 已补 PUT/DELETE 并落库清阅读记录；前端 goals 改走 `/culture-wall/personal-goals`，工作台点击目标不再跳未注册 `/personal-goals` |
| MISC-24 | ai_strategy 旧别名/占位路由+前端 5 接口全 404 | P2 | 已验证 | api.py；ai_strategy.py；aiStrategy.js；strategyRoutes.jsx；sidebarConfig/default.js；tests/unit/test_ai_strategy_misc24.py | 下架 0.5d/重写 5d+ | 静态已证；✅已动态回归（2026-07-04） | 现场校正：当前后端实际只有兼容占位 shim，真实战略能力在 `/strategy`；已移除主路由 `/ai-strategy` 挂载、删除 AI 战略助手入口和死 API，保留未挂载 501 shim 防误挂 |

**MISC 域小结**：24 个边缘模块以"僵尸/半成品/假实现"为主。P0 唯 MISC-01（用户正看虚构竞品数据）已下架止血；P1 集群：MISC-02 资源总览已改走真实 PMO cockpit 并补汇总/明细响应、MISC-03 升级任务坏死（已修复）、MISC-12 裸 sqlite3+启动 DDL（并入 HR-15）、人事 PII 入库。MISC-04 legacy best_practice 下架确认+潜在权限、MISC-05 legacy endpoints/knowledge 已下架为 501 stopgap、MISC-06 文档上传 multipart 契约/写权限/demo 假路径、MISC-07 优势产品入口/导入默认安全值、MISC-08 change_impact 主路由已挂真实 `/project-change-impacts` 且旧占位下架、MISC-09 归集无 RBAC、MISC-10 成本偏差权限/404/N+1、MISC-11 积分自退刷分、MISC-13 项目贡献报告默认全周期并接 calculate/rate 闭环、MISC-14 PM 介入零鉴权/数据源桩、MISC-15 关系成熟度前后端假数据/NameError 已接真实评分与记录、MISC-16 RequirementSurvey 旧 `/requirement-surveys` 死链已移除、MISC-17 legacy resource_scheduling 已下架且保留真实 `/engineer-scheduling`、MISC-18 商务支持 5 组 404 已补前后端契约/权限、MISC-19 发货审批已接统一审批引擎并保留旧按钮兼容、MISC-21 预算提交/审批已接统一审批且修总额口径/前端预算接口接入、MISC-22 自定义预警规则 CRUD 已权限降级止血、MISC-23 文化墙配置/内容/目标链路已补真实 CRUD 与前端契约、MISC-24 legacy `/ai-strategy` 与 AI 战略助手死 API 已下架。

## 视图一：17 项全局 P0 → 追踪 ID 映射

| 全局P0# | 问题 | 对应追踪 ID |
|---|---|---|
| 1 | 4 条审批链 template_code 错位，提交必失败且 200 掩盖 | APPR-01 |
| 2 | 审批模板无种子/迁移，新环境全审批不可用 | APPR-02 |
| 3 | 报价资金三连（状态直改 + 审批后改明细 + 成本漏乘数量） | SALES-01 + SALES-02 + SALES-03 |
| 4 | 回款登记无勾稽、无权限、错配发票 | SALES-04 |
| 5 | 会签驳回语义破坏，REJECTED 可翻转 | APPR-03 |
| 6 | 收货→库存断链（收货不入库/领料不扣库/调拨不动库/在途恒0） | PROD-03 + PROD-11 + PROD-04 + PROD-12 + PROD-14（打包） |
| 7 | 智能缺料预警引擎引用不存在字段必 500 | PROD-02 |
| 8 | 结项无门禁 + 变更审批不回基线 | PROJ-06（已验证：结项 readiness 门禁） + PROJ-20（已验证：变更审批回基线） |
| 9 | 现场调试签到/完工全链假实现 | PROD-01（主）＋ AS-01（重复-合并） |
| 10 | 14/56 定时任务 stub 且监控全绿 | APPR-04 |
| 11 | 通知触达假成功（email/SMS 假桩 + Redis 有产无消 + 841 条饿死） | AS-02（已验证） + AS-15（已验证） + AS-03（已验证） + APPR-17（已验证） |
| 12 | BOM→生产工单断链 | PROD-08（主）＋ APPR-05（重复-合并） |
| 13 | 售后无设备档案，工单无设备外键 | AS-10（主，已验证）＋ AS-11（已验证）＋ APPR-06（重复-合并） |
| 14 | 派工冲突检测空转 | AS-04（已验证） |
| 15 | 销售预测接口整文件硬编码 | SALES-06（+ SALES-07 前端假兜底） |
| 16 | 发票门禁读旧轨空表 + update_invoice 绕上限/状态 | APPR-10 + APPR-11（+ SALES-09 权限、PEER-04/05 关联） |
| 17 | 合同审批撤回必 500（4 域，CONFIRMED） | APPR-07（主）＋ PEER-03（重复-合并） |

> 注：全局 P0 表为跨域去重后的危害排序视角；APPR-07/10/11、PROD-08、AS-10/11 在域内总表定级 P1，本台账等级列以域内总表为准，全局定级在备注标注。

## 视图二：按修复批次分组（对应汇总报告第四节）

| 批次 | 追踪 ID | 合计工作量 |
|---|---|---|
| **P0-0 资金正确性急救包**（插队最前） | SALES-03 → SALES-01 → SALES-02 → SALES-04 → APPR-10 → APPR-11（含 PEER-04）→ APPR-15 → PEER-05 → SALES-09 | 约 6-8d |
| **P0-0' 审批链救活包**（并入/前置 F2） | APPR-01（已验证）→ APPR-02（已验证）→ APPR-07（已验证，含 PEER-03）→ APPR-03（已验证；SALES-10 已随包消除） | 约 4-5d |
| **Quick-win 闸门包**（≤1d/项，本周清完） | PROJ-06（已验证：结项 readiness 门禁）、PROJ-10（已验证：里程碑 except 重抛+全局 complete 接状态机）、PRE-16（已验证：_has_live_ai 补 qwen）、PRE-23（已验证：立项关卡异常不再静默）、AS-19（已验证：关单 payload/id + 质保工单兜底）、APPR-07（已验证：撤回参数名）、AS-16（已验证：Header 铃铛）、PROD-13（已验证：报工回写移审批后）、RPT-02（已验证：项目月报成本真实聚合）、RPT-03（已验证：成本分析按配置时薪）、RPT-06（已验证：xlsx 明细导出）、RPT-09（已验证：工作台 stats 契约）、RPT-10（已验证：驾驶舱 KPI 真实绑定）、RPT-11（已验证：驾驶舱 KPI 不封顶）、RPT-13（已验证：采购看板节省金额真实聚合） | 约 3d |
| **假实现止损下架包** | SALES-06（假接口下架）、SALES-07（前端假兜底）、SALES-13（智能报价页）、PROD-17（AI 排程建议）、PRE-15（售前移动端路由）、PRE-20（AI 工作流编排）、PRE-12（方案"PDF 导出"）、PRE-13（export-report 假 URL） | 约 2d |
| **F1 扩围（库存台账真实化）** | PROD-03（已验证）→ PROD-11（已验证，含 PROD-22）→ PROD-04（已验证）→ PROD-12（已验证）→ PROD-14（已验证）＋ PROD-02（已验证）＋ PROD-05（已验证：齐套口径）＋ PROD-15（已验证：缺料→紧急采购闭环） | 约 13d |
| **F3 扩围（通知+调度可信化）** | AS-02（已验证）、AS-15（已验证）、AS-03（已验证）、AS-06（已验证）、AS-14（已验证：设备保养提醒 + 终验转售后保养计划）、AS-25（已验证）、AS-23（已验证）、PROJ-21（已验证）、APPR-16（已验证）、APPR-17（已验证）、APPR-09（已验证：通用审批超时/预超时调度）、MISC-03（已验证）、PRE-21（已验证，含 APPR-22①）、APPR-04（已验证：P0#10 全量回归 + 缺料 3 件套回填）、APPR-22（已验证：①/②/③/④/⑤） | 约 10-14d |
| **其他（结构性/体验/收口，按域推进）** | 结构断链：已清空；审批收口（F2 相关）：已清空；北极星体验：SALES-11、SALES-12、APPR-18、APPR-14、PROJ-03、PRE-04、PRE-10；数据可信：PROJ-11、PROJ-14、PROJ-16、SALES-08、SALES-15；其余 P2/P3 按域排期 | 余量 |

## 视图三：数据清洗专项清单（存量脏数据，任何状态机修复前置）

| # | 脏数据 | 库内实况 | 关联 ID |
|---|---|---|---|
| 1 | 合同状态大小写两套混杂 | 代码已统一写入 uppercase canonical 且读侧兼容 `ACTIVE/SIGNED/draft/executing/voided/approving`；已补 `20260704_contract_status_normalization_sqlite.sql`，本轮未直接执行真实库写入 | APPR-13（已验证；迁移脚本待发布/执行） |
| 2 | 服务工单状态枚举外脏值 | 新写入已收敛到 `PENDING/IN_PROGRESS/RESOLVED/CLOSED`；存量 89 条中 48 条枚举外值仍需迁移清洗 | AS-05（代码已验证） |
| 3 | 项目状态三套词汇表 | COMPLETED(45)/EXECUTING(35)/ST01(24)/archived，定时任务过滤三套全不匹配 | PROJ-05（PROJ-04/PROJ-25 依赖先清洗） |
| 4 | 商机 assessment_status 两套值 | 已补迁移脚本：ASSESSMENT_COMPLETED→COMPLETED、ASSESSMENT_IN_PROGRESS→IN_PROGRESS、REQUESTED→PENDING；读侧兼容旧值 | PRE-24（已验证） |
| 5 | PO/POI 状态空值与读写字典错位 | PO 空状态 60 条、收货单 status 全空；读侧 ORDERED/PARTIAL_RECEIVED 无写入点 | PROD-11 + PROD-04 |
| 6 | quotation_type 非法枚举 | 已补迁移脚本：AUTO/MANUAL/NORMAL/空值→STANDARD；读取历史列表时也归一化为接口小写档位 | PRE-24（已验证） |
| 7 | 售前工单状态字典分裂 | PROCESSING(1)/REVIEW(1) 存量工单无路可走 | PRE-14 |
| 8 | 商机阶段词表分裂 | 经 advance 到 CLOSING 的商机在 PUT /stage 下为非法值 | SALES-21 |
| 9 | 报价存量版本成本/毛利错算 | qty≠1 的版本成本被低估，需重算脚本 | SALES-03 |
| 10 | project_costs 脏值 | 141 行中 60 行 cost_type 为空 | PROJ-11 |
| 11 | 预警积压 | 841 条 PENDING 积压 4 个月（2026-03-09~06-30）；代码已按最老优先逐批出队，生产一次性处置仍需运维窗口 | APPR-17（代码已验证） |
| 12 | 孤儿表/孤儿实例 | `field_tasks/field_checkins/field_issues` 已接 ORM 模型与现场调试接口；entity_type 空审批实例 3 条仍待清理 | PROD-01（已验证） / APPR-20 |
| 13 | machines 设备数据缺失 | `customer_id/serial_no/warranty` 字段已补；存量 6 台设备仍需业务补录 SN/客户/保修实际值，ship_date 仍为空 | AS-10（代码已验证） |
| 14 | SLA 策略未激活 | 3 条 sla_policies 的 is_active 全 NULL；已按历史 NULL=启用兼容，调度任务会同步新工单 SLA monitor | AS-06（已验证） |
| 15 | 根目录 app.db 为 0 字节空文件 | 真实库在 data/app.db，易误导验证与备份 | 口径事实（汇总报告），建议删除或 README 标注 |

## 视图四：僵尸模块 Top 清单（后端有路由 / 前端零调用）

全局扫描约 **427/3104 端点（~14%）、137 模块前端零调用**。Top18：

| # | 模块/路由 | 端点数 | 关联 |
|---|---|---|---|
| 1 | /ai-strategy | 84 | MISC-24（已下架主挂载；保留未挂载 501 shim 防误挂） |
| 2 | /timesheet-reminders | 26 | api.py:1247 整 router 冗余别名重挂 |
| 3 | /solution-credits | 13 | MISC-11 |
| 4 | /standard-costs | 13 | — |
| 5 | engineer_performance.* | 43 | collaboration 被用非整 router |
| 6 | /production/schedule/* | 10 | — |
| 7 | /ai-planning | 9 | — |
| 8 | /presale-mobile | 9 | PRE-15 |
| 9 | /production/material/* | 9 | — |
| 10 | /acceptance-issues | 9+ | — |
| 11 | production/progress | 8 | — |
| 12 | production/exception | 8 | — |
| 13 | dashboard/cost | 8 | RPT-12 |
| 14 | /auth/2fa+sessions | 10 | — |
| 15 | bonus.rules+allocation | 15 | HR-19 |
| 16 | /sla | 8 | AS-06 |
| 17 | ecn/state-machine | 6 | PROD-09 |
| 18 | /pitfalls | 6 | — |

**四类结构性僵尸**：
1. **占位自引用文件**（27 行自 import 永远 fallback 空 router，剩 6 个）：itr.py、account_unlock.py、backup.py、change_impact.py、quality_risk.py、resource_scheduling.py。`culture_wall_config.py` 已在 HR-22/MISC-23 修实。
2. **丢前缀挂载**：permissions.matrix、performance.individual、business_support 系列（MISC-18）。
3. **双段前缀 bug**：/analytics/analytics/skill-matrix、/kit-check/kit-check/*、/bonus/rules/rules。
4. **冗余别名挂载**：/acceptance（前缀版 44 端点前端用免前缀 legacy）、/technical-specs、/presale-analytics。

## 视图五：前端→后端 404 断链清单（排除第一轮 5 处）

新发现 **118 个唯一断链路径+47 处方法不匹配**。高价值项：

| 前端 service | 调用 | 后端实况 |
|---|---|---|
| aiStrategy.js:14-67 | /ai-strategy/analyze 等 | 已删除前端死 API、AI 战略助手路由和侧边栏入口（MISC-24） |
| businessSupport.js | 16 调用 | 下划线/丢前缀（MISC-18） |
| marginAlert.js | 14 调用 /sales/margin-alerts/* | 后端只有 /margin-prediction/* |
| stageTemplates.js | 13 路径 | 后端仅 2 条只读 GET |
| production.js+assembly.js | 旧 /assembly/* 24 调用 | 已迁 /assembly-kit/* |
| kit.js | /kit-checks* 6 | 后端 /kit-check/work-orders/* |
| assemblyKit.js | /assembly-kit/kit-rates* 5 | 后端 /kit-rate/* |
| admin.js | /admin/leave·meeting-rooms·dashboard、/finance/summary 33 调用 | 后端无（ADMIN-07） |
| analytics.js | skill-matrix/resource-conflicts 12 | 双段前缀 bug |
| solutionVersionService.js | 11 调用 | 后端零 solution-version |
| hr.js | /timesheets/{id}/approve 等 10 | 后端无 |
| purchaseService.ts | /purchase/suggestions/{id}/approve | api.py:232 被注释停用 |
| 整体死 service | survey.js/settings.js/salesProject.js/communication.js/schedulerConfig.js/adminApproval.js/aiSales.js/quotation.js/crm.js | 成批生成从未对齐 |

**四类根因**：前缀丢失、双段前缀 bug、下划线 vs 连字符、旧路径未迁移/成批生成从未对齐的骨架 service。

## 视图六：安全与合规新发现（第二轮）

| ID | 一句话 | 等级 |
|---|---|---|
| ADMIN-18 | 合同附件下载无目录白名单，可 POST 任意 file_path→GET 拖走整库/私钥（任意文件读取） | P0(安全) |
| MISC-11 | solution_credits POST/internal/refund 原任何登录用户可给自己退任意积分；已改为 `solution_credit:manage` 权限门禁（2026-07-04） | P2（已验证） |
| MISC-14 | pm_involvement 原 6 端点全无 auth；已补登录/`presale:manage` 权限，且 test 示例端点不再匿名可读（2026-07-04） | P1（已验证） |
| MISC-09 | cost_collection POST/collect 原仅要求登录；已改为 `cost:manage` 权限门禁（2026-07-04） | P1（已验证） |
| MISC-10 | cost_variance 原 summary/patterns/detail 仅登录可读，且 detail 缺失项目返 200；已改为 `project:read`、404、summary grouped 查询（2026-07-04） | P2（已验证） |
| MISC-04 | legacy best_practice 原 4 个潜在写端点均无认证；已确认未挂载主路由并补写权限门禁（2026-07-04） | P2（已验证） |
| PERM-11 | require_permission 覆盖率 34.6%，142 个 NONE 端点裸奔（通用 CRUD/员工/风险/产能任意登录可调） | P1 |
| PERM-15/16/17 | 数据权限整域裸奔：制造/供应链/财务 0 行级过滤，配置层坏死，CUSTOMER 恒 True | P1 |
| TEN-06 | 多租户无上下文全链 fail-open，163 非超管 tenant_id=NULL 畅通，越权不被拒 | P1 |
| MISC-05* | 人事 PII（ATE-人事档案系统.xlsx 56.8MB）提交进 git 库（misc.md 五·孤儿产物；建议 git-filter 清历史+入受控存储） | P1 |

> *注：任务清单以 MISC-05 指代人事 PII 项，但 misc.md 中 MISC-05 实为 endpoints/knowledge 僵尸；人事 PII 属该报告"五、孤儿产物"节的独立 P1 项、无 MISC 编号，此处按任务口径归入安全视图并标注真实来源。
