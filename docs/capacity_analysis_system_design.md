# 产能分析系统设计文档

## 1. 系统概述

产能分析系统是生产管理平台的核心模块,通过设备OEE分析、工人效率分析、产能瓶颈识别、产能预测等功能,帮助企业全面了解和优化生产产能。

### 1.1 核心功能

- **设备OEE分析**: 基于国际标准的OEE(Overall Equipment Effectiveness)计算和分析
- **工人效率分析**: 工人工作效率、质量率、利用率的多维度分析
- **产能瓶颈识别**: 自动识别影响整体产出的瓶颈工位、设备和工人
- **产能预测**: 基于历史数据的线性回归预测,考虑季节性因素
- **多维度对比**: 支持车间、设备、工人、时间段等多维度对比分析
- **产能趋势分析**: 产能随时间的变化趋势
- **产能看板**: 可视化展示整体产能状况
- **产能报告**: 支持汇总报告、详细报告、分析报告,可导出Excel

## 2. 数据模型设计

### 2.1 设备OEE记录表 (equipment_oee_record)

```python
class EquipmentOEERecord:
    # 基础信息
    id: 主键ID
    equipment_id: 设备ID
    workshop_id: 车间ID
    workstation_id: 工位ID
    record_date: 记录日期
    shift: 班次
    
    # 时间数据(分钟)
    planned_production_time: 计划生产时间
    planned_downtime: 计划停机时间
    unplanned_downtime: 非计划停机时间
    operating_time: 运行时间
    
    # 产量数据
    ideal_cycle_time: 理想单件周期时间
    actual_output: 实际产量
    target_output: 目标产量
    qualified_qty: 合格数量
    defect_qty: 不良品数量
    rework_qty: 返工数量
    
    # OEE指标(百分比)
    availability: 可用率
    performance: 性能率
    quality: 合格率
    oee: OEE综合效率
    
    # 损失分析
    availability_loss: 可用性损失
    performance_loss: 性能损失
    quality_loss: 质量损失
```

### 2.2 工人效率记录表 (worker_efficiency_record)

```python
class WorkerEfficiencyRecord:
    # 基础信息
    id: 主键ID
    worker_id: 工人ID
    workshop_id: 车间ID
    workstation_id: 工位ID
    work_order_id: 工单ID
    record_date: 记录日期
    shift: 班次
    
    # 工时数据(小时)
    standard_hours: 标准工时
    actual_hours: 实际工时
    overtime_hours: 加班工时
    break_hours: 休息时间
    idle_hours: 空闲时间
    
    # 产量数据
    completed_qty: 完成数量
    qualified_qty: 合格数量
    defect_qty: 不良数量
    rework_qty: 返工数量
    
    # 效率指标(百分比)
    efficiency: 工作效率
    quality_rate: 合格率
    utilization_rate: 利用率
    overall_efficiency: 综合效率
    
    # 绩效数据
    performance_score: 绩效得分
    attendance_rate: 出勤率
    safety_incidents: 安全事件数
```

## 3. API接口设计

### 3.1 设备OEE分析

**接口**: `GET /production/capacity/oee`

**参数**:
- equipment_id: 设备ID(可选)
- workshop_id: 车间ID(可选)
- start_date: 开始日期
- end_date: 结束日期
- group_by: 分组方式(equipment/workshop/date/detail)

**返回**: OEE分析数据,包含可用率、性能率、合格率、OEE等级

### 3.2 工人效率分析

**接口**: `GET /production/capacity/worker-efficiency`

**参数**:
- worker_id: 工人ID(可选)
- workshop_id: 车间ID(可选)
- start_date: 开始日期
- end_date: 结束日期
- group_by: 分组方式(worker/workshop/date/skill)

**返回**: 工人效率数据,包含效率、质量率、利用率、效率等级

### 3.3 产能瓶颈识别

**接口**: `GET /production/capacity/bottlenecks`

**参数**:
- workshop_id: 车间ID(可选)
- start_date: 开始日期
- end_date: 结束日期
- threshold: 瓶颈阈值

**返回**: 设备瓶颈、工位瓶颈、低效工人列表及改进建议

### 3.4 产能预测

**接口**: `GET /production/capacity/forecast`

**参数**:
- type: 类型(equipment/worker)
- history_days: 历史数据天数
- forecast_days: 预测天数

**返回**: 预测值、置信区间、趋势分析、模型信息

### 3.5 多维度对比

**接口**: `GET /production/capacity/comparison`

**参数**:
- dimension: 对比维度(workshop/equipment/worker/time)
- metric: 对比指标(oee/efficiency/output/quality)
- compare_periods: 是否对比时间段

**返回**: 对比数据、排名、变化趋势

### 3.6 产能利用率

**接口**: `GET /production/capacity/utilization`

**参数**:
- type: 类型(equipment/worker)
- workshop_id: 车间ID(可选)

**返回**: 利用率分析,状态分类(饱和/良好/正常/偏低)

### 3.7 产能趋势

**接口**: `GET /production/capacity/trend`

**参数**:
- type: 类型(oee/efficiency)
- granularity: 粒度(day/week/month)

**返回**: 时间序列数据、趋势分析

### 3.8 OEE计算触发

**接口**: `POST /production/capacity/oee/calculate`

**请求体**:
```json
{
  "equipment_id": 1,
  "record_date": "2026-02-15",
  "planned_production_time": 480,
  "unplanned_downtime": 20,
  "ideal_cycle_time": 2.0,
  "actual_output": 200,
  "qualified_qty": 190
}
```

**返回**: 计算后的OEE数据和等级

### 3.9 产能看板

**接口**: `GET /production/capacity/dashboard`

**返回**: 综合看板数据,包含OEE概览、效率概览、Top设备/工人、瓶颈、趋势

### 3.10 产能报告

**接口**: `GET /production/capacity/report`

**参数**:
- report_type: 报告类型(summary/detailed/analysis)
- format: 输出格式(json/excel)

**返回**: 产能分析报告

## 4. 核心算法

### 4.1 OEE计算(严格遵循国际标准)

```
1. 可用率(Availability) = 运行时间 / 计划生产时间 × 100%
   运行时间 = 计划生产时间 - 计划停机 - 非计划停机

2. 性能率(Performance) = (理想周期时间 × 实际产量) / 运行时间 × 100%
   注: 性能率上限为100%

3. 合格率(Quality) = 合格数量 / 实际产量 × 100%

4. OEE = 可用率 × 性能率 × 合格率
```

**OEE等级**:
- 世界级: ≥ 85%
- 良好: 60% - 85%
- 需改进: < 60%

### 4.2 工人效率计算

```
1. 工作效率 = 标准工时 / 实际工时 × 100%

2. 合格率 = 合格数量 / 完成数量 × 100%

3. 利用率 = (实际工时 - 空闲时间 - 休息时间) / 实际工时 × 100%

4. 综合效率 = 工作效率 × 合格率 × 利用率
```

**效率等级**:
- 优秀: ≥ 120%
- 良好: 100% - 120%
- 正常: 80% - 100%
- 偏低: < 80%

### 4.3 瓶颈识别算法

```python
瓶颈识别标准:
1. 设备瓶颈: 产能利用率 > 阈值(默认80%) 且 影响整体产出
2. 工位瓶颈: 工作负荷最高 且 处理时间最长
3. 工人瓶颈: 平均效率 < 80%

优先级排序:
- 按利用率/影响程度降序
- 提供针对性改进建议
```

### 4.4 产能预测算法

```python
方法: 线性回归 + 季节性调整

1. 线性回归计算趋势:
   斜率 = Σ[(x - x̄)(y - ȳ)] / Σ[(x - x̄)²]
   截距 = ȳ - 斜率 × x̄

2. 季节性因子计算:
   - 按周统计(7天周期)
   - 计算每天相对平均值的因子

3. 预测值 = 线性趋势 × 季节性因子

4. 置信区间 = 预测值 ± 1.96 × 标准差(95%置信度)
```

## 5. 数据聚合策略

### 5.1 按设备聚合
- 平均OEE、可用率、性能率、合格率
- 总产量、合格数、不良数
- 停机时间统计

### 5.2 按车间聚合
- 车间整体OEE
- 设备数量、记录数量
- 总产出

### 5.3 按时间聚合
- 日/周/月粒度
- 趋势计算
- 同比/环比分析

## 6. 性能优化

### 6.1 索引优化
```sql
-- 设备+日期复合索引
CREATE INDEX idx_oee_equipment_date ON equipment_oee_record(equipment_id, record_date);

-- 车间+日期索引
CREATE INDEX idx_oee_workshop ON equipment_oee_record(workshop_id);

-- 效率指标索引
CREATE INDEX idx_worker_eff_efficiency ON worker_efficiency_record(efficiency);
```

### 6.2 查询优化
- 使用聚合查询减少数据传输
- 分页查询大数据集
- 使用缓存存储常用统计数据

### 6.3 计算优化
- 后台异步计算OEE和效率
- 预计算常用统计指标
- 使用批量插入提高性能

## 7. 扩展性设计

### 7.1 自定义指标
- 支持用户自定义KPI指标
- 灵活的公式配置

### 7.2 多工厂支持
- 支持跨工厂数据对比
- 集团级产能分析

### 7.3 实时监控
- 实时OEE看板
- 异常实时告警

## 8. 安全性考虑

- 数据访问权限控制
- 敏感数据脱敏
- 操作日志记录
- 审计追踪

## 9. 集成接口

### 9.1 与MES系统集成
- 实时获取设备运行数据
- 自动计算OEE

### 9.2 与ERP系统集成
- 同步标准工时数据
- 同步物料信息

### 9.3 与BI系统集成
- 提供数据接口
- 支持自定义报表

## 10. 未来规划

- AI智能预测
- 自动优化建议
- 移动端应用
- 实时大屏展示
