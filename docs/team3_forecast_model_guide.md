# 物料需求预测模型 - 使用指南

**Team 3: 智能缺料预警系统**  
**版本**: v1.0  
**日期**: 2026-02-16

---

## 📋 目录

1. [预测模型概述](#预测模型概述)
2. [算法选择指南](#算法选择指南)
3. [算法详解](#算法详解)
4. [准确率评估](#准确率评估)
5. [实战案例](#实战案例)
6. [常见问题](#常见问题)

---

## 预测模型概述

### 为什么需要预测?

传统的物料管理基于"安全库存"，但存在问题：
- ❌ 库存太高 → 资金占用、仓储成本
- ❌ 库存太低 → 频繁缺料、生产中断

智能预测可以：
- ✅ **提前准备** - 预知未来需求，提前采购
- ✅ **优化库存** - 根据预测动态调整库存水平
- ✅ **降低成本** - 减少缺料和积压

### 预测目标

**输入**:
- 物料ID
- 预测周期（天数）
- 历史数据周期

**输出**:
- 预测需求量
- 置信区间（上限/下限）
- 准确率指标

### 预测流程

```
1. 数据收集
   ↓
   从 WorkOrder、BOM 获取历史需求数据
   
2. 数据预处理
   ↓
   - 清洗异常值
   - 填补缺失值
   - 计算统计指标
   
3. 季节性检测
   ↓
   比较近期和历史数据，识别季节性模式
   
4. 算法预测
   ↓
   根据选择的算法计算预测值
   
5. 季节性调整
   ↓
   应用季节性系数
   
6. 置信区间计算
   ↓
   基于标准差计算上下限
   
7. 保存预测结果
   ↓
   记录到 material_demand_forecasts 表
```

---

## 算法选择指南

### 快速决策树

```
需求是否稳定？
│
├─ 是 → 需求波动小，无明显趋势
│         推荐: 移动平均 (MOVING_AVERAGE)
│         ✅ 简单快速
│         ✅ 适合稳定物料
│
└─ 否 → 需求有波动或趋势
         │
         ├─ 有上升/下降趋势
         │    推荐: 线性回归 (LINEAR_REGRESSION)
         │    ✅ 适合持续增长/下降
         │    ✅ 适合新产品或淘汰品
         │
         └─ 有短期波动，无明显趋势
              推荐: 指数平滑 (EXP_SMOOTHING) ⭐
              ✅ 通用性强
              ✅ 兼顾稳定性和灵活性
              ✅ 默认推荐
```

### 算法对比表

| 算法 | 适用场景 | 优点 | 缺点 | 准确率 | 计算速度 |
|------|----------|------|------|--------|----------|
| **移动平均** | 需求稳定 | 简单易懂<br/>抗干扰 | 滞后性强<br/>不能捕捉趋势 | ⭐⭐⭐ | ⚡⚡⚡ |
| **指数平滑** | 通用场景 | 兼顾新旧数据<br/>灵活性好 | 参数需调优 | ⭐⭐⭐⭐ | ⚡⚡⚡ |
| **线性回归** | 有趋势变化 | 能捕捉趋势<br/>预测长期 | 假设线性关系<br/>易受异常值影响 | ⭐⭐⭐ | ⚡⚡ |

### 算法选择示例

**场景1: 标准件（螺丝、螺母）**
- 特点：需求稳定，每月消耗量差不多
- 推荐算法：**移动平均** (MOVING_AVERAGE)
- 窗口期：7天

**场景2: 常规物料（钢板、线缆）**
- 特点：需求有波动，但无明显趋势
- 推荐算法：**指数平滑** (EXP_SMOOTHING) ⭐
- α值：0.3（平滑系数）

**场景3: 新产品物料**
- 特点：需求持续增长
- 推荐算法：**线性回归** (LINEAR_REGRESSION)
- 历史周期：30-60天

**场景4: 季节性物料（风扇、加热器）**
- 特点：季节性明显
- 推荐算法：**指数平滑** + 季节性调整
- 历史周期：365天（包含完整周期）

---

## 算法详解

### 1. 移动平均 (MOVING_AVERAGE)

#### 原理

计算最近N天的平均值作为预测。

**公式**:
```
forecast = (D₁ + D₂ + ... + Dₙ) / n
```

其中：
- D₁, D₂, ..., Dₙ 是最近n天的实际需求
- n 是窗口大小（默认7天）

#### 代码实现

```python
def moving_average_forecast(data, window=7):
    """
    移动平均预测
    
    Args:
        data: 历史需求列表 [10, 20, 15, 25, ...]
        window: 窗口大小，默认7天
    
    Returns:
        预测值
    """
    if len(data) < window:
        window = len(data)
    
    recent_data = data[-window:]  # 取最近N天
    return sum(recent_data) / len(recent_data)
```

#### 使用示例

```python
# 历史需求（最近14天）
historical_demand = [
    100, 105, 98, 102, 110, 95, 108,  # 第1周
    103, 99, 107, 101, 106, 104, 102   # 第2周
]

# 预测（取最近7天平均）
forecast = moving_average(historical_demand, window=7)
# forecast = (103 + 99 + 107 + 101 + 106 + 104 + 102) / 7 = 103.14
```

#### 优缺点

**优点**:
- ✅ 简单易懂
- ✅ 计算快速
- ✅ 抗异常值干扰

**缺点**:
- ❌ 滞后性强（跟不上趋势变化）
- ❌ 所有历史数据权重相同（忽略近期更重要）

---

### 2. 指数平滑 (EXP_SMOOTHING) ⭐ 推荐

#### 原理

给予近期数据更高的权重，远期数据逐渐衰减。

**公式**:
```
S_t = α * Y_t + (1 - α) * S_{t-1}
```

其中：
- S_t 是第t期的平滑值
- Y_t 是第t期的实际值
- α 是平滑系数（0 < α < 1）
- S_{t-1} 是第t-1期的平滑值

**α值含义**:
- α = 0.1 → 保守，变化慢（适合稳定需求）
- α = 0.3 → 中等，推荐默认值 ⭐
- α = 0.5 → 激进，反应快（适合波动需求）

#### 代码实现

```python
def exponential_smoothing_forecast(data, alpha=0.3):
    """
    指数平滑预测
    
    Args:
        data: 历史需求列表
        alpha: 平滑系数 (0 < α < 1)，默认0.3
    
    Returns:
        预测值
    """
    # 初始值使用第一个数据点
    smoothed = data[0]
    
    # 逐步平滑
    for value in data[1:]:
        smoothed = alpha * value + (1 - alpha) * smoothed
    
    return smoothed
```

#### 使用示例

```python
# 历史需求
historical_demand = [100, 110, 105, 115, 120, 118, 125]

# 预测（α = 0.3）
forecast = exponential_smoothing(historical_demand, alpha=0.3)

# 逐步计算:
# S₀ = 100
# S₁ = 0.3 * 110 + 0.7 * 100 = 103
# S₂ = 0.3 * 105 + 0.7 * 103 = 103.6
# S₃ = 0.3 * 115 + 0.7 * 103.6 = 107.02
# ...
# 最终 forecast ≈ 118.5
```

#### 参数调优

**如何选择α?**

1. **观察历史波动**
   - 波动大 → α = 0.4 - 0.5（快速反应）
   - 波动小 → α = 0.2 - 0.3（平稳预测）

2. **回测验证**
   ```python
   for alpha in [0.2, 0.3, 0.4, 0.5]:
       accuracy = backtest(data, alpha)
       print(f"α={alpha}, accuracy={accuracy}%")
   ```

3. **推荐默认**
   - α = 0.3（适合80%的场景）

#### 优缺点

**优点**:
- ✅ 兼顾新旧数据
- ✅ 适应性好，能跟上趋势
- ✅ 计算简单

**缺点**:
- ❌ 需要调优α参数
- ❌ 不能捕捉周期性

---

### 3. 线性回归 (LINEAR_REGRESSION)

#### 原理

拟合一条直线来表示需求趋势。

**公式**:
```
y = ax + b
```

其中：
- y 是预测值
- x 是时间（天数）
- a 是斜率（增长率）
- b 是截距

使用最小二乘法求解 a 和 b。

#### 代码实现

```python
def linear_regression_forecast(data):
    """
    线性回归预测
    
    Args:
        data: 历史需求列表
    
    Returns:
        预测值（下一个时间点）
    """
    n = len(data)
    x = list(range(n))  # 时间序列 [0, 1, 2, ...]
    y = data
    
    # 计算平均值
    x_mean = sum(x) / n
    y_mean = sum(y) / n
    
    # 计算斜率 a
    numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
    denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
    a = numerator / denominator
    
    # 计算截距 b
    b = y_mean - a * x_mean
    
    # 预测下一个点
    next_x = n
    forecast = a * next_x + b
    
    return max(0, forecast)  # 需求不能为负
```

#### 使用示例

```python
# 历史需求（持续增长）
historical_demand = [100, 110, 120, 125, 135, 145, 150]

# 预测
forecast = linear_regression(historical_demand)
# 拟合: y = 8.2x + 97.1
# 预测: y = 8.2 * 7 + 97.1 = 154.5
```

#### 适用场景

**适合**:
- ✅ 新产品（需求增长）
- ✅ 淘汰品（需求下降）
- ✅ 长期趋势预测

**不适合**:
- ❌ 稳定需求（会出现虚假趋势）
- ❌ 周期性需求（无法捕捉周期）

---

## 准确率评估

### 评估指标

#### 1. MAE (Mean Absolute Error) - 平均绝对误差

**公式**:
```
MAE = |actual - forecast|
```

**含义**: 预测值与实际值的平均偏差

**示例**:
```python
forecast = 100
actual = 110
mae = abs(110 - 100) = 10

解释: 平均偏差10个单位
```

#### 2. MAPE (Mean Absolute Percentage Error) - 平均绝对百分比误差

**公式**:
```
MAPE = |actual - forecast| / actual * 100%
```

**含义**: 预测误差的百分比

**示例**:
```python
forecast = 100
actual = 110
mape = abs(110 - 100) / 110 * 100% = 9.09%

解释: 偏差9.09%
```

#### 3. 准确率

**公式**:
```
accuracy = 100% - MAPE
```

**评价标准**:
- ≥ 95% - 优秀 ⭐⭐⭐⭐⭐
- 85-95% - 良好 ⭐⭐⭐⭐
- 75-85% - 合格 ⭐⭐⭐
- < 75% - 需改进 ⭐⭐

### 验证预测准确率

**API调用**:
```python
# 1. 生成预测
forecast_response = POST /shortage/smart/forecast/100
{
  "forecast_horizon_days": 30,
  "algorithm": "EXP_SMOOTHING"
}

# 2. 30天后验证
validate_response = POST /shortage/smart/forecast/{forecast_id}/validate
{
  "actual_demand": 115.5
}

# 3. 查看准确率
{
  "forecast_id": 1,
  "forecasted_demand": 110.0,
  "actual_demand": 115.5,
  "error": 5.5,
  "error_percentage": 4.76,
  "accuracy_score": 95.24,  // ← 准确率
  "within_confidence_interval": true
}
```

### 提高准确率的方法

**1. 增加历史数据**
```python
# 不推荐: 历史数据太少
forecast(historical_days=7)  # 准确率: 70%

# 推荐: 足够的历史数据
forecast(historical_days=90)  # 准确率: 88%
```

**2. 选择合适的算法**
```python
# 需求稳定 → 移动平均
# 需求波动 → 指数平滑 ⭐
# 有趋势 → 线性回归
```

**3. 考虑季节性**
```python
# 系统自动检测季节性
seasonal_factor = 1.2  # 当前处于旺季
final_forecast = base_forecast * seasonal_factor
```

**4. 排除异常值**
```python
# 去除异常的历史数据
historical_data = filter_outliers(raw_data)
```

---

## 实战案例

### 案例1: 标准件需求预测（移动平均）

**背景**: 螺丝M8×20，需求稳定

**历史数据**（最近14天）:
```
98, 102, 100, 105, 99, 103, 101, 
100, 98, 104, 102, 99, 101, 103
```

**预测**:
```python
# API调用
GET /shortage/smart/forecast/1001?algorithm=MOVING_AVERAGE&historical_days=14

# 响应
{
  "forecasted_demand": "101.29",  // 最近7天平均
  "lower_bound": "95.00",
  "upper_bound": "107.00",
  "confidence_interval": "95.00",
  "algorithm": "MOVING_AVERAGE"
}
```

**结果**: 预测需求 101个，建议采购 110个（含安全余量）

---

### 案例2: 常规物料预测（指数平滑）

**背景**: 钢板Q235，需求有波动

**历史数据**（最近30天）:
```
500, 520, 480, 550, 530, 510, 560, 
540, 520, 580, 570, 550, 590, 600,
580, 610, 620, 590, 630, 640, 
620, 650, 660, 640, 670, 680, 
660, 690, 700, 680
```

**预测**:
```python
# API调用
GET /shortage/smart/forecast/2001?algorithm=EXP_SMOOTHING&historical_days=30

# 响应
{
  "forecasted_demand": "695.50",  // 指数平滑
  "lower_bound": "650.00",
  "upper_bound": "740.00",
  "confidence_interval": "95.00",
  "seasonal_factor": "1.05",  // 检测到上升趋势
  "algorithm": "EXP_SMOOTHING"
}
```

**结果**: 预测需求 696kg，建议采购 750kg

---

### 案例3: 新产品预测（线性回归）

**背景**: 新产品配件，需求持续增长

**历史数据**（最近21天）:
```
10, 15, 20, 18, 25, 30, 28,
35, 40, 38, 45, 50, 48, 55,
60, 58, 65, 70, 68, 75, 80
```

**预测**:
```python
# API调用
GET /shortage/smart/forecast/3001?algorithm=LINEAR_REGRESSION&historical_days=21

# 响应
{
  "forecasted_demand": "85.20",  // 线性拟合
  "lower_bound": "75.00",
  "upper_bound": "95.00",
  "algorithm": "LINEAR_REGRESSION",
  "influencing_factors": {
    "trend": "increasing",
    "growth_rate": "3.5/day"
  }
}
```

**结果**: 预测需求 85个，建议采购 100个（考虑增长）

---

## 常见问题

### Q1: 历史数据不足怎么办？

**A**: 
- 至少需要 **7天** 数据才能预测
- 推荐 **30-90天** 数据以提高准确率
- 新物料：参考同类物料的历史数据

### Q2: 预测结果不准怎么办？

**A**: 检查以下几点
1. **算法选择** - 是否适合该物料特点？
2. **历史周期** - 数据是否足够？
3. **异常值** - 是否有突发订单干扰？
4. **季节性** - 是否考虑季节因素？

### Q3: 置信区间如何理解？

**A**: 
- **95%置信区间** = 有95%的概率，实际需求在此范围内
- 例如：预测100，置信区间[80, 120]
- 建议采购：取上限 120，以应对最大需求

### Q4: 多久更新一次预测？

**A**: 推荐频率
- 常规物料：**每周更新**
- 关键物料：**每天更新**
- 稳定物料：**每月更新**

### Q5: 如何验证预测效果？

**A**: 使用回测
```python
# 取90天历史数据
# 用前60天预测，验证后30天
accuracy_report = GET /shortage/smart/analysis/forecast-accuracy?days=30

# 查看
{
  "average_accuracy": "92.5%",  // 平均准确率
  "by_algorithm": {
    "EXP_SMOOTHING": {"avg_accuracy": 93.2},
    "MOVING_AVERAGE": {"avg_accuracy": 88.5},
    "LINEAR_REGRESSION": {"avg_accuracy": 85.0}
  }
}
```

---

## 最佳实践

### 1. 算法组合使用

```python
# 策略: 使用多个算法，取平均值
forecast_ma = moving_average(data)
forecast_es = exponential_smoothing(data)
forecast_lr = linear_regression(data)

final_forecast = (forecast_ma + forecast_es + forecast_lr) / 3
```

### 2. 动态调整窗口期

```python
# 根据波动性调整窗口
std = calculate_std(data)

if std < 10:  # 波动小
    window = 14  # 更长窗口，更平滑
else:  # 波动大
    window = 7   # 更短窗口，更敏感
```

### 3. 考虑外部因素

```python
# 叠加外部影响
base_forecast = 100

# 营销活动影响 +20%
marketing_factor = 1.2

# 价格上涨影响 -10%
price_factor = 0.9

final_forecast = base_forecast * marketing_factor * price_factor
# = 100 * 1.2 * 0.9 = 108
```

---

**文档版本**: v1.0  
**最后更新**: 2026-02-16  
**联系方式**: team3@example.com
