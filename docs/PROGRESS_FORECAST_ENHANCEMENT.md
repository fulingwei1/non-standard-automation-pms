# 进度预测增强方案

更新时间：2026-01-07
负责模块：进度跟踪/智能预测

## 1. 现有基础
- 已有任务、依赖、进度日志、基线等 ORM 模型，可获取计划/实际日期、权重与历史填报。
- `/progress/projects/{id}/progress-forecast` 基于线性速度估算未来完工；未引入资源负载或跨项目经验。
- `/progress/projects/{id}/dependency-check` 可识别循环依赖、时序冲突，并触发通知。

## 2. 数据资产梳理
| 数据源 | 关键字段 | 备注 |
| --- | --- | --- |
| `tasks` | 计划/实际时间、权重、owner、stage、status | 支撑特征工程，如阶段、任务类型、负责人负载 |
| `progress_logs` | progress_percent、updated_at、updated_by | 可构建进度曲线、计算速度、识别停滞 |
| `project_payment_plans` / `milestones` | 计划节点、金额、触发条件 | 用于关联“里程碑完成 vs. 收款”预测 |
| `TaskUnified`/工时表 | actual_hours、estimated_hours | 可度量资源投入与剩余工时 |
| `Project` | type、industry、priority、历史成功率 | 训练跨项目模型所需的上下文 |

## 3. 预测能力升级路线
1. **资源负载驱动的规则模型（短期）**
   - 引入 `actual_hours / estimated_hours`、负责人进行中任务数、阶段权重等特征，调整 `rate_per_day`。
   - 若负责人当前有 N 个任务并且历史效率偏低，则下调预测速度；里程碑关键任务可强制提高权重。
   - 输出：更贴近资源约束的滚动预测。

2. **相似项目回归模型（中期）**
   - 训练回归模型（如 XGBoost/LightGBM），输入项目维度特征（规模、行业、里程碑计划 vs. 实际、关键任务进度），输出整体剩余周期估计。
   - 需要准备：历史已完成项目数据集（至少数十个项目），划分训练/验证集，指标可选 MAPE、RMSE。
   - 部署方式：
     - 离线批量训练，模型文件存储于对象存储/数据库。
     - 推理环节在 `/progress-forecast` 中加载模型，根据当前项目特征输出 `predicted_completion_date_ml` 供前端展示。

3. **序列预测（长期）**
   - 针对关键项目引入时间序列模型（Prophet、LSTM）分析进度曲线，判断“进度卡点”与“恢复速度”。
   - 可结合阶段划分：对 S3/S4 阶段单独建模，捕捉阶段性特征。

## 4. 数据与工程要求
- **数据集**：整理 `projects` + `tasks` + `progress_logs` + `milestones` 历史快照；必要时创建 ETL 任务写入 `analytics_project_progress`。
- **特征管道**：
  1. 任务级：进度速度、停滞天数、剩余工时、依赖数量。
  2. 项目级：阶段分布、关键任务完成比、资源投入（人员数×工时）。
- **训练流程**：
  - Notebook/脚本采用 `scikit-learn` + `lightgbm`，输出模型及特征标准化配置。
  - 结果写入 `models/progress_forecast/model.pkl`，并记录版本号。
- **推理服务**：
  - 在 `app/services/progress_forecast_service.py` 中封装 `load_model()` 与 `predict_completion(project_id)`。
  - 失败时回退到现有规则模型，保证接口稳定。

## 5. 指标与验证
- **准确度**：过去项目的预测完工日期 vs. 实际完工日期，目标 MAPE < 15%。
- **预警提前量**：延迟项目中，有多少在真实延迟发生前 7 天被预测出来。
- **用户反馈**：在项目驾驶舱中展示“模型版本+置信度”，收集 PM 对预测的主观评价。

## 6. 后续工作拆解
1. 数据准备：编写 SQL/ETL 生成历史项目进度特征表。
2. 规则模型增强：在现有 `/progress-forecast` 中引入资源负载、阶段系数。
3. 模型实验：基于历史数据训练基线回归模型，评估指标。
4. 推理集成：在 API 层加载模型（或调用独立服务），输出 `ml_predicted_completion_date`、`ml_confidence`。
5. 可视化：前端驾驶舱展示“ML 预测 vs. 规则预测”差异，并提供反馈入口。

---
此文档用于指导后续 ML 预测的实施，若需要创建默认 ETL 或模型脚本，可在 `analytics/` 目录新增对应任务。
