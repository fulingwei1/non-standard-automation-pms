# 生产排程算法设计文档

## 1. 概述

生产排程优化引擎旨在为非标自动化设备制造提供智能化的生产排程解决方案，通过算法自动化排程，提高生产效率和资源利用率。

### 1.1 核心目标

- **自动化排程**: 根据工单、资源、约束条件自动生成排程方案
- **多目标优化**: 平衡交期、资源利用率、成本等多个目标
- **实时调整**: 支持紧急插单和排程动态调整
- **冲突检测**: 自动识别资源冲突并提供解决建议

### 1.2 关键特性

- ✅ 考虑设备产能约束
- ✅ 考虑工人技能匹配
- ✅ 支持多种优先级策略
- ✅ 紧急插单优化
- ✅ 资源冲突自动检测
- ✅ 排程方案评分与对比

## 2. 算法设计

### 2.1 贪心排程算法 (GREEDY)

**策略**: 局部最优选择

#### 算法流程

```python
1. 工单排序:
   - 优先级: URGENT > HIGH > NORMAL > LOW
   - 交期: plan_end_date (升序)
   - 工单号: work_order_no

2. 资源时间表初始化:
   equipment_timeline = {}
   worker_timeline = {}

3. 对每个工单:
   a. 选择最优设备:
      - 如果工单指定设备，使用指定设备
      - 否则，选择同车间、最空闲的设备
   
   b. 选择最优工人:
      - 如果工单指定工人，使用指定工人
      - 如果需要技能匹配，筛选具备该技能的工人
      - 选择最空闲的工人
   
   c. 计算最早开始时间:
      - 检查设备和工人的时间表
      - 找到第一个满足时长要求的空闲时间段
      - 考虑工作时间窗口 (08:00-18:00)
   
   d. 创建排程记录:
      - 记录开始和结束时间
      - 更新资源时间表
      - 计算优先级评分
```

#### 时间复杂度

- 工单排序: O(n log n)
- 资源选择: O(m * k)，m为设备/工人数量，k为已有排程数量
- 总体: O(n * m * k)

对于100个工单，20个设备，50个工人，复杂度约为 O(100,000) 操作，可在1秒内完成。

#### 优点

- 实现简单，易于理解和调试
- 执行速度快，适合实时排程
- 对于优先级明确的场景效果好

#### 缺点

- 可能陷入局部最优
- 对资源利用率优化不够充分

### 2.2 启发式排程算法 (HEURISTIC)

**策略**: 贪心 + 局部优化

#### 算法流程

```python
1. 使用贪心算法生成初始排程

2. 局部优化(迭代):
   for iteration in range(max_iterations):
       improved = False
       
       for i, j in all_schedule_pairs:
           if should_swap(schedule_i, schedule_j):
               swap(schedule_i, schedule_j)
               improved = True
       
       if not improved:
           break

3. 交换规则:
   - 高优先级工单排在前面
   - 减少总等待时间
   - 提高资源利用率
```

#### 优化目标

| 目标 | 描述 | 权重 |
|------|------|------|
| 交期达成率 | 在计划日期内完成的工单比例 | 25% |
| 设备利用率 | 设备工作时间 / 总可用时间 | 15% |
| 工人利用率 | 工人工作时间 / 总可用时间 | 10% |
| 技能匹配率 | 工人技能与工序要求的匹配度 | 15% |
| 优先级满足度 | 高优先级工单的时间满足度 | 20% |

#### 优点

- 排程质量优于贪心算法
- 可调节优化目标和权重
- 适合中等规模排程

#### 缺点

- 计算时间略长
- 可能需要多次迭代

### 2.3 遗传算法 (GENETIC) - 未实现

**策略**: 进化优化

适用于超大规模排程(500+工单)，需要更长计算时间但能找到更优解。

## 3. 约束条件处理

### 3.1 硬约束

必须满足的约束:

1. **时间约束**:
   - 工作时间: 08:00 - 18:00
   - 排程不能超出计划时间窗口
   - 每个任务必须连续执行

2. **资源约束**:
   - 一个设备同一时间只能执行一个任务
   - 一个工人同一时间只能执行一个任务

3. **技能约束**:
   - 工人必须具备工序所需技能(可选)

### 3.2 软约束

尽量满足的约束:

1. **优先级约束**: 高优先级工单优先安排
2. **交期约束**: 尽量在计划日期内完成
3. **设备偏好**: 优先使用指定设备
4. **工人偏好**: 优先使用指定工人

### 3.3 约束处理策略

```python
def validate_constraints(schedule, request):
    """验证约束条件"""
    constraints_met = {
        "time_window": True,
        "resource_available": True,
        "skill_matched": True,
        "equipment_capacity": True
    }
    
    # 检查时间窗口
    if not is_within_work_hours(schedule):
        constraints_met["time_window"] = False
    
    # 检查资源冲突
    if has_resource_conflict(schedule):
        constraints_met["resource_available"] = False
    
    # 检查技能匹配
    if request.consider_worker_skills:
        if not is_skill_matched(schedule):
            constraints_met["skill_matched"] = False
    
    return constraints_met
```

## 4. 时间计算

### 4.1 工作时间窗口

```python
WORK_START_HOUR = 8   # 08:00
WORK_END_HOUR = 18    # 18:00
WORK_HOURS_PER_DAY = 8
```

### 4.2 跨天计算

```python
def calculate_end_time(start_time, duration_hours):
    """计算结束时间(考虑非工作时段)"""
    remaining_hours = duration_hours
    current = start_time
    
    while remaining_hours > 0:
        # 调整到工作时间
        if current.hour < WORK_START_HOUR:
            current = current.replace(hour=WORK_START_HOUR)
        elif current.hour >= WORK_END_HOUR:
            # 跳到第二天
            current = (current + timedelta(days=1)).replace(hour=WORK_START_HOUR)
        
        # 计算当天剩余工作时间
        work_end = current.replace(hour=WORK_END_HOUR)
        hours_until_end = (work_end - current).total_seconds() / 3600
        
        if remaining_hours <= hours_until_end:
            # 可以在今天完成
            current = current + timedelta(hours=remaining_hours)
            remaining_hours = 0
        else:
            # 需要跨天
            remaining_hours -= hours_until_end
            current = (current + timedelta(days=1)).replace(hour=WORK_START_HOUR)
    
    return current
```

### 4.3 时间槽查找

```python
def find_earliest_available_slot(equipment_slots, worker_slots, start_from, duration):
    """找到最早可用时间槽"""
    current = adjust_to_work_time(start_from)
    
    while True:
        end = calculate_end_time(current, duration)
        
        # 检查是否与已有排程冲突
        if not has_time_overlap(current, end, equipment_slots + worker_slots):
            return current
        
        # 移动到下一个可能的时间点
        current = find_next_slot(current, equipment_slots + worker_slots)
```

## 5. 冲突检测

### 5.1 冲突类型

| 类型 | 描述 | 严重程度 |
|------|------|----------|
| EQUIPMENT | 设备时间冲突 | HIGH |
| WORKER | 工人时间冲突 | MEDIUM |
| TIME_OVERLAP | 时间窗口冲突 | HIGH |
| SKILL_MISMATCH | 技能不匹配 | LOW |
| CAPACITY_EXCEEDED | 产能超限 | CRITICAL |

### 5.2 检测算法

```python
def detect_conflicts(schedules):
    """检测资源冲突"""
    conflicts = []
    
    for i, schedule1 in enumerate(schedules):
        for schedule2 in schedules[i+1:]:
            # 设备冲突
            if (schedule1.equipment_id == schedule2.equipment_id and
                time_overlap(schedule1, schedule2)):
                conflicts.append(ResourceConflict(
                    type='EQUIPMENT',
                    severity='HIGH',
                    ...
                ))
            
            # 工人冲突
            if (schedule1.worker_id == schedule2.worker_id and
                time_overlap(schedule1, schedule2)):
                conflicts.append(ResourceConflict(
                    type='WORKER',
                    severity='MEDIUM',
                    ...
                ))
    
    return conflicts
```

## 6. 紧急插单算法

### 6.1 插单策略

```python
def urgent_insert(work_order_id, insert_time, max_delay_hours, auto_adjust):
    """紧急插单"""
    # 1. 分配资源(优先级最高)
    equipment = select_best_equipment(work_order)
    worker = select_best_worker(work_order)
    
    # 2. 创建排程
    new_schedule = create_schedule(
        work_order, equipment, worker, insert_time,
        priority=5.0, is_urgent=True
    )
    
    # 3. 查找冲突的排程
    conflicting = find_conflicting_schedules(new_schedule)
    
    # 4. 如果自动调整
    if auto_adjust:
        for conf_schedule in conflicting:
            # 计算延迟时间
            delay = new_schedule.end_time - conf_schedule.start_time
            
            # 如果延迟在允许范围内
            if delay <= max_delay_hours:
                # 延后排程
                conf_schedule.start_time = new_schedule.end_time
                conf_schedule.end_time = calculate_end_time(
                    conf_schedule.start_time,
                    conf_schedule.duration
                )
    
    return new_schedule, adjusted_schedules
```

### 6.2 影响分析

插单后需要评估影响:

- 直接影响的排程数量
- 延迟的总工时
- 可能违约的工单数量
- 资源利用率变化

## 7. 评分算法

### 7.1 评分指标

```python
class ScheduleScoreMetrics:
    completion_rate: float         # 交期达成率 (0-1)
    equipment_utilization: float   # 设备利用率 (0-1)
    worker_utilization: float      # 工人利用率 (0-1)
    total_duration_hours: float    # 总时长(小时)
    skill_match_rate: float        # 技能匹配率 (0-1)
    priority_satisfaction: float   # 优先级满足度 (0-1)
    conflict_count: int            # 冲突数量
```

### 7.2 综合评分

```python
def calculate_overall_score(metrics):
    """计算综合评分(0-100)"""
    # 基础分数
    base_score = (
        0.25 * metrics.completion_rate +
        0.15 * metrics.equipment_utilization +
        0.10 * metrics.worker_utilization +
        0.15 * metrics.skill_match_rate +
        0.20 * metrics.priority_satisfaction
    )
    
    # 惩罚项
    conflict_penalty = min(metrics.conflict_count * 0.02, 0.5)
    overtime_penalty = min(metrics.overtime_hours * 0.001, 0.1)
    
    # 最终分数
    final_score = max(0, base_score - conflict_penalty - overtime_penalty)
    
    return round(final_score * 100, 2)
```

## 8. 性能优化

### 8.1 目标性能指标

- 100个工单排程: < 5秒
- 200个工单排程: < 15秒
- 500个工单排程: < 60秒

### 8.2 优化技术

1. **数据结构优化**:
   - 使用字典存储资源时间表: O(1) 查找
   - 时间槽列表保持有序: 二分查找

2. **算法优化**:
   - 提前终止无效分支
   - 缓存重复计算结果
   - 并行处理独立工单

3. **数据库优化**:
   - 批量插入排程记录
   - 索引优化
   - 懒加载关联数据

### 8.3 性能监控

```python
def generate_schedule_with_metrics(request):
    start_time = time.time()
    
    # 执行排程
    schedules = generate_schedule(request)
    
    elapsed_time = time.time() - start_time
    
    metrics = {
        "elapsed_time_seconds": elapsed_time,
        "schedules_per_second": len(schedules) / elapsed_time,
        "total_schedules": len(schedules)
    }
    
    return schedules, metrics
```

## 9. 扩展性设计

### 9.1 算法插件化

```python
class SchedulingAlgorithm(ABC):
    @abstractmethod
    def schedule(self, work_orders, resources, constraints):
        pass

class GreedyAlgorithm(SchedulingAlgorithm):
    def schedule(self, ...):
        # 贪心算法实现
        pass

class HeuristicAlgorithm(SchedulingAlgorithm):
    def schedule(self, ...):
        # 启发式算法实现
        pass
```

### 9.2 自定义约束

```python
class Constraint(ABC):
    @abstractmethod
    def check(self, schedule):
        pass

class SkillConstraint(Constraint):
    def check(self, schedule):
        # 检查技能匹配
        pass
```

## 10. 总结

本排程算法设计兼顾了:

- ✅ **实用性**: 贪心算法快速生成可用方案
- ✅ **优化性**: 启发式算法提升排程质量
- ✅ **灵活性**: 支持多种优化目标和约束
- ✅ **可扩展性**: 插件化设计，便于添加新算法

适用于中小型非标自动化设备制造企业的生产排程需求。
