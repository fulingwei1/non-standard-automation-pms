# 生产排程优化最佳实践

## 1. 排程前准备

### 1.1 数据完整性检查

在开始排程前，确保以下数据完整:

✅ **工单信息**
- 工单编号、任务名称
- 标准工时(必需)
- 计划开始/结束日期
- 优先级设置

✅ **资源信息**
- 设备状态为 IDLE 或 RUNNING
- 工人状态为 ACTIVE
- 车间、工位信息完整

✅ **技能匹配**
- 工序定义清晰
- 工人技能认证记录
- 技能等级设置

### 1.2 约束条件设置

```json
{
  "consider_worker_skills": true,      // 推荐开启
  "consider_equipment_capacity": true, // 推荐开启
  "allow_overtime": false,             // 根据实际情况
  "max_delay_hours": 4                 // 紧急插单允许延迟
}
```

## 2. 算法选择指南

### 2.1 选择依据

| 场景 | 推荐算法 | 理由 |
|------|----------|------|
| 日常排程(< 50工单) | GREEDY | 速度快，效果好 |
| 周排程(50-100工单) | HEURISTIC | 平衡速度和质量 |
| 月排程(100-200工单) | HEURISTIC | 需要更优解 |
| 超大规模(200+工单) | 待开发 | 需要GENETIC算法 |
| 紧急插单 | GREEDY | 实时性要求高 |

### 2.2 优化目标选择

**TIME模式**: 最短完成时间
```json
{
  "algorithm": "GREEDY",
  "optimize_target": "TIME"
}
```
适用场景: 赶工期、订单交期紧张

**RESOURCE模式**: 最高资源利用率
```json
{
  "algorithm": "HEURISTIC",
  "optimize_target": "RESOURCE"
}
```
适用场景: 资源有限、需要充分利用设备和人力

**BALANCED模式**: 平衡模式(推荐)
```json
{
  "algorithm": "HEURISTIC",
  "optimize_target": "BALANCED"
}
```
适用场景: 大多数情况，综合考虑各项指标

## 3. 排程流程最佳实践

### 3.1 推荐工作流程

```
1. 数据准备
   ↓
2. 生成排程 (POST /schedule/generate)
   ↓
3. 预览检查 (GET /schedule/preview)
   ↓
4. 冲突检测 (GET /schedule/conflicts)
   ↓
5. 手动调整 (POST /schedule/adjust) [可选]
   ↓
6. 方案对比 (GET /schedule/comparison) [可选]
   ↓
7. 确认排程 (POST /schedule/confirm)
   ↓
8. 导出甘特图 (GET /schedule/gantt)
```

### 3.2 完整示例

```python
import requests

# 1. 生成排程
response = requests.post('/api/v1/production/schedule/generate', json={
    "work_orders": [1, 2, 3, 4, 5],
    "start_date": "2026-02-17T08:00:00",
    "end_date": "2026-02-28T18:00:00",
    "algorithm": "HEURISTIC",
    "optimize_target": "BALANCED",
    "consider_worker_skills": True,
    "consider_equipment_capacity": True
})

data = response.json()
plan_id = data['plan_id']
print(f"✅ 排程生成成功，方案ID: {plan_id}")
print(f"   成功: {data['success_count']}, 失败: {data['failed_count']}")
print(f"   评分: {data['score']}")

# 2. 预览检查
preview = requests.get(f'/api/v1/production/schedule/preview?plan_id={plan_id}')
preview_data = preview.json()

if preview_data['warnings']:
    print("⚠️  警告信息:")
    for warning in preview_data['warnings']:
        print(f"   - {warning}")

# 3. 检查冲突
conflicts = requests.get(f'/api/v1/production/schedule/conflicts?plan_id={plan_id}')
conflicts_data = conflicts.json()

if conflicts_data['has_conflicts']:
    print(f"❌ 检测到 {conflicts_data['total_conflicts']} 个冲突")
    
    # 高优先级冲突需要处理
    critical_conflicts = [c for c in conflicts_data['conflicts'] 
                          if c['severity'] in ['HIGH', 'CRITICAL']]
    if critical_conflicts:
        print("   需要解决的高优先级冲突:")
        for c in critical_conflicts:
            print(f"   - {c['conflict_description']}")
        
        # 调整排程解决冲突
        # ...
else:
    print("✅ 无冲突")

# 4. 确认排程
confirm = requests.post(f'/api/v1/production/schedule/confirm?plan_id={plan_id}')
if confirm.status_code == 200:
    print("✅ 排程已确认")
else:
    print(f"❌ 确认失败: {confirm.json()['detail']}")
```

## 4. 冲突处理策略

### 4.1 冲突分类处理

**CRITICAL (严重)**
- 立即处理，必须解决
- 示例: 产能严重超限
- 处理: 增加资源或拆分工单

**HIGH (高)**
- 优先处理，建议解决
- 示例: 设备时间冲突
- 处理: 调整时间或更换设备

**MEDIUM (中)**
- 可以容忍，建议优化
- 示例: 工人时间冲突
- 处理: 调整工人分配

**LOW (低)**
- 可接受，记录即可
- 示例: 技能匹配度不高
- 处理: 无需处理或后续优化

### 4.2 自动解决冲突

```python
# 调整排程时自动解决冲突
response = requests.post('/api/v1/production/schedule/adjust', json={
    "schedule_id": 123,
    "adjustment_type": "TIME_CHANGE",
    "new_start_time": "2026-02-18T08:00:00",
    "reason": "解决设备冲突",
    "auto_resolve_conflicts": True  # 开启自动解决
})
```

### 4.3 手动解决流程

```python
# 1. 获取冲突详情
conflicts = get_conflicts(plan_id=1001)

for conflict in conflicts['conflicts']:
    if conflict['severity'] == 'HIGH':
        # 2. 获取冲突的两个排程
        schedule1 = get_schedule(conflict['schedule_id'])
        schedule2 = get_schedule(conflict['conflicting_schedule_id'])
        
        # 3. 决策: 调整哪个排程
        if schedule1['priority_score'] > schedule2['priority_score']:
            # 调整优先级较低的
            adjust_schedule(
                schedule_id=schedule2['id'],
                new_start_time=schedule1['scheduled_end_time']
            )
        else:
            adjust_schedule(
                schedule_id=schedule1['id'],
                new_start_time=schedule2['scheduled_end_time']
            )
```

## 5. 紧急插单最佳实践

### 5.1 插单前评估

```python
# 1. 评估影响
preview = requests.get(f'/api/v1/production/schedule/preview?plan_id={current_plan_id}')

# 2. 检查是否有足够的缓冲时间
if preview['statistics']['equipment_utilization'] > 0.9:
    print("⚠️  设备利用率已很高，插单可能导致大量延迟")
    
    # 考虑:
    # - 是否真的紧急?
    # - 是否可以加班?
    # - 是否可以外包?
```

### 5.2 插单操作

```python
response = requests.post('/api/v1/production/schedule/urgent-insert', json={
    "work_order_id": 999,
    "insert_time": "2026-02-17T14:00:00",  // 希望的插入时间
    "max_delay_hours": 4,                  // 允许其他工单延迟的最大时长
    "auto_adjust": True,                   // 自动调整其他排程
    "priority_override": True              // 覆盖优先级
})

data = response.json()
if data['success']:
    print(f"✅ 紧急插单成功")
    print(f"   调整了 {len(data['adjusted_schedules'])} 个排程")
    
    # 检查被调整的排程
    for adj_schedule in data['adjusted_schedules']:
        print(f"   - 工单 {adj_schedule['work_order_id']} 延后")
else:
    print(f"❌ 插单失败: {data['message']}")
```

### 5.3 插单后验证

```python
# 1. 重新检查冲突
conflicts = get_conflicts(plan_id=plan_id)

# 2. 查看影响的工单是否超期
for schedule in adjusted_schedules:
    work_order = get_work_order(schedule['work_order_id'])
    if schedule['scheduled_end_time'] > work_order['plan_end_date']:
        print(f"⚠️  工单 {work_order['work_order_no']} 可能延期")
        # 通知相关人员
        notify_stakeholders(work_order)
```

## 6. 性能优化建议

### 6.1 批量排程

**不推荐**: 逐个工单排程
```python
for work_order_id in work_orders:
    generate_schedule(work_orders=[work_order_id])  # ❌ 慢
```

**推荐**: 批量排程
```python
generate_schedule(work_orders=work_order_ids)  # ✅ 快
```

### 6.2 时间窗口设置

```python
# 合理的时间窗口
{
    "start_date": "2026-02-17T08:00:00",
    "end_date": "2026-02-28T18:00:00"  // 2周时间窗口
}

# 避免过长的时间窗口
{
    "end_date": "2026-06-30T18:00:00"  // ❌ 6个月太长
}
```

### 6.3 分阶段排程

对于大量工单(200+)，建议分阶段:

```python
# 阶段1: 本周紧急工单
week1_orders = get_urgent_orders(week=1)
plan1 = generate_schedule(work_orders=week1_orders)

# 阶段2: 下周工单
week2_orders = get_orders(week=2)
plan2 = generate_schedule(work_orders=week2_orders)

# 阶段3: 未来两周工单
future_orders = get_orders(week_range=(3, 4))
plan3 = generate_schedule(work_orders=future_orders)
```

## 7. 监控与维护

### 7.1 关键指标监控

```python
# 定期检查排程质量
def monitor_schedule_quality(plan_id):
    preview = get_schedule_preview(plan_id)
    
    metrics = preview['statistics']
    
    # 交期达成率
    if metrics['completion_rate'] < 0.8:
        alert("交期达成率过低", metrics['completion_rate'])
    
    # 设备利用率
    if metrics['equipment_utilization'] < 0.6:
        alert("设备利用率偏低", metrics['equipment_utilization'])
    
    # 冲突数量
    if metrics['total_conflicts'] > 0:
        alert("存在未解决冲突", metrics['total_conflicts'])
```

### 7.2 调整记录追踪

```python
# 查看排程历史
history = requests.get(f'/api/v1/production/schedule/history?plan_id={plan_id}')

# 分析调整频率
adjustments = history.json()['adjustments']
print(f"总调整次数: {len(adjustments)}")

# 识别频繁调整的工单
frequent_changes = {}
for adj in adjustments:
    schedule_id = adj['schedule_id']
    frequent_changes[schedule_id] = frequent_changes.get(schedule_id, 0) + 1

# 超过3次调整的需要关注
for schedule_id, count in frequent_changes.items():
    if count > 3:
        print(f"⚠️  排程 {schedule_id} 已调整 {count} 次")
```

## 8. 常见问题与解决方案

### Q1: 排程生成速度慢

**原因**: 
- 工单数量过多
- 资源数据未优化

**解决**:
```python
# 1. 筛选有效工单
active_orders = [wo for wo in work_orders if wo.status == 'PENDING']

# 2. 筛选可用资源
available_equipment = [eq for eq in equipment if eq.is_active and eq.status == 'IDLE']

# 3. 使用更快的算法
{
    "algorithm": "GREEDY",  # 而不是 HEURISTIC
    "optimize_target": "TIME"
}
```

### Q2: 冲突数量过多

**原因**:
- 资源不足
- 工单优先级设置不合理
- 时间窗口过紧

**解决**:
```python
# 1. 检查资源负载
preview = get_preview(plan_id)
if preview['statistics']['equipment_utilization'] > 0.95:
    # 增加设备或扩大时间窗口
    pass

# 2. 调整优先级
# 避免过多 URGENT 优先级

# 3. 允许加班
{
    "allow_overtime": True
}
```

### Q3: 技能匹配率低

**原因**:
- 工人技能认证不完整
- 技能要求过于严格

**解决**:
```python
# 1. 更新工人技能
update_worker_skills()

# 2. 降低技能匹配要求
{
    "consider_worker_skills": False  # 临时关闭
}

# 3. 安排培训
identify_skill_gaps()
schedule_training()
```

## 9. 最佳实践检查清单

### 排程前
- [ ] 工单数据完整(工单号、工时、交期)
- [ ] 设备状态检查(可用、维护中)
- [ ] 工人在岗情况确认
- [ ] 技能认证记录更新
- [ ] 确定优先级策略

### 排程中
- [ ] 选择合适的算法
- [ ] 设置合理的时间窗口
- [ ] 开启必要的约束检查
- [ ] 设置优化目标

### 排程后
- [ ] 预览排程结果
- [ ] 检查冲突情况
- [ ] 验证关键指标(交期达成率、利用率)
- [ ] 必要时进行手动调整
- [ ] 确认排程
- [ ] 导出甘特图
- [ ] 通知相关人员

### 运行中
- [ ] 监控执行进度
- [ ] 处理紧急插单
- [ ] 记录调整原因
- [ ] 定期回顾优化

## 10. 总结

遵循以上最佳实践，可以:

✅ 提高排程质量和效率
✅ 减少资源冲突
✅ 提升交期达成率
✅ 优化资源利用率
✅ 降低人工调度工作量

**核心原则**:
1. 数据质量第一
2. 选择合适的算法
3. 冲突及时处理
4. 持续监控优化
