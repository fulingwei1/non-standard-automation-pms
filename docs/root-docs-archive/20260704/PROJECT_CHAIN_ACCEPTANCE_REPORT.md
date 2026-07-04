# 项目链路端到端验收报告

**链路**：项目立项 → 阶段计划 → 任务/里程碑 → 成本/风险 → 交付
**验收方式**：真实角色(PM/工程师)登录 → 逐环节调真实 API → 每步核对数据库 → 正向 + 越权双向 → 整库还原清理
**日期**：2026-07-02
**环境**：后端 `app.main:app`@127.0.0.1:8002；DB SQLite `data/app.db`（验收前整库备份，验收后已还原，零残留）
**结果**：链路主干 **端到端跑通**；检查项 **18/19 通过**，唯一未通过为**已确认的高危缺陷**（项目风险表缺失）。

---

## 1. 测试账号与角色

| 用户 | 角色 | 数据范围 | 关键权限 | 用途 |
|---|---|---|---|---|
| acc_pm | 验收-项目经理 | ALL | project/milestone/cost/risk 全套 | 立项、阶段、任务、里程碑、成本、风险 |
| acc_engineer | 验收-工程师 | OWN | project/milestone/cost read | 项目成员、越权对照 |
| acc_sales_rep | 验收-销售员 | OWN | 无 project/milestone/cost 写权限 | 越权对照 |
| acc_sales_rep2 | 验收-销售员 | OWN | — | 非项目成员越权对照 |

---

## 2. 正向主链路（单据流转与三方核对）

代表性一次完整执行（单据号，均已在验收后清理）：

| # | 环节 | 操作角色 | 单据 | 结果 | 三方核对 |
|---|---|---|---|---|---|
| 1 | 立项 | PM | 项目 `ACCPJ-xxxxxx`（id 108） | ✅ | API 201；DB `pm_id` 正确，初始 status=ST01 / stage=S1 |
| 2 | 阶段计划 | PM | 9 个阶段(S1–S9) | ✅ | 按模板"标准全流程"生成 `project_stages` 9 行 |
| 3 | 加成员 | PM | 成员（工程师，80%投入） | ✅ | 需 `project:update`；DB `project_members` 存在 |
| 4 | 建任务并分派 | PM | 任务（分派工程师） | ✅ | API 201；`check_project_access` 通过（PM 有项目访问权） |
| 5 | 里程碑 | PM | FAT 里程碑 | ✅ | 创建 PENDING → 流转 IN_PROGRESS → **COMPLETED** |
| 6 | 项目成本 | PM | 人工成本 ¥50,000 | ✅ | API 201；DB `project_costs` 归集到项目 |
| 7 | 项目风险 | PM | 风险(概率3×影响4) | ❌ **500** | **`project_risks` 表缺失**（见发现 P1） |
| 8 | 阶段推进 | PM | 首阶段启动 | ✅ | start→IN_PROGRESS(状态机认可)；重复 start 被 400 拒 |

**说明**：里程碑状态机不支持 PENDING 直达 COMPLETED，需先流转 IN_PROGRESS（接口按此设计，验收已适配）。

---

## 3. 越权 / 反向验收

| 用例 | 期望 | 结果 |
|---|---|---|
| N1 销售员建里程碑 | 403（无 milestone:create） | ✅ 403 |
| N2 销售员建成本 | 403（无 cost:create） | ✅ 403 |
| N3 工程师加成员 | 403（无 project:update） | ✅ 403 |
| N4 未携带 token 访问 | 401 | ✅ 401 |
| N5 风险概率>5 | 422（1–5 风险矩阵校验） | ✅ 422 |
| N6 非项目成员建任务 | 403（check_project_access 拦截） | ✅ 403 |

权限闸门核对：`milestone:*` / `cost:*` / `project:update` / `risk:create` 均按设计生效；非项目成员被 `check_project_access` 正确拦截；风险概率/影响强制 1–5 矩阵校验有效。

---

## 4. 发现问题（FINDINGS）

| 编号 | 严重度 | 环节 | 问题 | 影响 |
|---|---|---|---|---|
| **P1** | 高 | 项目风险 | `POST /projects/{id}/risks` 返回 **500**：`no such table: project_risks`。`ProjectRisk` 模型对应的 `project_risks` 表未随迁移建立（DB 中仅有 `pmo_project_risk` / `project_risk_history` / `project_risk_snapshot`） | 该项目风险登记端点**完全不可用**；存在**重复风险子系统**（`/projects/.../risks` 走 `project_risks`，`/pmo/projects/.../risks` 走 `pmo_project_risk`），一套已坏 |

> 附带观察（非阻断，建议关注）：
> - **阶段运行时状态与 `project_stages.status` 列不一致**：start 后服务层判定为 IN_PROGRESS，但 `project_stages.status` 列仍为 PENDING（运行时状态存于阶段节点实例而非该列），列表/报表若读该列会失真。
> - **里程碑 `/complete` 不支持 PENDING 直达 COMPLETED**，需先手动流转 IN_PROGRESS，接口易用性偏差。

---

## 5. 数据清理

- 本链路创建的全部测试数据（项目/阶段/成员/任务/里程碑/成本）与测试用户/角色，验收后从**验收前整库备份还原**。
- 还原后核对：`projects=104 / customers=110 / users=195` 与基线一致，测试标记数据 **0 残留**，`PRAGMA foreign_key_check` 回到基线水平（69，均为既有历史项）。

---

## 6. 结论

项目链路**业务主干端到端跑通**：从立项到阶段/任务/里程碑/成本，PM 与工程师真实协作，接口/数据库一致，权限与项目访问控制有效。

**待修复**：P1 项目风险表缺失导致 `/projects/{id}/risks` 500（高，且与 PMO 风险端点重复，需统一）；另建议修正阶段状态列与运行时状态不一致、里程碑完成态流转易用性两项观察。
