# 销售模块 易用性修复 + 会议纪要 AI 增强

**日期**：2026-07-02

## 一、易用性 7 项修复（对照评分 6/10 的问题清单）

| # | 问题 | 修复 | 验证 |
|---|---|---|---|
| 1 🔴 | 占位脏数据满屏（customers_customer_name…） | 清洗为真实非标行业名：客户30/项目60/供应商30/机台3/BOM3/物料30/商机25 | 占位残留 0 |
| 2 🔴 | 销售员菜单无"报价/合同"入口 | **根因**：`sales:quote:read`/`sales:contract:read` 等权限码 `is_active=0` 被权限引擎过滤。**激活**这些码 + 授予 sales_rep 读/建 + 迁移 | yangc 菜单现显示 报价管理/合同管理 ✅ |
| 3 🟡 | 新建客户手填"客户编码*" | 前端自动生成 `KH-YYYYMMDD-XXXX`（只读+提示"系统自动生成"） | 实测 KH-20260702-8302 只读 |
| 4 🟡 | 空提交无校验提示 | 改为内联校验（红字"请填写客户名称"+邮箱格式校验），去掉 alert | 空提交显示内联错误 ✅ |
| 5 🟡 | "行业"自由文本 | 改为下拉 Select（家电/消费电子/汽车/新能源/半导体…12项） | 行业为下拉 ✅ |
| 6 🟢 | 列表首屏空白 | CustomerTable 加骨架屏（animate-pulse 6行占位） | — |
| 7 🟢 | 空状态干巴巴 | 空状态加图标 + "去新建"引导按钮（onCreate 已连线） | — |

涉及前端：`CreateCustomerDialog.jsx`、`CustomerTable.jsx`、`CustomerManagement/index.jsx`、`sidebarConfig/default.js`。迁移：`20260702_grant_sales_rep_quote_contract_sqlite.sql`。

> 权限缓存说明：权限走进程内内存缓存（10min TTL / Redis 未配置），直接改库后需重启后端或调用失效接口才生效。

## 二、会议纪要 AI 增强（3 项 + 清单）

### 增强 0：AI 生成"下次会议信息清单"（非标核心）
纪要解读新增 `next_meeting_checklist`：**需获取 / 需确认 / 技术需求盲点**。实测对小米 FCT 纪要输出：需获取"具体3种机型规格/测试项清单/来料状态/产能/验收标准/现场条件/MES协议"，需确认"15秒是单工位还是整体循环/双工位切换逻辑"，盲点"机型兼容机械干涉风险/测试项复杂度影响节拍"——直击"需求不清晰致失败"。

### 增强 1：文件输入
`POST /sales/activities/parse-minutes-file`（multipart）支持 `.txt/.md/.docx`（python-docx 解析）→ 走同一后台 AI 任务。实测上传 minutes.txt（127字符）→ 解析成功。

### 增强 2：前端交互页
`/sales/meeting-minutes-ai`（菜单"会议纪要AI"）：粘贴/上传 → AI 解读卡片（要点+竞品+清单）→ 选择关联商机/项目 → 一键归档。页面渲染 0 console 错误。文件 `pages/MeetingMinutesAI.jsx` + `salesRoutes.jsx` + 菜单。

### 增强 3：自动派生
确认归档时：
- **回填商机**：`budget_range`（预算）、`acceptance_basis`（关键诉求）、`requirement_maturity`（有技术盲点判 LOW）。
- **派生任务**：`next_actions` + 清单"需获取/需确认"逐条写入项目任务表（stage=PRESALE, status=TODO）。
- 实测：确认后 `created_tasks=19`、`backfilled_opportunity=true`；商机26 成熟度=LOW/预算=200万/需求已回填。

后端文件：`ai_job_service.py`（handler+匹配+抽取）、`sales/activity_minutes.py`（3端点）。

## 三、销售功能重复 去重（分析+清理）

### 已清理
1. **后端 API 4× 重复挂载 → 去重**：`/sales-regions/*`、`/sales-targets/*`、`/sales-teams/*` 是同一 sales router 的兼容 shim 重复挂载。取消这 3 处 `include_router`（前端未调用，零风险）。验证：三前缀路由数归零，`/sales/*` 保留 545 条，移除约 1600 条重复路由注册。（`app/api/v1/api.py`）
2. **前端孤儿重复页 → 重定向**：`/quotations`(QuotationList) → `/cost-quotes/quotes`；`/contracts`(ContractList) → `/sales/contracts`（菜单规范页）。实测重定向生效。（`salesRoutes.jsx`）

### 深入分析后的决策与清理
- **报价（读组件后修正）**：QuoteManagementCenter(菜单页)**内嵌** QuoteManagement+毛利分析+模板，IntelligentQuote 是独立"AI智能报价"——**均非重复，全部保留**。仅把冗余备用路由 `/sales/quotes/management` 重定向到 `/cost-quotes/quotes`（QuoteManagement 仍作为内嵌内容复用）。
- **团队**：SalesTeam(/sales/team) 是"统一入口"，其组织架构Tab 用自绘 OrganizationTree+OrgHierarchyCard；SalesOrganization(615) 是独立组织架构页、功能重叠且仅被路由引用 → **保 SalesTeam，去 SalesOrganization**：`/sales/organization` 重定向到 `/sales/team`。
- 结论：真正"重复的整页"只有 **SalesOrganization**（已重定向），其余是"容器+内嵌"关系（非重复）。

### 死组件文件清理（已备份）
确认仅被路由引用后，删除 3 个已废弃页面（备份于 scratchpad/deleted_pages/）：
- `pages/QuotationList/`（→ /cost-quotes/quotes）
- `pages/ContractList/`（→ /sales/contracts；注意 `components/contract-management/ContractList` 是另一复用组件，保留）
- `pages/SalesAI/SalesOrganization.jsx`（→ /sales/team）
并移除 salesRoutes.jsx 中对应 lazyLoad import。冒烟验证：4 页正常渲染、重定向生效、0 致命错误。
（QuoteManagement 仍被 QuoteManagementCenter 内嵌复用，未删。）
