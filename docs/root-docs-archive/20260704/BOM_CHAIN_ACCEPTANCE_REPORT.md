# BOM 创建/维护/变更管理链路端到端验收报告

**链路**：建机台 → 建 BOM(DRAFT) → 明细维护(增/改) → 审批 → 发布(RELEASED) → 齐套率闭环 → 版本管理 → BOM 生成采购申请
**验收方式**：真实角色(BOM 工程师/BOM 审批)登录 → 逐环节调真实 API → 每步核对数据库 → 正向 + 反向 → 整库还原清理
**日期**：2026-07-02
**环境**：后端 `app.main:app`@127.0.0.1:8002；DB SQLite `data/app.db`（验收前整库备份，验收后已还原，零残留）
**结果**：BOM 创建/维护/发布/版本/采购联动**端到端跑通**，并**闭环解答了齐套率 KR-obs**。检查项 **15/16 通过**，唯一未通过为已确认的高危缺陷（BOM 审批端点 500）。

---

## 1. 正向主链路（单据流转与三方核对）

| # | 环节 | 操作角色 | 结果 | 三方核对 |
|---|---|---|---|---|
| 0 | 建机台 | BOM审批 | ✅ | 机台挂 project 104 |
| 1 | 建 BOM(带2条初始明细) | BOM工程师 | ✅ | `bom_headers` status=DRAFT，挂 project/machine；`bom_items`=2 |
| 2 | 新增明细 | BOM工程师 | ✅ | `bom_items` 2→3 |
| 2 | 修改明细数量 | BOM工程师 | ✅ | 明细 quantity 改为 3 生效 |
| 3 | BOM 审批 | BOM审批 | ❌ **500** | approve 端点崩溃（见发现 BOM1） |
| 4 | 发布 | BOM工程师 | ✅ | `bom_headers` status→**RELEASED** |
| 5 | **发布后齐套率可计算** | BOM审批 | ✅ | kit-rate 返 200，kit_rate=0.0（无到货→0，正确） |
| 6 | BOM 版本可查 | BOM工程师 | ✅ | versions 接口 200 |
| 7 | BOM 生成采购申请(联动) | BOM工程师 | ✅ | generate-pr 200 |

**闭环结论（回应齐套率 KR-obs）**：`assembly_kit_service` 要求 `BomHeader.status=="RELEASED"`（错误文案写"已发布"），而 BOM 发布正是置为 RELEASED；本次**建 BOM→发布→齐套率立即可算**，证实此前齐套率返 404 仅因**数据中无任何已发布(RELEASED) BOM**，非状态口径 bug。**KR-obs 已澄清为数据/流程状态，非缺陷。**

---

## 2. 越权 / 反向验收

| 用例 | 期望 | 结果 |
|---|---|---|
| N1 无 bom:approve(工程师)审批 | 403 | ✅ 403（审批有权限闸门） |
| N2 已发布 BOM 重复发布 | 拒绝 | ✅ 400（状态机） |
| N3 未携带 token 访问 | 401 | ✅ 401 |

**BOM 模块 RBAC 现状**：仅**审批**有权限校验(`bom:approve`)；创建/明细/发布/版本/生成采购申请均为任意登录（`get_current_active_user`）。

---

## 3. 发现问题（FINDINGS）

| 编号 | 严重度 | 环节 | 问题 | 影响 |
|---|---|---|---|---|
| **BOM1** | 高 | BOM 审批 | `POST /bom/headers/{bom_id}/approve` 返 **500**：`bom_approve.py:62 TypeError: object NoneType can't be used in 'await' expression`（端点写成 async + `await AsyncSession`，但底层为同步 Session，await 非可等待对象） | **BOM 审批端点完全不可用**（与质检 PR1 同类：异步/同步会话不匹配的代码缺陷） |
| **BOM2** | 中 | BOM 发布控制 | 发布(release)可从 DRAFT **直接置 RELEASED，无"必须先审批通过"的前置**；叠加 BOM1 审批已坏，BOM 实际可绕过审批直接发布 | 缺发布前审批管控（与合同签署 F2 同类控制弱点） |

> 附带：BOM 创建/明细/发布/采购联动均无 RBAC（仅审批有），职责分离偏弱。

---

## 4. 数据清理

- 测试机台、BOM 及明细，验收后从**验收前整库备份还原**。
- 还原后核对：`bom_headers=8 / bom_items=56 / machines=3 / users=195` 与基线一致（`BOM-` 前缀 5 条为种子数据），测试标记数据 **0 残留**，`PRAGMA foreign_key_check` 回到基线（69）。

---

## 5. 结论

BOM 创建/维护/发布/版本/采购联动主干**功能正常**：BOM 从建单、明细增改、发布(RELEASED)、版本查看到生成采购申请均可用，明细数量与状态落库正确；并**闭环验证了发布后齐套率可正常计算**（澄清齐套率 KR-obs 非缺陷）。

**待修复**：BOM1 审批端点 500（高，异步/同步会话不匹配，须修复）；BOM2 发布缺审批前置（中）。
