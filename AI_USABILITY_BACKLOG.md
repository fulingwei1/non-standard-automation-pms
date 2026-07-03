# AI 提效 / 易用性增强 + 管理员 AI 配置（本轮目标）

> 目标：深挖 ≥10 个"提效/易用"AI 点并实现 + 管理员后台可视化配置 AI 接入。
> 原则延续：少录入、数据带出/AI 计算、功能好用。

## ✅ 管理员后台 AI 接入配置（可视化 + 一键测试）
- 表 `ai_settings`(key/value) 覆盖 env；`AIClientService` 启动读 DB（`load_ai_settings`，30s 缓存，best-effort 回退 env）。
- 端点 `/admin/ai-config` GET(脱敏读取)/PUT(保存,敏感字段留空不改,即时生效)/POST test(真实调用测连接,返回模型/耗时/样例)。仅管理员(is_superuser/role含admin)。
- 前端页 `/admin/ai-config`：表单 + 🔌测试连接 + 来源标识(后台配置/环境变量)。菜单"AI接入配置"。
- 实测：保存生效、测试连接 1.1s 连通 qwen3-coder-plus。

## ✅ 11 个提效/易用 AI 点（均已实现+实测，端点前缀 /ai-copilot）
| # | 能力 | 端点 | 价值 |
|---|---|---|---|
| 1 | **全局 AI 命令栏 (Cmd/Ctrl+K)** | POST command | 自然语言导航/搜索/问答，全站一处直达（"打开商机列表"→跳转）。UX 天花板 |
| 2 | **全局语义搜索** | GET search | 跨商机/客户/项目/模块统一搜，带路由直达 |
| 3 | **日报/周报自动生成** | GET report | 从我的活动记录自动成文，销售/工程师零填写 |
| 4 | **长文本一键摘要** | POST summarize | 纪要/合同/需求→3句摘要+要点+待办 |
| 5 | **中英互译(技术语境)** | POST translate | 图纸/邮件/方案专业术语翻译，服务海外客户 |
| 6 | **邮件/沟通代写** | POST draft | 催款/跟进/道歉一键成稿 |
| 7 | **自然语言→筛选条件** | POST nl-filter | "金额>100万且没做售前评估"→结构化过滤 |
| 8 | **我的一天(待办AI聚合)** | GET my-day | 个人当日最该做的事，数据主动找人 |
| 9 | **智能表单填充** | POST autofill | 一句线索→预填客户/商机/报价字段 |
| 10 | **文本润色/规范化** | POST polish | 口语→专业规范，适合写入 CRM/汇报 |
| 11 | **操作助手(怎么做)** | POST how-to | 系统内 how-to 向导，降低上手门槛 |

## 前端落地
- **全局命令栏** 挂载于 MainLayout（全站 Cmd/Ctrl+K 唤起）。
- **AI 助手页**(/ai/assistant) 扩展：我的一天 + 图纸理解 + 数字员工问答 + 文本助手(摘要/翻译/润色/邮件) + 日报周报。
- **AI 接入配置页**(/admin/ai-config)。
- 均加入侧边栏菜单。

## ✅ 日报/周报自动推送（定时任务）
- 任务 `push_daily_reports/push_weekly_reports`（app/utils/scheduled_tasks/ai_report_tasks.py）：扫当日/本周有活动记录的用户 → AI 生成个人日报/周报 → 站内通知(notifications, 链接/ai/assistant)。**幂等**(同人同天只推一次)，AI 失败兜底拼接。
- 定时：日报每天 18:30、周报每周五 17:30（scheduler_config，可 DB 覆盖时间）。已在调度器注册。
- 管理员手动立即触发：POST /admin/ai-config/push-reports?period=day|week。
- 实测：触发→推送1位、再触发→0(幂等)、通知落库含三段式AI日报。

## ✅ 日报推送三项增强（本轮）
1. **多通道推送**：系统站内(必达) + 邮件 + 企微。复用 UnifiedNotificationService(EmailChannelHandler/WeChatChannelHandler)，用户启用则发、未配置自动跳过。
2. **覆盖 PM/工程师**：数据源从"仅销售活动"扩为 **销售活动(customer_communications) + 任务进展(tasks)**，AI 融合成一份日报（实测同时含"客户拜访"+"任务进度60%"）。
3. **管理端调时间/开关**：GET/PUT /admin/ai-config/report-schedule（存 SchedulerTaskConfig + **热重排 apscheduler job**，实测改到19:00即时生效）；配置页有日报/周报开关+时间+立即推送。

## ✅ 表单填充嵌入新建对话框（2026-07-03）
- 可复用组件 `AutofillBar`（frontend/src/components/ai/AutofillBar.jsx）：一句话线索 → `/ai-copilot/autofill` → `mergeAutofill` 只填空位、不覆盖已填、嵌套 requirement 递归合并、忽略 AI 多余键。
- 已嵌入：新建商机（/sales/opportunities）、新建客户（/sales/customers）两个主销售入口对话框。
- 后端 autofill schema 扩充对齐表单字段（商机含 requirement 嵌套：产品对象/节拍/接口/现场约束/验收标准；客户含简称/联系人/电话/地址），并加"没提到的留空、不编造"约束。
- 验证：vitest 6/6（mergeAutofill 3 + 组件 3）；真实 AI 实测商机线索带出金额 1200000/节拍 18/验收误判率<0.3%，客户不编造电话；真实浏览器 5/5（`.gstack/qa-reports/ai-autofill-sweep-20260702222128.json`，0 console/page/api error）。

## ✅ 命令栏执行动作（2026-07-03）
- `/ai-copilot/command` 意图扩为 `navigate|search|answer|action`；action 白名单 `create_opportunity`/`create_customer`（只打开预填对话框、不直接写库，用户确认后才创建）。
- 链路：Cmd/Ctrl+K →"新建商机 给宁德时代做视觉检测…"→ AI 提取业务线索 → 跳转 `?ai_hint=` → 页面自动开新建对话框 → AutofillBar 自动执行 AI 预填（同一线索只跑一次）。
- 验证：真实浏览器 6/6（`.gstack/qa-reports/ai-command-action-sweep-20260703001213.json`，商机名/金额/公司全称均自动填出，导航意图回归正常，0 错误）；vitest 7/7。

## ✅ 多模型/多厂商配置页切换（2026-07-03）
- 新设置 `AI_DEFAULT_MODEL`：模型前缀决定厂商路由（qwen*→阿里百炼 / glm*→智谱 / gpt*→OpenAI / kimi*→月之暗面），未配置目标厂商 Key 时自动回退通义千问。
- 配置页字段分组（通用/阿里百炼/其他厂商），新增智谱/OpenAI/Kimi Key（脱敏）；默认模型带预设快捷按钮+datalist；测试连接支持选模型单测。
- 实测：切 glm-5 即时生效（default_model=glm-5，无智谱 Key 优雅回退 qwen 仍连通）；指定 qwen3-coder-plus 测试 1.0s 连通；复位后回落 qwen3.7-plus。

## 后续可继续增强
- 语义搜索接向量检索(对应 ROADMAP F4，大项单独立项)；表单填充可再扩到报价/线索等更多新建入口；命令栏动作可扩到"记录活动/申请售前支持"等；邮件/企微渠道需配 SMTP/企微 webhook 后自动启用。
