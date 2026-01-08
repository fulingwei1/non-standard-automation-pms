# 短期执行指南

> 本指南作为 PMO / 研发团队的操作说明，串联所有短期执行产物，确保从行动拆解 → 燃尽 → 里程碑 → 风险 → 日常跟踪形成闭环。

## 1. 文档索引

| 文档 | 作用 | 更新频率 |
| --- | --- | --- |
| `docs/SHORT_TERM_ACTION_BOARD.md` | 行动主题 → Story 拆解，含 Owner / SP / 状态 | Story 状态变化即更新 |
| `docs/SHORT_TERM_BURNDOWN_PLAN.md` | 总体行动拆解 + 6 周燃尽计划 | 基线调整时更新 |
| `docs/MILESTONE_CHART.md` | ASCII 甘特图，直观展现 M0-M6 | 计划调整时更新 |
| `docs/MILESTONE_REVIEW_CHECKLIST.md` | 每个里程碑的进入条件、检查项、输出物 | 里程碑前后更新 |
| `docs/BURNDOWN_TRACKING_LOG.md` | 周度计划 vs 实际 SP、偏差说明 | 每周例会 |
| `docs/RISK_REGISTER.md` | 风险及缓解方案 | 风险状态变化时 |

## 2. 执行流程
1. **启动 (W0)**：阅读 `SHORT_TERM_BURNDOWN_PLAN`，确认行动主题与里程碑；将 `SHORT_TERM_ACTION_BOARD` 中的 Story 导入看板。
2. **开发周期 (W1-W5)**：
   - 每周例会前收集各 Story 的实际进度，例会时更新 `SHORT_TERM_ACTION_BOARD` & `BURNDOWN_TRACKING_LOG`。
   - 里程碑前准备 `MILESTONE_REVIEW_CHECKLIST` 中的材料，评审后将结论回写到相应文档。
   - 关注 `RISK_REGISTER`，对触发条件及时处理。
3. **收尾 (W6)**：结合 `MILESTONE_CHART` 和 `BURNDOWN_TRACKING_LOG` 做燃尽复盘，输出上线材料。

## 3. 角色职责
- **PMO**：维护文档、主持里程碑审阅、确保风险登记；负责更新 `BURNDOWN_TRACKING_LOG` 和 `RISK_REGISTER`。
- **Backend / Frontend / Issue / Data Owner**：对口更新所在主题的 Story 状态与交付物；在里程碑前提供必要材料。
- **QA/运维**：在 M2/M4/M6 里程碑中提供验证报告与上线支持。

## 4. 工具化建议
- 将 `SHORT_TERM_ACTION_BOARD` 导入 Jira/飞书项目，保持字段一致。
- 使用自动化脚本从看板统计 SP 并写回 `BURNDOWN_TRACKING_LOG`，减少人工误差。
- 将里程碑材料（PPT/录屏/报告）放入统一共享盘，并在文档中附链接。

## 5. 追踪指标
- **燃尽速度**：每周消耗的 SP；参考 `SHORT_TERM_BURNDOWN_PLAN` 的计划曲线。
- **里程碑通过率**：按 M0-M6 统计是否按期通过，记录原因。
- **风险关闭率**：`RISK_REGISTER` 中 Open → Mitigating → Closed 的数量。

## 6. 变更流程
- 新增/修改行动项：需在例会上讨论并更新 `SHORT_TERM_ACTION_BOARD` 与燃尽基线。
- 里程碑延迟：在 `BURNDOWN_TRACKING_LOG` 的“阻塞/说明”中记录，同时在 `MILESTONE_CHART` 添加脚注。
- 风险升级：若触发条件满足，立即在 `RISK_REGISTER` 标记并通知负责人。

> 按此指南操作，可确保短期 P0 行动在 6 周内可衡量、可监管、可复盘。
