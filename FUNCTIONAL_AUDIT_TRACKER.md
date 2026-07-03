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

**2026-07-03 止血进展**：APPR-01/APPR-02 已修复审批模板 code、全失败 200 掩盖与新库审批种子；APPR-03 已补稳定复现并修复会签/或签驳回汇总与终态防复活；APPR-07 已修复并回归；PRE-16 已修复 qwen/百炼 live AI 判断；PRE-23 已修复立项关卡异常静默放行；PROJ-06 已修复结项 readiness 强制门禁；PROJ-10 已修复里程碑完成门禁异常吞掉和全局 complete 旁路；PROD-02/03/04/11/12/14/22 已完成库存入库、在途、领料扣库、调拨动库与缺料扫描 500 止血回归；MISC-01 已下架竞品分析假数据菜单/路由并让直链接口返回 501；SALES-01/02/03/04 已完成报价资金三连与回款勾稽止血回归；SALES-09/APPR-10/APPR-11/PEER-05 已完成发票资金门禁止血回归；SALES-14 已修复付款审批前端 404 断链；SALES-15 已修复销售团队统计/排名恒 0 桩；AS-02/AS-15 已修复邮件/短信触达假成功与工时提醒 SMTP 配置错位；AS-03 已修复通知队列默认同步止血与 worker 导入断裂；AS-06 已修复 SLA 历史 NULL 策略兼容与定时预警扫描；AS-25 已修复预警订阅默认接收人、双 notification resolver 兼容与通用 Webhook URL；APPR-16 已修复 ECN 超期检查调度模块路径；APPR-17 已修复预警通知状态流转和最老优先出队，历史积压需随调度/运维逐批处置；MISC-03 已修复预警超时升级查询短路和 OPEN 状态漏扫；AS-19 已修复客服关单 payload/id 与质保工单兜底列表；RPT-16 已验证负荷瓶颈部门名兼容；APPR-04 已完成 stub 标记、调度失败计数、stub-backed 任务默认禁用，业务回填仍待做；PERM-11 已先补组织员工/HR 档案权限小切口；奖金 payment 端点已补 bonus 权限，HR-17 主审批链仍待修；PRE-21 已修复 AI 后台任务重启恢复与轮询超时；PRE-10 已打通 AI 需求分析下游（方案/报价自动带出 + 确认回填商机需求）。

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
| SALES-06 | 销售预测线上接口整文件硬编码，真算法服务是死代码 | P1 | 已修待验 | sales/sales_forecast.py；services/sales_forecast_service.py；tests/unit/test_sales_forecast_wiring.py | 3-5d | 静态已证；✅契约+P0复现回归（2026-07-03） | 全局P0#15；company-overview 已接线真服务（修模型漂移：Contract 小写状态/est_amount/终态阶段剔除）；其余 8 个零消费假端点 501 下架；团队/个人/驾驶舱做实待排期（ROADMAP F6） |
| SALES-07 | 目标预测页前端假数据兜底、AI 预测卡纯常量 | P1 | 已修待验 | ForecastDashboard.jsx | 1-2d | 静态已证；✅构建+lint 通过（2026-07-03） | AI 预测卡改调真接口（失败显式"暂不可用"）；漏斗改真实枚举键；目标/团队/个人假兜底全部改空态；驾驶舱 tab（整段编造数字）下架 |
| SALES-08 | 销售目标 actual_value 无自动回填，达成率口径未定义 | P1 | 已修待验 | sales/targets.py；sales_team_service.calculate_target_performance；tests/unit/test_sales_target_actuals.py | 2d | 静态已证；✅契约测试回归（2026-07-03） | 列表接口接线 calculate_target_performance 实时计算（LEAD/OPP 按 owner 计数、CONTRACT_AMOUNT 按合同负责人金额、COLLECTION 按发票实收；达成率=actual/target*100）；团队/部门级目标归集口径待定返回 0 |
| SALES-09 | 发票写操作只挂 finance:read + 未签署（草稿）合同可开票 | P1 | 已验证 | sales/invoices/basic.py；sales/invoices/operations.py；models/sales/invoices.py；tests/api/test_sales_invoice_gate_contracts.py | 1d | 静态已证；✅已动态回归（2026-07-03） | 资金急救包；写入口改为 finance:create/update/delete，未签署合同禁止开票，金额上限与状态字段门禁已补 |
| SALES-10 | 合同审批 F1 复核：模板数据已补，但 200 掩盖失败与种子缺口仍在 | P1 | 已验证 | sales/contracts/approval.py；api/v1/endpoints/approval_submit_guard.py；app/utils/init_approval_data.py；tests/api/test_approval_submit_error_contracts.py | 0.5-1d | 静态已证；✅已动态回归（2026-07-03） | 关联 APPR-01/APPR-02；合同审批全失败提交不再 200，新库审批模板种子已补 |
| SALES-11 | 线索转商机丢字段 + 前端写死 skip_validation 绕 G1 | P1 | 待修 | leads/actions.py:56,69-78；LeadManagement.jsx:320 | 1-2d | 静态已证 | 北极星项 |
| SALES-12 | 报价转合同前端断链（后端 from-quote 齐备、前端零入口，金额/版本ID手填） | P1 | 待修 | contracts/basic.py:380-；前端 grep from-quote 零命中 | 2d | 静态已证 | 北极星项；附注"报价明细不成交付物"=APPR-18（以 APPR-18 为主） |
| SALES-13 | 智能报价整页假实现（历史价/竞品/折扣/赢单率全硬编码） | P1 | 待修 | sales/intelligent_quote.py:42-95,204,250,382 | 下架0.5d/做实5d+ | 静态已证 | 止损包；ROADMAP F5 |
| SALES-14 | 付款审批页前端调不存在接口，必 404 | P1 | 已验证 | frontend/src/services/api/paymentApproval.js；frontend/src/pages/PaymentApproval/hooks/usePaymentApproval.js；frontend/src/services/api/__tests__/paymentApproval.test.js；frontend/src/pages/PaymentApproval/hooks/__tests__/usePaymentApproval.test.js | 1d | 静态已证；✅已动态复现并回归（2026-07-03） | 付款审批服务改走统一审批 `/approvals/pending/*` 与 `/approvals/tasks/*`，清除 `/sales/payments/approvals` 404 断链 |
| SALES-15 | 销售团队统计/排名多维度恒 0 桩 | P1 | 已验证 | app/services/sales_team_service.py；app/services/sales_ranking_service.py；app/api/v1/endpoints/sales/team/utils.py；tests/services/test_sales_team_aggregation_contracts.py | 2-3d | 静态已证；✅已动态复现并回归（2026-07-03） | 个人目标、最近跟进、客户分布、跟进统计、线索质量、商机统计均改为真实聚合；/sales/team 与 /sales/team/ranking 消费同一真实 Session 数据 |
| SALES-16 | AI 销售助手降级罐头文本无标注；流失清单从不调 AI | P2 | 已修待验 | sales_ai_assistant_service.py；tests/unit/test_sales_ai_degradation_marking.py；SalesAI/index.jsx | 1d | 静态已证；✅契约测试回归（2026-07-03） | mock 集群（集群2）；5 方法降级统一标 ai_generated/degraded/degraded_reason，真 AI 标 ai_generated=true；流失清单定口径为规则批量扫描（scoring_method=rule_scan+每项 analysis_source），单客户深评走 predict_churn_risk 真 AI；前端 4 卡片显示降级横幅 |
| SALES-17 | 报价域无税率/含税建模 | P2 | 待修 | quotes.py:430；quote_versions.py:243 | 2-3d | 静态已证 | — |
| SALES-18 | 报价"当前版本"口径不一致（versions[-1] vs current_version_id） | P2 | 已验证 | quote_costs.py；tests/api/test_sales_quote_costs_quantity_contracts.py | 0.5d | 静态已证；✅已动态复现并回归（2026-07-03） | 成本分析当前版本改为优先使用 Quote.current_version_id，与报价详情/统计一致；无 current_version_id 时才显式回退最新创建版本 |
| SALES-19 | 发票作废无红冲（需先删回款，审计链断） | P2 | 待修 | invoices/operations.py:141-142 | 2d | 静态已证 | 关联 PEER-05 |
| SALES-20 | 报价数量/单价无 0/负数校验 | P2 | 已验证 | sales/utils/quote_item_validation.py；quotes.py；quote_versions.py；quote_items.py；schemas/sales/quotes.py；QuoteItemsTable.jsx；tests/api/test_sales.py；QuoteCreateEdit.test.jsx | 0.5d | 静态已证；✅已动态复现并回归（2026-07-03） | 首版创建、版本创建、明细新增/更新均拒绝数量/单价 0 或负数；本地 data/app.db 发现 8 条历史空明细，价格无法无损推回，未自动改历史数据 |
| SALES-21 | 商机阶段词表两套不一致（ON_HOLD vs CLOSING） | P2 | 已验证 | sales/utils/stage_guard.py；sales/statistics_core.py；sales/statistics_reports.py；opportunity_batch.py；frontend OpportunityManagement/OpportunityDetail/SalesStatistics；migrations/20260703_sales_opportunity_stage_vocab_sqlite.sql | 0.5d | 静态已证；✅已动态复现并回归（2026-07-03） | 商机阶段写入口、统计桶、前端下拉/展示统一到 OpportunityStageEnum；旧 QUALIFIED/ON_HOLD 等存量值有清洗迁移 |
| SALES-22 | check_sales_data_permission 同文件重复定义 | P3 | 已验证 | core/sales_permissions.py；tests/unit/test_sales_scope_expansion.py | 0.25d | 静态已证；✅已动态复现并回归（2026-07-03） | 删除后置重复定义与重复导出，保留单一记录级权限入口；FINANCE_ONLY 对普通销售记录恢复拒绝，财务域仍走专用 finance scope |

### 二、售前域（PRE，24 项）

| ID | 功能/问题 | 等级 | 状态 | 证据位置 | 工作量 | 验证方式 | 备注/关联 |
|---|---|---|---|---|---|---|---|
| PRE-01 | 商机一键申请售前支持 request-presale-support | — | 已验证 | presale/tickets/crud.py:126-183 | — | 静态已证（正面确认） | 无缺陷 |
| PRE-02 | 售前工单主链路（接单→进度→交付物→完成→评分） | P2 | 重复-合并→PRE-14 | 见 PRE-14 | — | 静态已证 | 主链路本体可用，唯一缺陷即状态字典分裂（PRE-14），域内合并 |
| PRE-03 | 技术评估打分/否决/风险生成（evaluate） | — | 已验证 | — | — | 静态已证（正面确认） | 无缺陷 |
| PRE-04 | 立项关卡 PMO_REQUIRE_PRESALE_ASSESSMENT 可被"自动空评估"绕过 | P1 | 待修 | presale_assessment_completion.py:95-105；pmo_initiation/service.py:213-214,362-371 | 1.5d | 静态已证 | 详#1；关联 PROJ-01（关卡本体真拦截） |
| PRE-05 | 三档报价金额梯度倒挂（BASIC>STANDARD，DB 实证两例） | P1 | 待修 | presale_ai_quotation_service.py:117-169 | 1d | 静态已证 | 详#2 |
| PRE-06 | 三档报价静态回退项是"ERP软件"报价，领域错配 | P2 | 待修 | presale_ai_quotation_service.py:424-536 | 0.5d | 静态已证 | 详#3 |
| PRE-07 | update_quotation 税额/折扣不随明细重算 | P2 | 待修 | presale_ai_quotation_service.py:194-212 | 0.5d | 静态已证 | 详#4 |
| PRE-08 | ai-enrich-requirement 整行覆盖清空已有需求；mock 回退破坏性写入 | P1 | 待修 | opportunity_workflow.py:508-522；ai_client_service.py:256-257 | 1d | 静态已证 | 详#5；mock 集群（集群2）统一拦截点 |
| PRE-09 | ai-quote-estimate mock 回退静默返回垃圾 200 | P2 | 待修 | opportunity_workflow.py:358-363 | 0.5d | 静态已证 | 详#6；修复并入 PRE-08 |
| PRE-10 | AI 需求分析结果无下游消费（数据孤岛，北极星断点） | P1 | 已修待验 | presale/requirement_analysis_bridge.py；presale_ai_service.py；presale_ai_quotation_service.py；tests/unit/test_presale_requirement_bridge.py | 3d | 静态已证；✅契约测试回归（2026-07-03） | 详#8；方案生成/三档报价支持 requirement_analysis_id 自动带出；新增 POST /presale/ai/analysis/{id}/confirm 确认后增量回填商机需求（不覆盖人工值，extra_json 溯源） |
| PRE-11 | 方案生成 mock 方案可入库（confidence 0.8）+ BOM 成本硬编码 10000 元 | P1 | 待修 | presale_ai_service.py:193-242,492-504 | 2d | 静态已证 | 详#10；mock 集群 |
| PRE-12 | 方案导出 PDF 是纯文本桩、Word/Excel 为 pass 缺失 | P1 | 待修 | presale_ai_export_service.py:46-72；presale_ai_routes.py:257-268 | 2-3d | 静态已证 | 详#11；止损包（先提示假导出）；同域有真 reportlab 可复用 |
| PRE-13 | AI 使用报告 export-report 返回不存在的文件 URL | P2 | 待修 | presale_ai_integration.py:399-409 | 1d | 静态已证 | 详#12；止损包 |
| PRE-14 | 售前工单状态字典分裂（PROCESSING vs IN_PROGRESS / REVIEW 无路可走） | P2 | 待修 | presale/core.py:50-59；operations.py:146-149；crud.py:117,151 | 1d | 静态已证 | 详#14；数据清洗专项（存量 PROCESSING/REVIEW 工单迁移）；PRE-02 并入本项 |
| PRE-15 | 售前移动端整域假实现（AI问答/语音/拜访/估价/快照全硬编码，前端零消费） | P1 | 待修 | presale_mobile_service.py:69-78,166-170,214-543 | 下架0.5d/做实4-5d | 静态已证 | 详#13；止损包（僵尸路由下架） |
| PRE-16 | 知识库 _has_live_ai 漏判 qwen，AI 提取/问答永走规则模板 | P1 | 已验证 | presale_ai_knowledge_service.py:681-687 | 0.1d | 静态已证；✅已修复并回归（2026-07-03） | 详#15；Quick-win 闸门包；_has_live_ai 已纳入 qwen_api_key |
| PRE-17 | 知识库/模板"语义搜索"实为字符哈希/Jaccard，非语义 RAG | P2 | 待修 | presale_ai_knowledge_service.py:439-445,677-679 | 短期1d/中期3-5d | 静态已证 | 详#16；sentence-transformers 未安装；ROADMAP F4 |
| PRE-18 | 相似案例检索为 equipment_type 精确匹配 SQL，非语义 | P2 | 待修 | opportunity_workflow.py:170-175 | 并入 PRE-17 | 静态已证 | 详#16；空值互配、命中率低 |
| PRE-19 | 方案 AI 评审 ai-solution-review / 验收标准生成 | — | 已验证 | — | — | 静态已证（正面确认） | 无缺陷；ai-acceptance-criteria 真回填 |
| PRE-20 | AI 工作流编排只建状态壳无执行器（DB 中 20 行 status 全空） | P2 | 待修 | presale_ai_integration.py:285-319 | 做实3d/下架0.5d | 静态已证 | 详#17；止损包 |
| PRE-21 | AI 后台任务重启后 PENDING/RUNNING 永久卡死（无恢复无超时） | P2 | 已验证 | ai_job_service.py；main.py startup；tests/unit/test_ai_job_recovery.py | 0.5d | 静态已证；✅已动态回归（2026-07-03） | 详#18；**主项**：APPR-22① 同问题并入本项（互为引用）；startup recover_stale_jobs + 轮询惰性超时（AI_JOB_MAX_RUNTIME_SECONDS 默认1800s）；`import app.main` 路由加载成功 |
| PRE-22 | 模块库 ai-modules（挖掘/列表/标准化建议，DB 7 模块） | — | 已验证 | — | — | 静态已证（正面确认） | 无缺陷 |
| PRE-23 | 立项提交关卡异常静默放行（except 后 missing=[]） | P2 | 已验证 | pmo_initiation/service.py:363-371 | 0.25d | 静态已证；✅已修复并回归（2026-07-03） | 详#19；Quick-win 闸门包；handover 构建异常 now raises ValueError，不再静默提交 |
| PRE-24 | 遗留脏数据字典（quotation_type 非法枚举 / assessment_status 两套值报表漏 93%） | P3 | 待修 | presale_ai_quotation.quotation_type；opportunities.assessment_status（DB 实证 51 vs 4） | 0.5d | 静态已证 | 详#20；数据清洗专项 |

### 三、项目/PMO 域（PROJ，26 项）

| ID | 功能/问题 | 等级 | 状态 | 证据位置 | 工作量 | 验证方式 | 备注/关联 |
|---|---|---|---|---|---|---|---|
| PROJ-01 | 立项链路（草稿→提交→审批→建项目）+ 售前评估关卡 | — | 已验证 | pmo_initiation/service.py:358-371 | — | 静态已证（正面确认） | 无缺陷；但关卡可被空评估绕过见 PRE-04、异常静默放行见 PRE-23 |
| PROJ-02 | 立项审批未选 PM 则静默不建项目（APPROVED 但无项目无报错） | P2 | 待修 | pmo_initiation/service.py:415-425 | 0.5d | 静态已证 | 详#15 |
| PROJ-03 | 合同→立项字段带入偷懒：占位文本冒充需求（商机/售前路径可用） | P2 | 待修 | ContractManagement.jsx:363；ContractDetail.jsx:442 | 2-3d | 静态已证 | 详#17；北极星主项；关联 APPR-14（交付日期幽灵字段） |
| PROJ-04 | 项目状态机无转移守卫，可任意非法跳转（S1→S9 直跳） | P1 | 待修 | projects/status/status_crud.py:107-127,157-177 | 2d | 静态已证 | 详#3；superuser 无条件放行 stage_advance_service.py:73-75；先清洗 PROJ-05 脏数据 |
| PROJ-05 | 项目 status 三套词汇表并存，过滤逻辑实际失效 | P2 | 待修 | DB：COMPLETED45/EXECUTING35/ST01×24；project_scheduled_tasks.py:279；archive.py:54 | 2-3d | 静态已证 | 详#4；数据清洗专项 |
| PROJ-06 | 结项无强制门禁——未验收可直接结项（readiness 真校验未接线） | P0 | 已验证 | pmo/closure.py:80-155；closure_readiness_service.py | 1-2d | ✅已动态复现并回归（test_p0_08，2026-07-03） | 全局P0#8；Quick-win 闸门包；创建结项 now requires readiness.ready=True |
| PROJ-07 | 阶段门两条旁路：终验收直写 S9 绕回款门 + superuser 静默跳门 | P1 | 待修 | acceptance_completion_service.py:255-287；stage_advance_service.py:73-75 | 1-2d | 静态已证 | 详#14（详述定级 P2，总表定级 P1，从总表） |
| PROJ-08 | 任务进度→项目进度"加权汇总"实为简单平均，真加权函数死代码 | P2 | 待修 | progress_service.py:196-200 vs :439-532 | 1d | 静态已证 | 详#13；"算法真接线假"集群3；Quick-win 候补 |
| PROJ-09 | 甘特依赖不影响排期（仅画线+CPM 长度，无级联重排） | P1 | 待修 | gantt_dependency.py:107-118,399-418 | 4-6d | 静态已证 | 详#6 |
| PROJ-10 | 里程碑完成闸门被自身 except 吞掉，三条路径口径不一 | P1 | 已验证 | core/state_machine/milestone.py:91-118；endpoints/milestones.py:183-226 | 1-2d | 静态已证；✅已修复并回归（2026-07-03） | 详#5；Quick-win 闸门包；HTTPException 已重抛，全局 complete 端点已接 MilestoneStateMachine |
| PROJ-11 | 成本归集非实时（D2 确认）、退货不冲减、在制工单入账、日期归错月 | P1 | 待修 | cost/cost_collection_service.py:33,157,188,383 | 4-5d | 静态已证 | 详#11；数据清洗（project_costs 141 行中 60 行 cost_type 空）；时薪写死 200 |
| PROJ-12 | 工时填报→审批→撤回（统一引擎，模板已入库） | — | 已验证 | — | — | 静态已证（正面确认） | 无缺陷；附带 P3：工时提醒 REST 端点占位桩（详#22，timesheet_reminders.py:7-25），调度器仍 MemoryJobStore（F3） |
| PROJ-13 | 工时→人工成本联动不过滤审批状态；报表时薪写死 100 | P1 | 待修 | cost_overrun_analysis_service.py:338-350 | 1-2d | 静态已证 | 详#12；DB：DRAFT71/PENDING113 占 43% 被计入 |
| PROJ-14 | 预算超支只预警不拦截，预警链路"哑炮"（富版通知服务不在链路） | P1 | 待修 | cost_collection_service.py:108-116；budget_alert_service.py:716-777 未接 | 3-4d | 静态已证 | 详#10 |
| PROJ-15 | 预算/成本预警调度口径含计划成本（把 BOM 计划当实际，误报超支） | P2 | 待修 | project_scheduled_tasks.py:455-461 | 0.5d | 静态已证 | 详#21；套用 cost_basis.py:17 现成过滤器 |
| PROJ-16 | EVM 挣值：引擎真、PV/EV/AC 全手填（data_source=MANUAL，仅 3 行数据） | P1 | 待修 | evm.py:33-36,256 | 3-4d | 静态已证 | 详#7；北极星项 |
| PROJ-17 | 项目健康度主计算器（H1-H4）无成本维、无数据即绿 | P2 | 待修 | health_calculator.py:31-54 | 2d（与 PROJ-19 打包） | 静态已证 | 详#9 |
| PROJ-18 | 四维趋势健康度成本维恒满分（幽灵字段 + 枚举错位双 bug） | P1 | 待修 | health_trend_service.py:335,352；enums/others.py:245 | 0.5-1d | 静态已证 | 详#8 |
| PROJ-19 | 健康度快照维度字段写死 0（四分维写同一总值） | P2 | 待修 | project_scheduled_tasks.py:227-248 | 与 PROJ-17 打包 | 静态已证 | 详#9；DB：355 条快照 295 条全零 |
| PROJ-20 | 变更请求审批通过不回写项目基线（真联动引擎只绑 ECN） | P0 | 待修 | project_change_requests/service.py:193-242；project_change_impact_service.py:144-219 未接 | 3-5d | ✅已动态复现（test_p0_08） | 全局P0#8；三套变更实现互不联动（集群6） |
| PROJ-21 | 变更/立项审批通知均未实现（TODO/pass） | P2 | 已验证 | project_change_requests/service.py；tests/unit/test_project_change_notifications_proj21.py | 1-2d | 静态已证；✅已动态回归（2026-07-03） | 详#16；F3 扩围候补已收口；变更提交 now 通知项目 PM，审批结果 now 通知提交人，均走真实站内通知 |
| PROJ-22 | 验收全流程 + 报告生成（真 reportlab PDF） | — | 已验证 | acceptance/report_utils.py:75-208 | — | 静态已证（正面确认） | 无缺陷 |
| PROJ-23 | 验收通过后无售后/ITR 移交联动（售后需人工重建） | P2 | 待修 | acceptance 域 grep after_sales/itr 零命中；acceptance_service.py:171-172 | 2d | 静态已证 | 详#18；关联 AS-10（设备建档钩子即本项修复落点）/AS-12 |
| PROJ-24 | 项目复盘可用，但 AI 降级 mock 语义错配（预售文案进复盘） | P3 | 待修 | ai_client_service.py:406-422 | 1-2d | 静态已证 | 详#19；附带：change_impact_ai_service.py 653 行死代码无端点 |
| PROJ-25 | 交付风险 AI（ai_delivery，规则真算） | — | 已验证 | — | — | 静态已证（正面确认） | 无缺陷；但只认 EXECUTING，ST 码项目不进扫描（随 PROJ-05 清洗解决） |
| PROJ-26 | 团队组建未接入立项；经验维度写死 20 分 | P3 | 待修 | team_generation_service.py:234-235 | 1-2d | 静态已证 | 详#20 |

### 四、生产/供应链域（PROD，24 项）

| ID | 功能/问题 | 等级 | 状态 | 证据位置 | 工作量 | 验证方式 | 备注/关联 |
|---|---|---|---|---|---|---|---|
| PROD-01 | 现场调试 field_commissioning 假实现（签到/进度/问题/完工只回成功不写库） | P0 | 待修 | field_commissioning.py:16-31,36-111 | 6-8d | ✅已动态复现（test_p0_09） | 全局P0#9；**主项**：AS-01 同问题并入本项；孤儿表 field_tasks(8)/field_checkins(3) 数据清洗 |
| PROD-02 | 智能缺料预警扫描引用不存在字段，扫描端点必 500 | P0 | 已验证 | services/shortage/smart_alert_engine.py；tests/audit_p0/test_p0_07_shortage_scan_500.py；tests/unit/test_smart_alert_engine.py | 1-2d | ✅已动态复现并回归（test_p0_07，2026-07-03） | 全局P0#7；F1 扩围；扫描字段错配 500 已消除，预警/齐套算法口径仍归 PROD-05 |
| PROD-03 | 收货→库存断链（inbound_service 全仓零调用，current_stock 只减无增） | P0 | 已验证 | purchase/receipts.py；inventory/inbound_service.py；inventory/stock_update_service.py；tests/api/test_purchase_receipts_workflow_contracts.py；tests/audit_p0/test_p0_06_receipt_no_stock.py | 2-3d | ✅已动态复现并回归（test_p0_06，2026-07-03） | 全局P0#6；F1 扩围；质检合格增量入库，写 MaterialStock/MaterialTransaction 并同步 Material.current_stock |
| PROD-04 | 在途量计算全线死数据（读侧状态字典无任何写入点，在途恒 0） | P1 | 已验证 | services/purchase/in_transit.py；kit_rate_service.py；tests/api/test_purchase_receipts_workflow_contracts.py | 1.5d | 静态已证；✅已动态回归（2026-07-03） | F1 扩围；采购在途读侧统一为 PO 生效状态 + 订单行剩余数量；PROD-05 齐套算法口径仍待修 |
| PROD-05 | 齐套率口径错误（在途计入已齐套/双算/无跨项目预留，四套实现互异） | P1 | 待修 | kit_rate_service.py:105-117；kit_check/utils.py:99-105 | 3-4d | 静态已证 | F1 扩围；修 PROD-04 不修本项则齐套率立即虚高 |
| PROD-06 | BOM 版本管理假实现（bom_no unique 与版本模型矛盾，永远单版本） | P1 | 待修 | models/material.py:143；bom/bom_versions.py:34-39 | 3d | 静态已证 | RELEASED 后冻结无修订出口 |
| PROD-07 | ECN 审批通过不自动应用到 BOM（sync_to_bom 仅手工端点可调） | P1 | 待修 | ecn/integration/ecn_integration_service.py:32-103；ecn/state_machine.py:209-291 | 2d | 静态已证 | "分析真、执行手工"（集群3） |
| PROD-08 | 工单不关联/不快照 BOM（无 bom_id 字段，WorkOrderBom 零业务读写） | P1 | 待修 | models/production/work_order.py:21-96 | 4d | ✅已动态复现（test_p0_12） | 全局P0#12（汇总定 P0，域内总表 P1）；**主项**：APPR-05 并入本项 |
| PROD-09 | ECN 状态机可跳步（SUBMITTED→APPROVED）且通用转换接口无权限 | P1 | 待修 | ecn/state_machine.py:27-63,369-373,542-547 | 1.5d | 静态已证 | 对比专用审批端点有权限（ecn/approval.py:134） |
| PROD-10 | 采购申请→订单转换绕审批、可重复生成、不回写 ordered_qty | P1 | 待修 | purchase/purchase_service.py:226-264 | 1.5d | 静态已证 | 对比 BOM 路径实现完整 |
| PROD-11 | 收货后 PO/POI 状态永不流转（PARTIAL_RECEIVED/RECEIVED 无写入点） | P1 | 已验证 | purchase/receipts.py；tests/api/test_purchase_receipts_workflow_contracts.py | 1d | 静态已证；✅已动态回归（2026-07-03） | F1 扩围；收货后刷新 PO/POI 到 PARTIAL_RECEIVED/RECEIVED，并累计订单已收金额 |
| PROD-12 | 生产领料不扣库存、无创建入口（前端调用必 404；OutboundService 真实现零调用） | P1 | 已验证 | production/material_requisitions.py；inventory/outbound_service.py；tests/api/test_production_compat_endpoints.py | 3d | 静态已证；✅已动态回归（2026-07-03） | F1 扩围；新增领料创建入口，审批后发料扣减库存并写 ISSUE 流水 |
| PROD-13 | 报工审批装饰性（未审批即回写产量，驳回不回滚） | P1 | 待修 | production/work_reports.py:257-280,384-420 | 2d | 静态已证 | Quick-win 闸门包（数量回写移到审批后） |
| PROD-14 | 物料调拨假实现（ProjectMaterial NameError 被吞、执行不动库存） | P1 | 已验证 | shortage/handling/transfers.py；inventory/transfer_service.py；material_transfer_service.py；tests/api/test_shortage_transfers.py | 2d | 静态已证；✅已动态回归（2026-07-03） | F1 扩围；调拨执行 now 源库扣减、目标库增加，并写 ISSUE/TRANSFER_IN 流水 |
| PROD-15 | 现场缺料→紧急采购断链（只建 DRAFT 申请即止，替代/调拨方案 return []） | P1 | 待修 | shortage/handling/reports.py:235-258；urgent_purchase_from_shortage_service.py:184-244 | 3-4d | 静态已证 | 关联 PROD-02/APPR-04 |
| PROD-16 | 发货单无明细行、无齐套/质检门禁、不联动项目状态 | P1 | 待修 | models/business_support/delivery.py:23-102；delivery_orders/crud.py:142-209,326-388 | 5-7d | 静态已证 | 北极星项（手填总额）；关联 AS-10（发货→设备档案断链） |
| PROD-17 | AI 智能排程/优化纯模板填充（工期系数/节省天数/复用率全写死） | P1 | 待修 | schedule_generation_service.py:113-119,330；schedule_optimization_service.py:110-163,230-283 | 标注0.5d/做实5-8d | 静态已证 | 止损包 |
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
| AS-04 | 工程师派工冲突检测空转（依赖表不存在静默返回 0 冲突，assign 零校验） | P0 | 待修 | engineer_scheduling_service.py:41-47,205-368；installation_dispatch/workflow.py:62-78 | 4d | ✅已动态复现（test_p0_14） | 全局P0#14；集群3（算法真接线假） |
| AS-05 | 服务工单状态机无转移矩阵：未派工可直接关单 | P1 | 待修 | service/tickets/status.py:76-88,121-122 | 1.5d | 静态已证 | 集群1（通用 PUT 击穿状态机）；数据清洗专项（89 条工单 48 条枚举外脏值） |
| AS-06 | SLA 计时真、超时预警/升级从不运行（零调度 + 策略 is_active 全 NULL） | P1 | 已验证 | sla_service.py；scheduled_tasks/alert_tasks.py；scheduler_config/alerting.py；tests/unit/test_sla_as06.py | 2.5d | 静态已证；✅已动态回归（2026-07-03） | F3 扩围；历史 `is_active NULL` 策略按启用兼容，新增 `check_sla_warnings` 调度同步未关闭工单 SLA monitor 并生成去重 AlertRecord |
| AS-07 | 项目级售后模块 create-only、前端只读、与服务工单双轨割裂 | P1 | 待修 | after_sales.py 全文（364 行 12 端点无 PUT）；AfterSalesCenter.jsx:38-42 | 3d | 静态已证 | 集群6 |
| AS-08 | 备件管理假实现：无领用扣减、无库存联动、parts_cost 是 String | P1 | 待修 | after_sales.py:237-251；models/after_sales.py:159-188,218 | 4d | 静态已证 | — |
| AS-09 | 六张售后表在运行库不存在，质保/备件/满意度等端点即调即 500 | P1 | 待修 | after_sales.py:26-33,214-346（sqlite3 证实表缺失） | 1-2d | 静态已证 | — |
| AS-10 | 无客户侧设备档案（Machine 无 SN/客户/保修字段），验收/发货不建档 | P1 | 待修 | project/core.py:458-508；PRAGMA 验证 | 4d | ✅已动态复现（test_p0_13，设计级） | 全局P0#13（汇总定 P0）；**主项**：APPR-06 并入本项；关联 PROJ-23/PROD-16；数据清洗（machines ship_date 全空） |
| AS-11 | 售后工单无设备外键；机台"服务历史"坏连接恒空（String vs Integer） | P1 | 待修 | machine_custom/service.py:349；service_tickets 无 machine 字段（PRAGMA） | 3d | 静态已证 | 全局P0#13 同包；与 AS-10 打包修 |
| AS-12 | 售后→ECN/质量闭环完全缺失；ITR 自我导入占位（925 行死代码） | P1 | 待修 | itr.py:9,20-25；全仓无售后创建 ECN/Issue | 4d | 静态已证 | 关联 PROJ-23 |
| AS-13 | 客户360 四页签绑定不存在字段恒空；售后工单不入 360 | P1 | 待修 | customer_360_service.py:102-112 vs Customer360.jsx:179-239 | 3d | 静态已证 | — |
| AS-14 | 维保计划周期调度 pass 桩 + 幽灵表，生成靠手动、验收不联动 | P1 | 修复中 | stub_tasks.py:113-119；scheduler_config/production.py:59-68 | 3d | 静态已证；调度止血已回归（2026-07-03） | 调度项已默认禁用并统一 not_implemented；真实维保计划生成仍待做，随 APPR-04 回填 |
| AS-15 | 短信渠道假发送（日志即 success），阿里云真实现是死代码 | P1 | 已验证 | notification/channels/sms_handler.py；tests/audit_p0/test_p0_11_notification_fake_success.py；tests/unit/test_notification_channels_sms.py | 1d | 静态已证；✅已动态回归（2026-07-03） | 全局P0#11；短信通道缺网关配置/SDK/网关成功响应时返回失败，不再 logger 即 success；APPR-17 预警积压另修 |
| AS-16 | Header 铃铛纯装饰（无 onClick、红点无条件渲染、badge 写死 5） | P1 | 待修 | Header.jsx:119-129；sidebarConfig/default.js:17 | 0.5d | 静态已证 | Quick-win 闸门包；通知中心本体是真实现 |
| AS-17 | 工程师调度前端 4 接口后端不存在必 404；模块请求时现场 DDL 建表 | P1 | 待修 | engineerScheduling.js:7,19,33,38；engineer_scheduling.py:44 | 2d | 静态已证 | 关联 AS-04 |
| AS-18 | 售后现场服务记录孤立记事本（is_warranty 写死、无流转、不建派工单、表不存在） | P1 | 待修 | after_sales.py:267（表缺失见 AS-09） | 3d | 静态已证 | 建议改生成 InstallationDispatchOrder |
| AS-19 | 客服工作台"关闭工单"按钮必 422（payload 字段名错）；质保页签恒空 | P1 | 已验证 | CustomerServiceDashboard.jsx；CustomerServiceDashboard/utils.js；schemas/service.py:56-63 | 0.5d | 静态已证；✅已修复并回归（2026-07-03） | Quick-win 闸门包；close payload now uses solution，后端兼容 resolution，质保页签用真实质保类工单兜底；AS-09 售后质保表缺失仍待修 |
| AS-20 | 保修在保/过保判断缺失，无过保收费（ProjectWarranty 自述未启用） | P2 | 待修 | project/extensions.py:145-202；after_sales.py:227 | 2.5d | 静态已证 | — |
| AS-21 | 关单不触发回访；调查"发送"不触达、前端 submit 接口 404；评分员工代填 | P2 | 待修 | surveys.py:250-277；services/api/service.js:236；status.py:128,145-164 | 3d | 静态已证 | — |
| AS-22 | 故障诊断 AI 真调 LLM 但零上下文（历史工单/知识库未注入）；降级语义错位 | P2 | 待修 | ai_engineering.py:78-89 | 2.5d | 静态已证 | — |
| AS-23 | 售后事件通知产生端缺失：12 端点零通知；派工 CC 直写 notified_at 造假 | P2 | 已验证 | after_sales.py；service/tickets/assignment.py；service/tickets/crud.py；service/tickets/status.py；service_ticket_notifications.py；tests/unit/test_service_ticket_notifications_as23.py | 1d | 静态已证；✅已动态回归（2026-07-03） | F3 扩围；集群4（假成功）；服务工单创建/派工/状态变更/关闭已发真实站内通知，CC `notified_at` 改为发送成功后写；`after_sales.py` 反馈/保养/support ticket/质保/备件/现场服务/满意度/知识库/升级写端已通知项目 PM/创建人 |
| AS-24 | 双轨派工占用账不同步；派工完工工时不生成 Timesheet（外勤成本消失） | P2 | 待修 | state_machine/installation_dispatch.py:105-106,190 | 4d | 静态已证 | 集群6 |
| AS-25 | 订阅默认接收人 TODO 返回空（双 resolver 口径不一）；webhook 仅企微 | P2 | 已验证 | alert_subscription_service.py；notification_utils.py；notification_service.py；channels/webhook_handler.py；tests/unit/test_notification_utils_as25.py | 2.5d | 静态已证；✅已动态回归（2026-07-03） | F3 扩围；默认接收人 now 取处理人/项目 PM 等业务负责人；旧 `app.services.notification_utils`/`notification_service` 路径恢复；Webhook 支持 `WEBHOOK_URL` 并兼容企微 URL |

### 六、审批引擎/状态机/跨域（APPR，22 项）

| ID | 功能/问题 | 等级 | 状态 | 证据位置 | 工作量 | 验证方式 | 备注/关联 |
|---|---|---|---|---|---|---|---|
| APPR-01 | 采购/外协/验收/立项 4 条审批链 template_code 与 DB 错位，提交必失败且 HTTP 200 掩盖 | P0 | 已验证 | purchase_workflow/service.py；outsourcing_workflow_service.py；acceptance_approval/service.py；projects/approvals/submit_new.py；api/v1/endpoints/approval_submit_guard.py；tests/audit_p0/test_p0_01_approval_template_mismatch.py | 1.5d | ✅已动态复现并回归（test_p0_01，2026-07-03） | 全局P0#1；审批链救活包；4 条业务链统一到 `TPL_*` 模板 code，全失败提交回滚并返回 400 |
| APPR-02 | 审批模板无任何种子/迁移，新环境全部审批不可用（F1/ECN1 根因） | P0 | 已验证 | scripts/init_db.py；app/utils/init_approval_data.py；app/utils/init_data.py；tests/audit_p0/test_p0_02_approval_template_no_seed.py | 1d | ✅已动态复现并回归（test_p0_02，2026-07-03） | 全局P0#2；审批链救活包；新库幂等种子 10 模板+13 flow+30 节点+3 路由规则 |
| APPR-03 | 会签/或签驳回语义破坏：REJECTED 实例可被翻转回 APPROVED | P0 | 已验证 | services/approval_engine/engine/approve.py；services/approval_engine/engine/core.py；tests/audit_p0/test_p0_05_cosign_reject_flip.py | 2d | ✅已动态复现并回归（test_p0_05，2026-07-03） | 全局P0#5；审批链救活包；AND_SIGN 汇总失败保持 REJECTED，OR_SIGN 拒绝后等待其他审批人，终态实例禁止 pending 任务复活 |
| APPR-04 | 14/56 定时任务 stub 假实现且监控记成功（含缺料预警 3 件套） | P0 | 修复中 | scheduled_tasks/stub_tasks.py:13-28；scheduler.py:107 | 0.5d标记+3-5d回填 | ✅已动态复现（test_p0_10）；✅止血已回归（test_p0_10 + stub/scheduler 单测，2026-07-03） | 全局P0#10；F3 扩围；已完成 stub 标记/not_implemented、失败计数、stub-backed 任务禁用；缺料/维保等真实实现仍待回填 |
| APPR-05 | BOM→生产工单断链，WorkOrderBom 中间表零业务读写 | P0 | 重复-合并→PROD-08 | models/shortage/requirements.py:25；bom/bom_release.py:105-118 | — | 静态已证 | 与 PROD-08 同一结构性断链（全局P0#12），保留 PROD-08 为主项 |
| APPR-06 | 售后无设备档案表，机台级溯源断链（machine_no 手填文本） | P0 | 重复-合并→AS-10 | delivery_orders/crud.py:326-390；service/records.py:260 | — | 静态已证 | 与 AS-10 同一结构性缺失（全局P0#13），保留 AS-10 为主项 |
| APPR-07 | 撤回审批 TypeError：合同/验收/报价/ECN 4 域传错参数名（CONFIRMED），撤回必 500 | P1 | 已验证 | contract_approval/service.py:399；acceptance_approval/service.py:360；quote_approval_service.py:378；ecn/approval/service.py:394 | 0.5d | ✅已动态复现（test_p0_17）；✅已修复并回归（2026-07-03） | 全局P0#17（汇总定 P0，域内总表 P1）；**主项**：PEER-03 并入本项；4 域均改为 initiator_id 并传 comment=reason |
| APPR-08 | 加签（前/后加签）假实现：加签人永收不到可办任务或原审批人被跳过 | P1 | 待修 | engine/approve.py:347,356-357；executor.py:163-165,329-354 | 2d | 静态已证 | — |
| APPR-09 | 审批超时机制（REMIND/AUTO_PASS/AUTO_REJECT/ESCALATE）零调度死代码 | P1 | 待修 | executor.py:392-435 全仓零调用 | 2d | 静态已证 | 集群3 |
| APPR-10 | 发票开票门禁读旧轨空表（查不到即放行）——未审批可开票 | P1 | 已验证 | sales/invoices/operations.py；services/approval_engine/adapters/invoice.py；tests/api/test_sales_invoice_gate_contracts.py；tests/audit_p0/test_p0_16_invoice_gate.py | 1d | 静态已证；✅已动态回归（2026-07-03） | 全局P0#16（汇总定 P0）；资金急救包；开票前要求发票状态与统一审批实例均为 APPROVED |
| APPR-11 | update_invoice 任意改金额/状态：绕 F3 上限、绕审批与状态机 | P1 | 已验证 | sales/invoices/basic.py；models/sales/invoices.py；tests/api/test_sales_invoice_gate_contracts.py | 1d | 静态已证；✅已动态回归（2026-07-03） | 全局P0#16；资金急救包；**主项**：PEER-04 并入本项；update 禁止改 status，并重跑合同累计开票上限 |
| APPR-12 | 合同审批三轨并存，旧轨 /contracts/enhanced/* 可绕统一引擎自审自过 | P1 | 待修 | sales/contracts/enhanced.py:163-230；sales/contract/approval_service.py:45-98,193-201 | 1.5d | 静态已证 | 集群6；F2 前置 |
| APPR-13 | 合同无中央状态机：15+ 直接赋值点、大小写两套状态值库中混存 | P1 | 待修 | status_service.py:59-104；data_sync_service.py:180；DB：ACTIVE18/SIGNED67/draft12/executing13 | 2-3d | 静态已证 | 集群1/集群5；数据清洗专项；关联 PEER-01/PEER-02（具体绕过点） |
| APPR-14 | 合同→项目交付日期幽灵字段 delivery_deadline，自动立项项目全部无计划完工日期 | P1 | 待修 | status_handlers/contract_handler.py:229 | 0.5-1d | 静态已证 | 关联 PROJ-03（合同→立项带出） |
| APPR-15 | 发货款（默认 40%）回款计划无任何触发器，最大回款节点靠人工盯 | P1 | 待修 | payment_plan_service.py:99-103,341-346 | 1-2d | 静态已证 | 资金急救包 |
| APPR-16 | ECN 超期检查 job 模块路径错误，注册失败被静默吞掉 | P1 | 已验证 | scheduler_config/other.py；tests/unit/test_scheduler_utils.py | 0.5d | 静态已证；✅已动态回归（2026-07-03） | F3 扩围；check_ecn_overdue 模块路径改为 `app.services.ecn.ecn_scheduler`，resolver 契约锁定可导入 |
| APPR-17 | 预警通知永不流转状态：841 条 PENDING 积压 4 个月饿死 | P1 | 已验证 | alert_tasks.py；tests/audit_p0/test_p0_11_notification_fake_success.py | 1-1.5d | 静态已证；✅已动态回归（2026-07-03） | 全局P0#11；F3 扩围；worker 导入断裂已随 AS-03 修复；通知尝试后 AlertRecord `PENDING→OPEN`，扫描改最老优先；历史 841 条未直接改库，需随调度/运维逐批处置 |
| APPR-18 | 报价明细不复制为合同交付物，G4 门禁逼人工重录 | P1 | 待修 | contracts/basic.py:475-488；utils/gate_validation.py:228-244 | 1d | 静态已证 | 北极星项；SALES-12 附注以本项为主 |
| APPR-19 | 大额审批路由规则挂孤儿模板：≥50 万报价不再经总经理 | P2 | 待修 | router.py:26-61；quote_approval_service.py:79 | 1d | 静态已证 | 附带 _advance_to_next_node 丢 entity_data（engine/core.py:174-180） |
| APPR-20 | legacy 兼容端点创建的审批实例无节点无任务，永久 PENDING | P2 | 待修 | approvals/legacy_compat.py:27-70,86-112 | 0.5d | 静态已证 | 数据清洗（entity_type 空实例 3 条） |
| APPR-21 | 角色型 SINGLE 节点审批人取"全库第一个"，与业务上下文无关 | P2 | 待修 | executor.py:50-57；router.py:267-294 | 1.5d | 静态已证 | 上下文有 project_id 未用 |
| APPR-22 | 后台机制综合：①AI job 无重启恢复 ②备份 4 个月未自动执行 ③禁用任务重启复活 ④第二调度器不进监控 ⑤调度器 except ImportError 全静默 | P2 | 修复中 | scheduler.py；main.py startup；backup_service.py；scheduled_tasks/backup_tasks.py；scheduler_config/other.py；tests/unit/test_ai_job_recovery.py；tests/unit/test_scheduler_utils.py；tests/unit/test_backup_scheduler_appr22.py | 0.5d起（分项） | 静态已证；✅子项①/②/③/⑤已动态回归（2026-07-03） | F3 扩围；**①与 PRE-21 重复并已验证**；②已修：新增 enabled `daily_database_backup`，SQLite 环境直接生成压缩 SQL dump+md5；③已修：DB `is_enabled=false` 不再重启复活；⑤已修：任务解析/注册失败写入 scheduler failure metrics，`main.py` scheduler 整体导入失败记录错误日志；④第二调度器监控仍待做 |

### 七、并行会话补充：合同+发票状态流（PEER，5 项）

| ID | 功能/问题 | 等级 | 状态 | 证据位置 | 工作量 | 验证方式 | 备注/关联 |
|---|---|---|---|---|---|---|---|
| PEER-01 | 已取消（CANCELLED）合同可经通用 PUT 改回 SIGNED，绕过签署校验 | P1 | 待修 | contracts/basic.py:63,539,570-571 | 0.5-1d（status 剔出 field_map） | 静态已证 | 候选 P0；集群1；关联 APPR-13（状态机收口后一并消除） |
| PEER-02 | 审批中合同可被通用 update 改状态，与 ApprovalInstance 脱钩 | P1 | 待修 | contracts/basic.py:539（不检查 PENDING 实例） | 并入 PEER-01 修复 | 静态已证 | 集群1；关联 APPR-13 |
| PEER-03 | 合同审批撤回必 500 / 状态永卡 PENDING_APPROVAL（user_id 参数名错） | P1 | 重复-合并→APPR-07 | contract_approval/service.py:399；engine/actions.py:73-77 | — | 静态已证（主会话 CONFIRMED） | 与 APPR-07 同一缺陷，APPR-07 覆盖 4 域为主项 |
| PEER-04 | 作废发票可经 update_invoice 改回 ISSUED/PAID，金额随意改 | P1 | 重复-合并→APPR-11 | invoices/basic.py:302,334-338 | — | 静态已证 | 与 APPR-11 同一端点同一根因，保留 APPR-11 为主项 |
| PEER-05 | 作废发票可被 /issue 重新开票（只查审批记录不校验当前 status） | P1 | 已验证 | sales/invoices/operations.py；tests/api/test_sales_invoice_gate_contracts.py | 0.5d | 静态已证；✅已动态回归（2026-07-03） | 候选 P0；资金急救包；作废/取消等非 APPROVED 当前状态不能重新开票 |

---

## 主表（第二轮：平台/支撑/边缘域）

> 第二轮覆盖 HR / 权限(PERM) / 平台运维(ADMIN) / 多租户(TEN) / 报表(RPT) / 边缘业务(MISC) 六域，来源为 audit2/ 下 6 份原始报告（hr.md/perm.md/admin.md/tenant_report.md/misc.md）。列结构、状态字典、验证方式口径与第一轮主表一致；等级列将 PERM 报告的"高/中/低"归一为 P1/P2/P3。二轮 P0 项验证方式仅"静态已证"（本轮未做动态复现，动态复现见第一轮 17 项）。

### 七、人力资源/组织域（HR，25 项）

| ID | 功能/问题 | 等级 | 状态 | 证据位置 | 工作量 | 验证方式 | 备注/关联 |
|---|---|---|---|---|---|---|---|
| HR-01 | 员工 Excel 导入端点必崩（运行时 import 不存在的 validate_excel_file） | P1 | 待修 | organization/employee_import.py:41-46 | 0.1d(Quick-win) | 静态已证 | 前端 useEmployeeProfileList.js:106 直连坏端点；193 名员工只能手工录入 |
| HR-02 | 离职处理仅置状态位，无交接不停账号（不联动 User.is_active） | P1 | 待修 | hr_management/transactions.py:175-179 | 3-4d | 静态已证 | 离职员工账号仍可登录 |
| HR-03 | 数据权限绑部门名字符串，组织变动不随动 | P1 | 待修 | data_scope/generic_filter.py:121-135 | 2-3d+清洗0.5d | 静态已证 | 关联 PERM-15/17；调岗员工永远看旧部门数据 |
| HR-04 | 部门/员工删除前端调不存在端点（405/404） | P2 | 待修 | services/api/hr.js:19；organization 目录无 delete | 1d | 静态已证 | — |
| HR-05 | 员工-部门无外键、双主数据字符串关联（同义词并存） | P2 | 待修 | organization.py:76 department=String(50) | 2-3d | 静态已证 | 数据清洗专项 |
| HR-06 | 考勤统计是取模公式伪造（迟到人数由序号取模决定） | P1 | 待修 | admin_attendance.py:4-7,81-84 | 止损0.5d/做实8-10d | 静态已证 | 前端 AttendanceManagement.jsx 真渲染；伪造管理数据比缺失更危险 |
| HR-07 | 打卡不落库、"我的考勤"硬编码 | P1 | 待修 | admin_attendance.py:194-198,153-170 | 并入 HR-06 | 静态已证 | 孤儿表 field_checkins(3) 代码零命中 |
| HR-08 | 请假缺失、加班僵尸模型、补卡缺失 | P1 | 待修 | timesheet.py:265-268；AttendanceManagement.jsx:38,310 | 5-8d/摘Tab0.5d | 静态已证 | 请假缺失致排产无输入 |
| HR-09 | 节假日双轨、DB 模型零消费（真消费的是硬编码字典） | P3 | 待修 | holiday.py:20；holiday_utils.py:13 | 1d | 静态已证 | DB 33 行真数据零消费 |
| HR-10 | 工程师五维绩效：算得出存不下读全空（PerformanceResult 零写入） | P0 | 待修 | result_evaluation.py:24；performance_calculator.py:50；engineer_performance_service.py:168 | 3-4d | 静态已证 | 域内最重；连锁击穿奖金 HR-16 |
| HR-11 | 绩效评分维度写死常量（五维至少两维对全岗恒定） | P1 | 待修 | performance_calculator.py:108,111,187-188 | 3-5d(与HR-10打包) | 静态已证 | collector 与 calculator 互不调用 |
| HR-12 | 绩效采集器与算分器双轨不联通（空数据回落 75） | P2 | 待修 | aggregator.py:33；data_sync.py:171-184 | 并入 HR-11 | 静态已证 | — |
| HR-13 | 绩效申诉缺失（模型完整但零写入无端点） | P2 | 待修 | appeal_adjustment.py:13 | 2d | 静态已证 | 挂审批引擎 |
| HR-14 | 三套绩效体系并行隔绝、服务大面积复制粘贴 | P2 | 待修 | evaluation.py:76,127；calculation.py:20 | 3d | 静态已证 | 谁是正式绩效说不清 |
| HR-15 | 绩效合同绕 ORM 用裸 sqlite3（连接串写死） | P2 | 待修 | performance/contract.py:11,28,35 | 2-3d | 静态已证 | **主项**：MISC-12 同一 performance_contract 裸 sqlite3，MISC-12 标重复-合并→HR-15 |
| HR-16 | 绩效→奖金串联空转（北极星断链，从未算出一分钱奖金） | P1 | 待修 | bonus/calculation.py:73；services/bonus/performance.py:42-46 | 0d(依赖HR-10)+0.5d | 静态已证 | 依赖 HR-10 疏通 |
| HR-17 | 奖金审批无权限无引擎，可自审可绕过（Excel 导入直 APPROVED） | P1 | 待修 | sales_calc.py:271-297；bonus_distribution_service.py:106 | 2-3d | 静态已证 | 同 SALES-01 性质；bonus payment 端点已补 bonus:read/distribute/pay/manage（2026-07-03），审批主链路仍待修 |
| HR-18 | 团队奖金分配无"合计=100%/总额"校验 | P2 | 待修 | bonus_allocation_parser.py:239-276 | 0.5d | 静态已证 | Excel 可把 1 万分出 3 万 |
| HR-19 | 奖金系数硬编码非规则驱动（等级/角色/售前系数全写死） | P2 | 待修 | services/bonus/base.py:96-125；presale.py:60-73 | 1-2d | 静态已证 | 规则表 DB 仅 3 行假种子 |
| HR-20 | 时薪费率体系：本体真实，旁路 14 处写死 | P1 | 待修 | hourly_rate_service.py:30-157；labor_cost_detail.py:15；sales/cost/cost_calculator.py:28 等 | 2-3d | 静态已证 | 更正 PROJ-13：时薪写死已部分修复（cost_overrun_analysis_service.py:338-350 已走费率服务），仅剩不过滤审批状态 |
| HR-21 | 费率兜底口径混乱（全级 miss 静默返 100）、变更无留痕 | P2 | 待修 | hourly_rate_service.py:28,50,157；crud.py:187-194 | 兜底0.5d/版本化1-2d | 静态已证 | 与 PROJ-11/PROJ-13、RPT-03 同"时薪多口径"病灶互引 |
| HR-22 | 文化墙：配置端点坏 shim、无审核、前端 405 | P2 | 待修 | culture_wall_config.py:9-25；contents.py:115,122,85 | 2-3d | 静态已证 | **主项**：与 MISC-23 同一 culture_wall，互引不合并（MISC-23 补 config/goals/PUT 细节） |
| HR-23 | 冲突调解：真算法架在无写入者的空表上（resource_conflicts 零写入） | P2 | 待修 | conflict_mediation_service.py:60-461；analytics/resource_conflicts.py:89-143 | 检测落库1d/收敛2-3d | 静态已证 | 与 MISC-02、AS-24 同 resource_conflicts 空表/双轨病灶互引 |
| HR-24 | 协作评价自动补齐默认分污染（缺评一键填 3 分/75 分无标记） | P3 | 待修 | ratings.py:196-230 | 0.5d | 静态已证 | 本域少数真闭环 |
| HR-25 | HR 域数据被通用填充脚本污染（假数据掩盖 HR-10 零写入断链） | P3 | 待修 | DB：hr_project_performance 70 行评分全 NULL；monthly_work_summary 含 task4_demo_seed | 0.5d | 静态已证 | 数据清洗专项 |

**HR 域小结**：骨架真、血肉假、串联断——用户/部门/时薪/奖金链路/协作评价 CRUD 骨架可用；考勤域是演示壳（HR-06/07/08）、工程师绩效"算得出存不下读全空"（HR-10）；绩效→奖金空转、组织变动→数据权限不随动、员工导入入口必崩。DB 侧 HR 域无任何真实业务数据流过。核心约 25-35 人天。

### 八、权限/认证域（PERM，23 项）

| ID | 功能/问题 | 等级 | 状态 | 证据位置 | 工作量 | 验证方式 | 备注/关联 |
|---|---|---|---|---|---|---|---|
| PERM-01 | JWT 签发/过期/签名/类型校验 | — | 已验证 | auth.py（真校验） | — | 静态已证（正面确认） | 无缺陷 |
| PERM-02 | Refresh Token 刷新+旋转（校验会话+黑名单旧 token） | — | 已验证 | auth.py | — | 静态已证（正面确认） | 无缺陷 |
| PERM-03 | Token 撤销黑名单无 Redis 降级（多 worker/重启即失效） | P1 | 待修 | auth.py:324-352,38 | 1-2d | 静态已证 | .env.local 未设 REDIS_URL；三系统性根因① |
| PERM-04 | 账号锁定 core 内存版是死代码（全仓无 import） | P2 | 待修 | account lockout core 版 | 0.5d | 静态已证 | 真正登录走 Service 版 |
| PERM-05 | 账号锁定 Service 版 DB 降级（阈值真生效） | P2 | 已验证 | AccountLockoutService | — | 静态已证（正面确认） | 无 Redis 走 DB 窗口统计 |
| PERM-06 | 账号解锁 API 缺失（account_unlock.py 占位桩） | P1 | 待修 | account_unlock.py:7-26；unlock_account:346-370 无调用方 | 1-2d | 静态已证 | 被锁账号无 Redis 环境只能等窗口或改库 |
| PERM-07 | 审计日志写入：用户/角色/权限有留痕，业务操作大面积无 | P2 | 待修 | sales_operation_logs 表不存在 | 2-3d | 静态已证 | — |
| PERM-08 | 审计日志查询 API 缺失（audits.py 占位桩） | P2 | 待修 | audits.py 占位 | 1d | 静态已证 | 审计写而不可查 |
| PERM-09 | RBAC 角色继承递归 CTE（SQL 支持但 DB 0 角色有 parent） | P3 | 已验证 | 递归 CTE | — | 静态已证（正面确认） | 数据未用，机制真 |
| PERM-10 | require_permission 装饰器机制（双模式实现正确） | — | 已验证 | require_permission | — | 静态已证（正面确认） | 无缺陷 |
| PERM-11 | require_permission 覆盖率仅 34%，125 个 NONE 端点裸奔 | P1 | 修复中 | AST 重扫 2883 路由：PERMISSION 980/AUTH_ONLY 1778/NONE 125 | 3-5d | 静态已证；组织员工/HR 档案小切口已回归（2026-07-03） | 已补 organization/employees 与 organization/hr_profiles 的 hr:* 权限；其余 NONE 端点仍待系统性收口 |
| PERM-12 | is_active=0 权限码静默过滤（禁用即从所有用户消失无告警） | P2 | 待修 | permission_engine.py:67 | 0.5d | 静态已证 | DB 现有 11 个 inactive 码（全 SALES） |
| PERM-13 | 权限缓存进程隔离+反查断链（改权限不重启不全生效） | P1 | 待修 | CacheService；role_management/service.py:1108 | 2d | 静态已证 | set_role_user_ids 全仓无调用→反查恒空，等 10min TTL |
| PERM-14 | :read/:view 别名在鉴权路径未生效（精确串匹配） | P2 | 待修 | auth.py:732-763 | 1d | 静态已证 | DB 5 个:view 码与 127 个:read 码并存 |
| PERM-15 | 数据权限 ALL/DEPT/OWN 过滤大量静默降级；CUSTOMER 恒 True | P1 | 待修 | generic_filter.py:218-221 | 3-5d | 静态已证 | 关联 HR-03；三系统性根因② |
| PERM-16 | RoleDataScope 配置层坏死（无 API、DB 垃圾种子 is_active 全 NULL） | P1 | 待修 | RoleDataScope 模型无 API；get_user_data_scopes 死代码 | 3-5d | 静态已证 | 实际生效的是 roles.data_scope 单字段 |
| PERM-17 | 数据权限挂载率：制造/供应链/财务全域 0 行级过滤 | P1 | 待修 | production(0/32)/procurement/bom/ecn/inventory/budget/cost/finance_reports/timesheet | 与 15/16 打包 | 静态已证 | acceptance(1/21)/presale(1/20) 近零 |
| PERM-18 | 超级管理员判定（is_superuser+tenant_id IS NULL 统一） | P2 | 已验证 | — | — | 静态已证（正面确认） | 库中有异常超管数据待清洗 |
| PERM-19 | 角色删除后残留会话（删角色不失效在线会话，靠 TTL 过期） | P2 | 待修 | 缓存 TTL | 1d | 静态已证 | 关联 PERM-13 |
| PERM-20 | 密码修改/重置流程（改密撤销当前 token；重置不撤销目标会话） | P3 | 待修 | 改密/重置 | 0.5d | 静态已证 | — |
| PERM-21 | 全局认证中间件默认拒绝（白名单外强制 Bearer；可 env 一键关闭） | P2 | 已验证 | 中间件 | — | 静态已证（正面确认） | 可被 env 一键关闭为隐患 |
| PERM-22 | 前端路由/菜单/按钮权限：system/hr/finance 路由零守卫 | P2 | 待修 | 前端路由；401 回落 mock | 1-2d | 静态已证 | mock 掩盖越权 |
| PERM-23 | PERMISSION_COVERAGE_AUDIT.json 过时（数字与本轮接近） | P3 | 待修 | 6/21 生成 | 0.1d | 静态已证 | 建议重新生成 |

**PERM 域小结**：三个系统性根因——①Redis 未配=三项安全机制降级（PERM-03/05-06/13），多 worker 下进程内内存态互不同步；②鉴权与数据权限"写了没挂"（覆盖率 34%、配置层坏死、整域裸奔 PERM-11/15/16/17）；③占位桩冒充功能（审计写而不可查、锁定锁而不可解 PERM-06/08）。最关键待修：配置 Redis/共享存储；给 125 个 NONE 端点补权限；实现真实审计查询与账号解锁；别名接入鉴权。

### 九、平台管理/运维域（ADMIN，23 项）

| ID | 功能/问题 | 等级 | 状态 | 证据位置 | 工作量 | 验证方式 | 备注/关联 |
|---|---|---|---|---|---|---|---|
| ADMIN-01 | 备份 API 路由自 import 自己必 ImportError，落占位路由 | P0 | 待修 | endpoints/backup.py:7-25 | 备份三层合计 4-5d | 静态已证 | 备份三层皆虚集群（01/02/03）；将第一轮"备份三层齐备"降级 |
| ADMIN-02 | 备份恢复 restore 产品内不存在（BackupService 无 restore 方法） | P0 | 待修 | backup_service.py 无 restore | 并入 ADMIN-01 | 静态已证 | 恢复只有需登录服务器的脚本 |
| ADMIN-03 | 备份/校验脚本技术栈错位（MySQL vs 实际 SQLite） | P0 | 待修 | scripts/backup_database.sh:10-12；verify_backup.sh:118 | 并入 ADMIN-01 | 静态已证 | 即便跑起来备的也不是这份数据 |
| ADMIN-04 | 备份文件完整性校验部分实现可绕过 | P2 | 待修 | verify_backup.sh:80-104 | 0.5d | 静态已证 | — |
| ADMIN-05 | admin_stats 路由死壳 fallback 占位 | P2 | 待修 | endpoints/admin_stats.py:7-22 | 0.5d | 静态已证 | **主项**：RPT-15 同一 admin_stats 占位，RPT-15 标重复-合并→ADMIN-05 |
| ADMIN-06 | /admin/stats 系统指标关键指标全硬编码（99.9%/0 错误率/从未备份） | P1 | 待修 | admin_compat.py:215-224 | 1d | 静态已证 | — |
| ADMIN-07 | 行政管理（用品/车辆/资产/费用）全硬编码+写端点缺失（404） | P1 | 待修 | admin_compat.py:18-186,254 | 2-3d | 静态已证 | 前端 admin.js:123-160 POST 必 404 |
| ADMIN-08 | Prometheus/Grafana 监控栈装饰性（无 /metrics 端点） | P1 | 待修 | monitoring/prometheus.yml:17-20 | 2-3d | 静态已证 | 抓 mysql:3306/redis 架构错位 |
| ADMIN-09 | 健康检查常量返回不查依赖 | P2 | 待修 | app/main.py:161-171 | 0.5d | 静态已证 | — |
| ADMIN-10 | 调度器指标/状态页真采集但内存态+不可抓取（重启清零） | P2 | 待修 | utils/scheduler_metrics.py:1-13 | 1d | 静态已证 | 关联 ADMIN-20 取证能力 |
| ADMIN-11 | 项目缓存层安慰剂（内存模式零命中） | P2 | 待修 | projects/project_crud.py:150 | 1d | 静态已证 | — |
| ADMIN-12 | 缓存管理端点调不存在的方法基本不可用（clear 会 flushdb 整库） | P1 | 待修 | projects/cache.py:85-91 | 1d | 静态已证 | 若与限流/Token 黑名单共库危险 |
| ADMIN-13 | 数据导入执行字段与模型不符→假失败真入库 | P1 | 待修 | import_upload.py:56-66 | 0.5d | 静态已证 | 用户看到失败数据实际已导入；本周内处理 |
| ADMIN-14 | 导入错误回执明细被丢弃任务表不落错误 | P2 | 待修 | import_upload.py:78-83 | 1d | 静态已证 | 修复并入 ADMIN-13 |
| ADMIN-15 | 导入部分失败/幂等：逐行容错+工时查重符合设计 | P3 | 已验证 | timesheet_importer.py:169 | — | 静态已证（正面确认） | 无缺陷 |
| ADMIN-16 | 导出水印 watermark_service 死代码全仓零调用 | P1 | 待修 | services/export/watermark_service.py | 1-2d | 静态已证 | 且中文渲染黑方块需注册 CID 字体 |
| ADMIN-17 | 统一文件上传服务孤儿；无内容校验/AV | P2 | 待修 | services/file_upload_service.py | 1-2d | 静态已证 | — |
| ADMIN-18 | 合同附件上传/下载任意文件读取漏洞 | P0(安全) | 待修 | sales/contracts/enhanced_attachments.py:31-41,67-84 | 1d | 静态已证 | 下载无目录白名单，可拖走整库/私钥；documents/operations.py:90-99 有正确范式；本周内处理 |
| ADMIN-19 | 附件-单据串联删单不删文件 343 孤儿文件 | P2 | 待修 | documents/operations.py:148 | 1-2d | 静态已证 | project_documents file_path 全 /demo/ 假路径 |
| ADMIN-20 | 日志管理/轮转不存在（仅 stdout，logs/ 空） | P2 | 待修 | core/logging_config.py:145 | 1d | 静态已证 | 配合 ADMIN-10 故障后几乎零取证能力 |
| ADMIN-21 | debug_issue/design_review 两 sync 真实现 | P3 | 已验证 | debug_issue_sync_service.py | — | 静态已证（正面确认） | 无缺陷 |
| ADMIN-22 | 编码规则生成器无统一功能，分散硬编码+并发撞号 | P2 | 待修 | business_support_utils/service.py:180-204 | 1-2d | 静态已证 | — |
| ADMIN-23 | 运维自助度：多数运维操作必须进服务器/改库 | P1(汇总) | 待修 | 见 ADMIN-01/06/12/20/22 | 汇总 | 静态已证 | 正面项：调度热 reschedule/导入模板/excel_export |

**ADMIN 域小结**：本域"真实现"比例各域最低。备份 API 整体占位、restore 产品内不存在且脚本技术栈错位；监控栈无 /metrics 纯装饰；行政管理前端有页后端硬编码演示数据且写端点缺失；缓存管理调不存在方法；发现 1 个 P0 安全漏洞（ADMIN-18 合同附件任意文件读取）。约 18-22 人日，ADMIN-18/ADMIN-13 建议本周内处理。

### 十、多租户域（TEN，8 项）

| ID | 功能/问题 | 等级 | 状态 | 证据位置 | 工作量 | 验证方式 | 备注/关联 |
|---|---|---|---|---|---|---|---|
| TEN-01 | 租户管理 API 全 404（四路盲猜 import 全不存在落空路由） | P1 | 待修 | endpoints/tenants.py:7-22；api.py:1236 仍打印成功 | 1d | 静态已证 | 宣传 SaaS 则 P0；TenantService 292 行无 API 调用方 |
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
| RPT-01 | 报表中心 8+ 类型返回"待实现"桩但权限矩阵照常展示 | P1 | 待修 | router.py:83-90 兜底空 200 | 做实/下架 | 静态已证 | COMPANY_MONTHLY 在 template_report 有真实现（两套体系未打通） |
| RPT-02 | PROJECT_MONTHLY 成本恒 0 | P2 | 待修 | project_reports.py:244 | 1d | 静态已证 | — |
| RPT-03 | WORKLOAD/COST_ANALYSIS 人工成本=工时×硬编码 100 | P2 | 待修 | analysis_reports.py:190-191 | 0.5d | 静态已证 | 与 PROJ-13(100)/PROJ-11(200)、HR-21 同"时薪多口径"病灶第三处复制且数值矛盾 |
| RPT-04 | 财务报表 4 端点无数据静默降级硬编码 demo，预算=成本×1.08 | P1 | 待修 | finance_reports.py:128-129,163,222 | 2-3d | 静态已证 | 与 SALES-06/13 同 mock 集群，响应无 is_demo 标记 |
| RPT-05 | 财务报表含税/不含税口径不分 | P2 | 待修 | finance_reports | 与 SALES-17 打包 | 静态已证 | 同 SALES-17 根 |
| RPT-06 | report_center xlsx 导出明细恒"无数据"（双键名+data 键不匹配） | P1 | 待修 | export.py:63 vs excel_renderer.py:182 | 0.5d(Quick-win) | 静态已证 | — |
| RPT-07 | template_report 三套并存两 orphan+一断链 import | P2 | 待修 | template_report_service.py:196 | 1-2d | 静态已证 | — |
| RPT-08 | PPT 生成器真产 pptx 但内容 100% 硬编码+0 调用方 | P3 | 待修 | generator.py:72-130 | 下架/做实 | 静态已证 | — |
| RPT-09 | 8 个工作台适配器统计卡因 label= vs 必填 title= 全部恒空（~46 张卡） | P1 | 待修 | schemas/dashboard.py:13-25；unified.py:66 静默吞 | 1-1.5d | 静态已证 | 本轮最严重契约断裂，schema 契约断裂同 AS-13(客户360)型 |
| RPT-10 | 决策驾驶舱 4 处 KPI 绑不存在字段恒 0 | P1 | 待修 | useExecutiveDashboard.js（project_growth/on_time_delivery_rate 等） | 1d | 静态已证 | schema 契约断裂同 AS-13 型 |
| RPT-11 | 驾驶舱营收/利润前端 Math.min(×0.3) 封顶+目标写死+毛利冒充净利润 | P1 | 待修 | useExecutiveDashboard.js | 删封顶 0.5d | 静态已证 | 数据操纵；真实数据超 4800 万即被裁剪 |
| RPT-12 | 驾驶舱成本页签/销售漏斗恒空（useState 无 setter），健康度结果丢弃 | P2 | 待修 | useExecutiveDashboard.js | 1d | 静态已证 | — |
| RPT-13 | 采购看板"节省金额"写死 0 | P2 | 待修 | 采购看板 | 下架 0.5d | 静态已证 | — |
| RPT-14 | 成本看板图表配置保存/读取为桩 | P3 | 待修 | 成本看板 | 1d | 静态已证 | — |
| RPT-15 | admin_stats 整体占位 fallback | P2 | 重复-合并→ADMIN-05 | admin_stats.py:7-23 | — | 静态已证 | 与 ADMIN-05 同一文件同一占位，ADMIN-05 为主 |
| RPT-16 | 负荷瓶颈接口 dept.name 字段不存在必 500（模型只有 dept_name） | P2 | 已验证 | workload.py:373；organization.py:59-62 | 0.1d(Quick-win) | 静态已证；✅已补回归验证（2026-07-03） | 当前 Department.name 兼容属性返回 dept_name；已新增超载部门 API 合约测试 |
| RPT-17 | 报表框架主干（引擎/17 适配器/YAML/Excel·Word 渲染/销售域导出） | — | 已验证 | engine.py:126；excel_export_service.py:106-235 | — | 静态已证（正面确认） | 无缺陷 |

**RPT 域小结**：框架和大部分聚合真（RPT-17），但三类系统性假象：①"待实现"桩静默返回空 200（RPT-01）；②demo 硬编码兜底/前端封顶让经营数字失真（RPT-04/11）；③schema 契约断裂让约 46 张工作台卡+驾驶舱 4 项 KPI+导出明细恒空（RPT-06/09/10，均 AS-13 同型）。建议作"契约测试"专项一次收口。Quick-win 包：RPT-06、RPT-09 批量改名、RPT-16、RPT-11 删封顶、RPT-13 下架。

### 十二、边缘业务模块域（MISC，24 项）

| ID | 功能/问题 | 等级 | 状态 | 证据位置 | 工作量 | 验证方式 | 备注/关联 |
|---|---|---|---|---|---|---|---|
| MISC-01 | 竞品分析菜单页展示虚构数据（后端硬编码+前端 0 次 API 调用） | P0 | 已验证 | competitor_analysis.py；salesRoutes.jsx；sidebarConfig/default.js；tests/api/test_competitor_analysis_stopgap_contracts.py；salesCompetitorAnalysisStopgap.test.jsx | 下架 0.5d | 静态已证；✅已下架止血并回归（2026-07-03） | 菜单与 `/sales/competitor-analysis` 路由已移除；后端直链返回 501，不再吐“竞品A/宁德时代”等硬编码假数据 |
| MISC-02 | 资源总览 PMO 可达页恒空白 | P1 | 待修 | resource_overview.py:7-24；ResourceOverview.jsx:323 | 聚合 3-5d/摘菜单 0.5h | 静态已证 | 与 HR-23、AS-24 同 resource_conflicts 空表/双轨病灶互引 |
| MISC-03 | 预警超时升级任务坏死（对 Column 取布尔导致查询短路） | P1 | 已验证 | alert_escalation_task.py；tests/unit/test_utils_missing.py | 0.5d | 静态已证；✅已动态回归（2026-07-03） | 与 APPR-17/AS-25 的 841 饿死不同源，是升级任务本身崩；未升级判断改 SQL 表达式并纳入 OPEN/PENDING/ACKNOWLEDGED/PROCESSING |
| MISC-04 | best_practice(P0 优化 4 端点) 僵尸+半成品（从未注册、0 commit、无认证） | P2 | 待修 | best_practice.py:32-34；set_kitting_targets:435 | 下架 0.5d | 静态已证 | 零鉴权写端点；与已挂载 best_practices/ 勿混 |
| MISC-05 | endpoints/knowledge 僵尸三无（表不存在挂载即 500，硬编码冒充 AI） | P2 | 待修 | __init__.py:19；knowledge_entries/knowledge_alerts 表不存在 | 下架 1d | 静态已证 | 前端调另一套 /knowledge-base |
| MISC-06 | documents 文档中心上传端到端不可用（无 multipart 端点前端必 422） | P1 | 待修 | documents POST 只收 JSON；Documents.jsx:188 | 2-3d | 静态已证 | 权限错用 document:read 应改 document:create；DB 60 行全 demo 假 path |
| MISC-07 | advantage_products 133 行真数据不可达（前端组件孤儿无入口） | P1 | 待修 | AdvantageProducts.jsx 无 import；routes/sidebar 零命中 | 加路由+菜单 0.5d | 静态已证 | 5 模块唯一有真数据；import?clear_existing=true 默认清库需改 false |
| MISC-08 | change_impact 占位上线真路由未挂 | P2 | 待修 | change_impact.py:7-24；projects/change_impact.py 未 include | 下架 0.5h/挂真 1-2d | 静态已证 | — |
| MISC-09 | cost_collection POST/collect 缺 RBAC（任何用户可全量触发写库归集） | P1 | 待修 | cost_endpoints/collection.py:55 | 0.5-1d | 静态已证 | 零鉴权写端点；与 PROJ-11 成本归集互引 |
| MISC-10 | cost_variance 成本偏差真功能·隐身（无菜单入口，无数据权限） | P2 | 待修 | financeRoutes:28；/{project_id}:166 | 1d | 静态已证 | /{project_id} 不存在返 200 应 404；/summary N+1 |
| MISC-11 | solution_credits 僵尸+刷分漏洞（自退任意积分） | P2 | 待修 | solution_credits 428 行；POST/internal/refund:56 | 下架 0.5h | 静态已证 | 任何登录用户可给自己退任意积分，启用扣费即刷分 |
| MISC-12 | performance_contract 裸 sqlite3+import 期 DDL | P1 | 重复-合并→HR-15 | contract.py:28,140 | — | 静态已证 | 与 HR-15 同一 performance_contract 裸 sqlite3，HR-15 为主 |
| MISC-13 | project_contributions 闭环断裂（前端仅 getReport 接了页面，报告页永远空） | P2 | 待修 | 后端 5 端点全真；rate/calculate/list 仅测试出现 | 2-3d | 静态已证 | DB period 全 "pr30222" 非法 |
| MISC-14 | pm_involvement 零鉴权+数据源桩致误判（6 端点全无 auth 含写语义） | P1 | 待修 | 6 端点无 auth；get_similar_project_count:131 硬编码 0；crd.py:195 | 加 auth 0.5d+数据源 2-3d | 静态已证 | 零鉴权写端点；DB 10/12 工单误判"高风险"失去区分度 |
| MISC-15 | relationship_maturity 假数据+必崩（improvement-plan 引用未定义变量 NameError 500） | P1 | 待修 | relationship 725 行:286,602 | 下架 1h | 静态已证 | 前后端双假（RelationshipMaturity.jsx:41 硬编码）；建议下架 |
| MISC-16 | RequirementSurvey 前端孤儿+后端 404 僵尸 | P2 | 待修 | survey.js:4；后端零匹配无表 | 删目录 0.5h | 静态已证 | 完整开发后遗弃 |
| MISC-17 | resource_scheduling 占位+完全僵尸 | P2 | 待修 | placeholder shim；api.py:1151 | 下架 0.5h | 静态已证 | 与真实 engineer_scheduling 无关联，勿误删 |
| MISC-18 | business_support 前缀丢失 5 组 API 全 404 | P1 | 待修 | api.py:826 不带前缀挂载 | 补前缀 0.5d/下架 1d | 静态已证 | dashboard/bidding/contractReview/paymentReminder/getTodos 全 404 |
| MISC-19 | business_support_orders 发货真其余僵尸 | P2 | 待修 | 发货单完整；开票/对账/入驻/验收僵尸 | 评估 1d | 静态已证 | 发货审批走模块内翻状态不走引擎 |
| MISC-20 | budget 写操作权限全配成 budget:read（接前端即越权） | P2 | 待修 | budgets.py/items.py/allocation_rules.py update/submit/delete | 换权限码 0.5d | 静态已证 | permissions 表已有 budget:create/update/delete 种子 |
| MISC-21 | budget 整体审批自闭环+前端僵尸+脏数据（total≠Σitems） | P2 | 待修 | submit/approve 只翻 status 无 ApprovalInstance | 切 budgetApi 2-3d/下架 0.5d | 静态已证 | 与 APPR-02 同源（连接口都没接）；DB 60 行全部 total≠Σitems |
| MISC-22 | alerts 自定义规则 CRUD 是摆设（通用引擎无生产调用方） | P2 | 待修 | AlertRuleEngine.evaluate_rule 仅单测；rules.py:128 | 加调度 2-4d/降级 0.5d | 静态已证 | 实际产警走各域硬编码 rule_code；create/toggle 无权限 |
| MISC-23 | culture_wall config 占位+goals 前端 404+空播 | P2 | 待修 | culture_wall_config.py:7-25；admin.js:243；contents 无 PUT/DELETE | 1-2d | 静态已证 | 与 HR-22 同一 culture_wall，HR-22 为主，本项补 config/goals/PUT 细节，互引不合并 |
| MISC-24 | ai_strategy 84 端点巨型僵尸+前端 5 接口全 404 | P2 | 待修 | /ai-strategy 8 模块 84 端点；aiStrategy.js 5 调用无一匹配 | 下架 0.5d/重写 5d+ | 静态已证 | 全库最大僵尸，典型前后端各写各的 |

**MISC 域小结**：24 个边缘模块以"僵尸/半成品/假实现"为主。P0 唯 MISC-01（用户正看虚构竞品数据）已下架止血；P1 集群：MISC-02 恒空白、MISC-03 升级任务坏死（已修复）、MISC-06 上传必 422、MISC-07 133 行真数据不可达+清库默认值、MISC-09 归集无 RBAC、MISC-12 裸 sqlite3+启动 DDL（并入 HR-15）、MISC-14 PM 误判 10/12、MISC-18 商务支持 5 组 404、人事 PII 入库。建议直接下架止血：resource_scheduling、relationship_maturity、change_impact 占位、culture_wall_config 占位、best_practice、endpoints/knowledge、solution_credits、RequirementSurvey、ai_strategy、business_support 五组。

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
| 8 | 结项无门禁 + 变更审批不回基线 | PROJ-06（已验证：结项 readiness 门禁） + PROJ-20（待修：变更审批回基线） |
| 9 | 现场调试签到/完工全链假实现 | PROD-01（主）＋ AS-01（重复-合并） |
| 10 | 14/56 定时任务 stub 且监控全绿 | APPR-04 |
| 11 | 通知触达假成功（email/SMS 假桩 + Redis 有产无消 + 841 条饿死） | AS-02（已验证） + AS-15（已验证） + AS-03（已验证） + APPR-17（已验证） |
| 12 | BOM→生产工单断链 | PROD-08（主）＋ APPR-05（重复-合并） |
| 13 | 售后无设备档案，工单无设备外键 | AS-10（主）＋ AS-11 ＋ APPR-06（重复-合并） |
| 14 | 派工冲突检测空转 | AS-04 |
| 15 | 销售预测接口整文件硬编码 | SALES-06（+ SALES-07 前端假兜底） |
| 16 | 发票门禁读旧轨空表 + update_invoice 绕上限/状态 | APPR-10 + APPR-11（+ SALES-09 权限、PEER-04/05 关联） |
| 17 | 合同审批撤回必 500（4 域，CONFIRMED） | APPR-07（主）＋ PEER-03（重复-合并） |

> 注：全局 P0 表为跨域去重后的危害排序视角；APPR-07/10/11、PROD-08、AS-10/11 在域内总表定级 P1，本台账等级列以域内总表为准，全局定级在备注标注。

## 视图二：按修复批次分组（对应汇总报告第四节）

| 批次 | 追踪 ID | 合计工作量 |
|---|---|---|
| **P0-0 资金正确性急救包**（插队最前） | SALES-03 → SALES-01 → SALES-02 → SALES-04 → APPR-10 → APPR-11（含 PEER-04）→ APPR-15 → PEER-05 → SALES-09 | 约 6-8d |
| **P0-0' 审批链救活包**（并入/前置 F2） | APPR-01（已验证）→ APPR-02（已验证）→ APPR-07（已验证，含 PEER-03）→ APPR-03（已验证；SALES-10 已随包消除） | 约 4-5d |
| **Quick-win 闸门包**（≤1d/项，本周清完） | PROJ-06（已验证：结项 readiness 门禁）、PROJ-10（已验证：里程碑 except 重抛+全局 complete 接状态机）、PRE-16（已验证：_has_live_ai 补 qwen）、PRE-23（已验证：立项关卡异常不再静默）、AS-19（已验证：关单 payload/id + 质保工单兜底）、APPR-07（已验证：撤回参数名）、AS-16（Header 铃铛）、PROD-13（报工回写移审批后） | 约 3d |
| **假实现止损下架包** | SALES-06（假接口下架）、SALES-07（前端假兜底）、SALES-13（智能报价页）、PROD-17（AI 排程建议）、PRE-15（售前移动端路由）、PRE-20（AI 工作流编排）、PRE-12（方案"PDF 导出"）、PRE-13（export-report 假 URL） | 约 2d |
| **F1 扩围（库存台账真实化）** | PROD-03（已验证）→ PROD-11（已验证，含 PROD-22）→ PROD-04（已验证）→ PROD-12（已验证）→ PROD-14（已验证）＋ PROD-02（已验证）；PROD-05（齐套修正）与 PROD-15（缺料→紧急采购闭环）仍待修 | 约 13d |
| **F3 扩围（通知+调度可信化）** | AS-02（已验证）、AS-15（已验证）、AS-03（已验证）、AS-06（已验证）、AS-25（已验证）、AS-23（已验证）、PROJ-21（已验证）、APPR-16（已验证）、APPR-17（已验证）、MISC-03（已验证）、PRE-21（已验证，含 APPR-22①）、APPR-04（stub 标记/禁用已完成，缺料回填待做）、APPR-22（①/②/③/⑤已修，第二调度器监控待做） | 约 10-14d |
| **其他（结构性/体验/收口，按域推进）** | 结构断链：PROD-08、AS-10、AS-11、PROJ-20、PROD-01、AS-04、PROD-06、PROD-07、PROD-16、AS-12；审批收口（F2 相关）：APPR-08、APPR-09、APPR-12、APPR-13（含 PEER-01/02）、APPR-19、APPR-20、APPR-21、PROD-09、PROD-10、SALES-05、AS-05、PROJ-04、PROJ-07；北极星体验：SALES-11、SALES-12、APPR-18、APPR-14、PROJ-03、PRE-04、PRE-10；数据可信：PROJ-11、PROJ-13、PROJ-14、PROJ-15、PROJ-16、PROJ-17/18/19、SALES-08、SALES-15；其余 P2/P3 按域排期 | 余量 |

## 视图三：数据清洗专项清单（存量脏数据，任何状态机修复前置）

| # | 脏数据 | 库内实况 | 关联 ID |
|---|---|---|---|
| 1 | 合同状态大小写两套混杂 | ACTIVE(18)/SIGNED(67)/draft(12)/executing(13)，ACTIVE 不属任何合法写入值 | APPR-13（PEER-01/02 收口后迁移归一） |
| 2 | 服务工单状态枚举外脏值 | 89 条中 48 条为枚举外值 | AS-05 |
| 3 | 项目状态三套词汇表 | COMPLETED(45)/EXECUTING(35)/ST01(24)/archived，定时任务过滤三套全不匹配 | PROJ-05（PROJ-04/PROJ-25 依赖先清洗） |
| 4 | 商机 assessment_status 两套值 | ASSESSMENT_COMPLETED(51) vs COMPLETED(4)，按 COMPLETED 统计漏 93% | PRE-24 |
| 5 | PO/POI 状态空值与读写字典错位 | PO 空状态 60 条、收货单 status 全空；读侧 ORDERED/PARTIAL_RECEIVED 无写入点 | PROD-11 + PROD-04 |
| 6 | quotation_type 非法枚举 | 存量含 AUTO/MANUAL/NORMAL | PRE-24 |
| 7 | 售前工单状态字典分裂 | PROCESSING(1)/REVIEW(1) 存量工单无路可走 | PRE-14 |
| 8 | 商机阶段词表分裂 | 经 advance 到 CLOSING 的商机在 PUT /stage 下为非法值 | SALES-21 |
| 9 | 报价存量版本成本/毛利错算 | qty≠1 的版本成本被低估，需重算脚本 | SALES-03 |
| 10 | project_costs 脏值 | 141 行中 60 行 cost_type 为空 | PROJ-11 |
| 11 | 预警积压 | 841 条 PENDING 积压 4 个月（2026-03-09~06-30）；代码已按最老优先逐批出队，生产一次性处置仍需运维窗口 | APPR-17（代码已验证） |
| 12 | 孤儿表/孤儿实例 | field_tasks(8)/field_checkins(3) 无模型无接口；entity_type 空审批实例 3 条 | PROD-01 / APPR-20 |
| 13 | machines 设备数据缺失 | 仅 6 行且 ship_date 全空，无 SN/客户/保修 | AS-10 |
| 14 | SLA 策略未激活 | 3 条 sla_policies 的 is_active 全 NULL；已按历史 NULL=启用兼容，调度任务会同步新工单 SLA monitor | AS-06（已验证） |
| 15 | 根目录 app.db 为 0 字节空文件 | 真实库在 data/app.db，易误导验证与备份 | 口径事实（汇总报告），建议删除或 README 标注 |

## 视图四：僵尸模块 Top 清单（后端有路由 / 前端零调用）

全局扫描约 **427/3104 端点（~14%）、137 模块前端零调用**。Top18：

| # | 模块/路由 | 端点数 | 关联 |
|---|---|---|---|
| 1 | /ai-strategy | 84 | MISC-24（全库最大僵尸） |
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
1. **占位自引用文件**（27 行自 import 永远 fallback 空 router，7 个）：itr.py、account_unlock.py、backup.py、change_impact.py、culture_wall_config.py、quality_risk.py、resource_scheduling.py。
2. **丢前缀挂载**：permissions.matrix、performance.individual、business_support 系列（MISC-18）。
3. **双段前缀 bug**：/analytics/analytics/skill-matrix、/kit-check/kit-check/*、/bonus/rules/rules。
4. **冗余别名挂载**：/acceptance（前缀版 44 端点前端用免前缀 legacy）、/technical-specs、/presale-analytics。

## 视图五：前端→后端 404 断链清单（排除第一轮 5 处）

新发现 **118 个唯一断链路径+47 处方法不匹配**。高价值项：

| 前端 service | 调用 | 后端实况 |
|---|---|---|
| aiStrategy.js:14-67 | /ai-strategy/analyze 等 | 84 路由无一匹配（MISC-24） |
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
| MISC-11 | solution_credits POST/internal/refund 任何登录用户可给自己退任意积分（刷分） | P2 |
| MISC-14 | pm_involvement 6 端点全无 auth（含写语义）+test 端点暴露生产 | P1 |
| MISC-09 | cost_collection POST/collect 仅要求登录，任何用户可全量触发写库归集，无留痕 | P1 |
| MISC-04 | best_practice 4 端点（含 PUT 写）均无认证 | P2 |
| PERM-11 | require_permission 覆盖率 34%，125 个 NONE 端点裸奔（通用 CRUD/员工/风险/产能任意登录可调） | P1 |
| PERM-15/16/17 | 数据权限整域裸奔：制造/供应链/财务 0 行级过滤，配置层坏死，CUSTOMER 恒 True | P1 |
| TEN-06 | 多租户无上下文全链 fail-open，163 非超管 tenant_id=NULL 畅通，越权不被拒 | P1 |
| MISC-05* | 人事 PII（ATE-人事档案系统.xlsx 56.8MB）提交进 git 库（misc.md 五·孤儿产物；建议 git-filter 清历史+入受控存储） | P1 |

> *注：任务清单以 MISC-05 指代人事 PII 项，但 misc.md 中 MISC-05 实为 endpoints/knowledge 僵尸；人事 PII 属该报告"五、孤儿产物"节的独立 P1 项、无 MISC 编号，此处按任务口径归入安全视图并标注真实来源。
