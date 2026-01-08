# 短期行动任务板

> 面向 1-2 个月内的 P0 行动，将每个主题拆分为可跟踪的任务卡，可直接在看板/Jira 中复用。

## 1. 完善后台定时服务（Owner：Backend Platform / Liang）

| Story | 描述 | 依赖 | 预估 | 状态 | 备注 |
| --- | --- | --- | --- | --- | --- |
| S1 | 健康度指标补齐：收集缺失字段、更新 `HealthCalculator`、同步验收脚本 | 数据库字段确认 | 5 SP | Planned | 入库 KPI：上线前回归通过 |
| S2 | 定时任务盘点与监控：生成 24 个任务清单、配置 APScheduler 日志、Grafana 面板 | APScheduler、日志系统 | 3 SP | Planned | 与运维协作 |
| S3 | 预警通知链路增强：补齐短信/企微推送、失败重试策略 | 通讯服务 | 2 SP | Planned | 输出测试报告 |
| S4 | 回归脚本扩展：扩展 `test_scheduled_services.py`，含数据库模拟、通知模拟 | 测试账号 | 2 SP | Planned | 交付自动化脚本 |
| S5 | Scheduler 健康监控：增加任务队列堆积/异常报警，提供 Dashboard 截图 | 监控平台 | 2 SP | Planned | M2 审阅材料 |

**验收标准**：Scheduler 回归日志 <1% 失败率；M2 审阅材料齐备。

## 2. 完善前端页面（Owner：Frontend Team / Chen）

| Story | 描述 | 依赖 | 预估 | 状态 | 备注 |
| --- | --- | --- | --- | --- | --- |
| F1 | 生产计划视图：展示甘特/工位，含筛选、导出 | 进度 API | 3 SP | Planned | 与 PM 评审交互 |
| F2 | 生产执行+报工视图：支持状态更新、批量审批 | 报工 API | 3 SP | Planned | 移动端复用组件 |
| F3 | 生产异常视图：展示报警、指派、处理记录 | 异常 API | 2 SP | Planned | 与预警服务联动 |
| F4 | 验收记录 & 附件页：多标签布局、附件预览 | 验收 API | 2 SP | Planned | 需权限控制 |
| F5 | 验收审批链视图：展示流程、节点意见 | Flow API | 1 SP | Planned | 同 `frontend/src/pages/RdProjectDocuments.jsx` 组件 |
| F6 | 移动端适配：关键页面响应式、触控手势 | UI 组件库 | 1 SP | Planned | 提供 Demo 视频 |
| F7 | 前端日志/监控：集成 Sentry/埋点，为 UAT 提供数据 | 监控平台 | 1 SP | Planned | 支撑 M4 审阅 |

**验收标准**：M3 评审通过，UAT 环境可演示；移动端样例连通 QA。

## 3. 完善问题管理模块（Owner：Issue Squad / Xu）

| Story | 描述 | 依赖 | 预估 | 状态 | 备注 |
| --- | --- | --- | --- | --- | --- |
| I1 | 批量操作后端：新增批量分配/状态/标签接口 | `issues.py` | 2 SP | Planned | Swagger 更新 |
| I2 | 批量操作前端：列表勾选、操作面板、权限控制 | API 完成 | 2 SP | Planned | 需 Loading/Undo |
| I3 | 统计分析：趋势图、责任人热力图、导出 | BI 数据 | 3 SP | Planned | 优先桌面端 |
| I4 | 风险提醒集成：在工作台显示逾期/阻塞提示 | Scheduler 数据 | 1 SP | Planned | 需 real-time 提示 |
| I5 | 问题数据质量巡检脚本：定期检查缺失字段、异常状态 | 数据库 | 1 SP | Planned | 支撑告警准确性 |

**验收标准**：工作台展示实时统计；批量操作提供操作记录。

## 4. 补充缺失数据库表（Owner：Data Team / Wang）

| Story | 描述 | 依赖 | 预估 | 状态 | 备注 |
| --- | --- | --- | --- | --- | --- |
| D1 | 缺料调拨记录表 DDL + 迁移 + DAO | 业务需求 | 2 SP | Planned | 提供回填脚本 |
| D2 | 缺料替代策略表 DDL + 迁移 + DAO | 业务需求 | 1 SP | Planned | 与缺料 API 联动 |
| D3 | 研发立项/评审/资源等 6 表建模 | 研发业务 | 4 SP | Planned | 需数据字典同步 |
| D4 | 数据一致性脚本：缺料 & 研发样例数据 | 现有数据 | 1 SP | Planned | UAT 校验使用 |
| D5 | 数据字典更新与评审材料整理 | `docs/数据字典.md` | 1 SP | Planned | 支撑 M5 审阅 |

**验收标准**：所有迁移在 Staging/Prod 脚本演练通过，`docs/数据字典.md` 更新。

## 5. 阻塞 / 风险池

| 风险 | 影响 | owner | 计划对策 | 跟踪 |
| --- | --- | --- | --- | --- |
| 通知渠道 SDK 版本落后 | 预警通知上线延迟 | Backend | 升级 SDK，影子环境验证 | _待填_ |
| 进度/验收 API 需求频繁变动 | 前端迭代滑期 | PM & Frontend | M1 建立接口冻结窗口 | _待填_ |
| 数据表权限定义不完整 | 数据字典评审滞后 | Data | 与安全组共评权限矩阵 | _待填_ |

## 6. 使用建议
1. 将此表复制到项目管理工具，按 Story 创建卡片并同步状态。
2. 每周例会更新 Story 状态与风险池，保持与 `docs/BURNDOWN_TRACKING_LOG.md` 里程碑一致。
3. 里程碑评审时引用本文件核对 Story 是否满足进入/退出条件。
