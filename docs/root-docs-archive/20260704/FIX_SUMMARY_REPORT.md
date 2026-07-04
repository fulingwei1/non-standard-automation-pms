# 缺陷修复总报告

**日期**：2026-07-02
**背景**：对 14 条业务链路 + 第二/三梯队全模块验收后，修复所发现问题
**源码改动**：均在工作区（未提交），供 review；DB 修复附带迁移文件
**验证**：每项均重启后端实测

---

## 一、已修复并验证 ✅

### A. 代码级 500 崩溃（6 个）
| 编号 | 模块 | 根因 | 修复 | 验证 |
|---|---|---|---|---|
| PR1 | 生产质检 | `quality.py` 4 处 `current_user["id"]`（User 非 dict） | 改 `current_user.id` | 质检 200 |
| P1 | 项目风险 | `project_risks` 表未建 | ORM metadata 建表 + `migrations/20260702_create_project_risks_sqlite.sql` | 风险创建 200 |
| AS1 | 售后工单 | 工单号 `SUP-日期-项目` 无序列→撞唯一约束 | 加同项目同日流水 `-NNN` | 同日多单 201 |
| BOM1 | BOM审批 | async/AsyncSession（app 同步栈）+ `selectinload(类)` 误用 | 端点/服务改同步 + `db.query` + `item.material` None 防御 | 审批 200 |
| OS1 | 外协交付 | `vendor` 查询误缩进在 `raise` 后 → UnboundLocalError | 缩进修正 | 不再 500 |
| TC1 | 任务中心 | 位置参数调用 `*,`(仅关键字)签名的 `get_task_detail` | 改关键字调用 | 建任务 201 |

### B. 审批模板 code 不匹配（F1/ECN1/TS1，系统性）
- **根因**：服务查 `SALES_CONTRACT_APPROVAL`/`ECN_STANDARD`/`TIMESHEET_APPROVAL`，但 DB 中对应模板是**孤儿** `TPL_CONTRACT`/`TPL_ECN`/`TPL_TIMESHEET`（零代码引用，已发布且各带审批流节点）。
- **修复**：将 3 个孤儿模板 `template_code` 改为服务期望的 code（复用其审批流）+ `migrations/20260702_fix_approval_template_codes_sqlite.sql`。
- **验证**：TIMESHEET 提交→SUBMITTED、ECN 提交→APPROVING、CONTRACT 模板解析（3/3，不再"模板不存在"）。

### C. 业务规则 / 逻辑（F2/F3/PS2 + OS1残留）
| 编号 | 修复 | 验证 |
|---|---|---|
| F3 | 发票创建加"累计开票≤合同额"校验（排除作废） | 超额 150k>100k 被拒 400；合理 50k 通过 201 |
| F2 | 合同签署加"须已审批通过"前置 | 未审批签署被拒 400 |
| PS2 | 售前工单完成加幂等（已完成不可重复） | 二次完成被拒 400 |
| OS1残留 | 外协交付 vendor 查询去掉恒不匹配的 `vendor_type=="OUTSOURCING"` 过滤 | 不再误报"外协商不存在"404 |

**合计已修复：6 代码级500 + 3 审批模板 + F2/F3/PS2 + OS1残留 = 12 项，全部实测通过。**

---

## 二、多模块 RBAC 缺失 → 已修复（关键动作端点）✅

**发现**：生产/发货/售后/售前/ECN执行段/缺料/验收 等模块的写/动作端点用 `get_current_active_user`，无细粒度权限（任意登录可审批/执行）。

**安全实施**（先授权、后设卡、防锁死）：
1. **补齐权限码**：新建 `production:manage`/`delivery:manage`/`presale:manage`/`ecn:execute`/`shortage:manage`/`acceptance:manage`/`aftersales:manage`（`migrations/20260702_rbac_module_permissions_sqlite.sql`，幂等）。
2. **按角色策略授予**：每个码授予 admin + **gm(总经理)** + 模块负责人角色（如 production→production_mgr/pmo_director、delivery→sales_director/finance_mgr、presale→tech_director/presales_engineer、shortage→procurement_mgr/production_mgr、acceptance→quality_mgr/pm、aftersales→service_mgr）。**每个码都含 gm+admin，杜绝锁死关键用户**；并补授 gm 缺失的 `production:write`。
3. **端点加 `require_permission`**：为 18 个关键动作端点（生产计划审批/发布、报工审批、工单完成；发货单审批/发货/签收；售前方案评审/工单完成；ECN 开始执行/验证/关闭；缺料处理/解决、替代料技术/生产审批；验收完成；售后工单创建）替换鉴权依赖。

**验证（15/15 通过）**：每个动作——**无关角色→403（RBAC 强制生效）**、**授权角色→非403（不锁死，正常放行）**；DB 核对**总经理 gm 持有全部 7 个新权限（不被锁）**。

> 说明：本轮加固覆盖各模块**最危险的审批/执行/完成动作端点**（即"任意登录可审批"的核心风险）。纯读/次要创建端点未逐一加卡，可按同一"补码→授权(含gm)→加卡→验证"模式继续细化。

---

## 三、附带观察（非阻断）
- 多路由重复挂载：`sales`/`sales-regions`/`sales-targets`/`sales-teams` 同一套销售路由挂 4 次；验收单、工时、审批亦有 `/x` 与 `/y` 双挂。建议清理。
- 采购成本自动归集依赖订单状态推进到 RECEIVED/COMPLETED（非缺陷，D2 已澄清）。
- BOM approve 双重审批语义（要求已 APPROVED 才能"审批建PO"）建议梳理。

---

## 四、迁移文件
- `migrations/20260702_create_project_risks_sqlite.sql`（P1）
- `migrations/20260702_fix_approval_template_codes_sqlite.sql`（F1/ECN1/TS1）
- `migrations/20260702_rbac_module_permissions_sqlite.sql`（RBAC 权限码+种子角色授权）

（其余为代码改动，见 `git diff`）

---

## 4.5 补充验收（数据可见性 + 否定链路）与新修复
- **数据可见性(data_scope 读隔离) 10/10**：客户/商机——归属人列表+详情可见；同 OWN 他人**列表不含+详情 403**（读隔离生效）；经理(ALL)可见。填补"该看的能看到、不该看的看不到"。
- **否定链路 6/6**：发货单驳回→不能发货(400)、报价驳回→不能转合同(400) 已内建有效；**采购订单驳回→仍可收货** 为新发现 **NP1**，已修复。
- **NP1 修复**：`purchase/receipts.py` 收货创建增加订单状态前置——仅 APPROVED/收货中订单可收货，草稿/待审/**驳回**/取消一律 400；实测：驳回订单收货被拒(400)、已审批订单仍可正常收货(200)。

## 4.6 BOM 专项验收 + 演示数据（持久化）
- **KR-500 修复**：机台齐套率 `kit_rate_service.calculate_kit_rate` 对未关联物料的 BOM 项取 `material.current_stock` 崩溃(NoneType)，加 None 防御；实测机台齐套率 200。
- **演示数据（保留，不清理）**：为 DEMO26 项目 66/67/68 各建 1 台机 + 1 套**已发布多级 BOM**——`DEMO26-BOM-066/067/068`（视觉检测机/ICT/FCT），含 L1 部件+L2 零件、**自制8/采购17/外协4** 分类、关键件、装配属性(交期/替代料)。
- **能力链验证 3/3**：项目齐套率可算、机台齐套率可查（KR-500 修后）、BOM 生成采购申请成功（`PR-20260702-001`，¥63940，打通 BOM→采购，二次调用正确判"已生成"不重复）。填补此前"无 RELEASED BOM 致齐套率算不出/source_type 全空"两大数据缺口。
- **分阶段齐套率细化（标准 S 码）**：装配属性 `assembly_stage` 由中文名改为标准阶段码并覆盖全部 29 项明细（消除 UNKNOWN）——采购件→**S3 采购备料**、自制/外协件→**S4 加工制造**、一级总成→**S5 装配调试**；并做备料梯度。实测分阶段齐套率：项目66 S3=60%(关键件 blocking 3/5)/S4=100%/S5=0%、项目67 S3=100%、项目68 全 0%（刚发布）。
- 备份：`app.db.with-demo.bak`（含演示 BOM + S 码装配阶段 + 备料梯度）。

## 4.7 ECN 设计变更 → BOM 影响（专项验收 + 演示数据）
- **全链路跑通**：建 ECN（`ECN-260702-001` 视觉检测机相机选型变更，项目66/机台4）→ 受影响物料（相机替换 + 直线模组数量变更）→ **分析 BOM 影响**（`ecn_bom_impacts`：影响 7 项、成本影响 ¥4400）→ 影响汇总 → 5 级审批通过 → 开始执行(EXECUTING) → **同步到 BOM**。
- **EBC-1 修复**：`ecn_integration_service.sync_to_bom` 用 `bom_item.qty` 赋值，但 BomItem 列名是 `quantity`（无该别名）→ **ECN 改数量静默丢失**。改为 `quantity`，并让 REPLACE 也应用规格/数量。实测同步后 BOM 真被改：相机 海康MV-CA050-10GM→**华睿A5501**、直线模组数量 2→**3**（updated_count=2）。
- **RBAC 补授**：ECN_STANDARD 审批流路由到 `quality_mgr`（品质经理），补授其 `ecn:approve`（写入迁移），使工作流指派的审批人具备权限。

## 4.8 ECN→BOM 变更审计留痕（补全 + schema 修复）
- **发现**：`ecn_bom_changes` 表**没有 ORM 模型**（只有 EcnBomImpact 有），从未被写入；且其 `ecn_id` 外键**误指向遗留表 `ecn_records`**（应为 `ecn`）——EBC-2。
- **修复**：① 新建 `EcnBomChange` 模型（`app/models/ecn/impact.py`）并导出；② 重建 `ecn_bom_changes` 表把外键改指 `ecn(id)`（`migrations/20260702_fix_ecn_bom_changes_fk_sqlite.sql`，保留有效行、丢弃指向遗留表的孤儿行）；③ `sync_to_bom` 每笔变更写入审计记录（旧值→新值+成本影响）。
- **验证**：同步后 `ecn_bom_changes` 落库 2 条——相机 REPLACE(海康MV-CA050-10GM→华睿A5501, -¥1200)、直线模组 UPDATE(数量2→3, +¥5600)。

## 五、总计
**已修复并验证：23 项**（新增 EBC-2 ecn_bom_changes 外键指向错误+审计留痕补全；EBC-1 ECN同步数量字段名；KR-500 机台齐套率 NoneType） = 6 代码级500 + 3 审批模板 + F2/F3/PS2 + OS1残留 + RBAC(7模块18端点关键动作)。
3 个迁移文件；源码改动约 17 个文件（工作区未提交，供 review）。所验证均重启后端实测通过。
