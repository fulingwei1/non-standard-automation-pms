# 挣值管理（EVM - Earned Value Management）完整指南

## 📚 目录

1. [EVM原理说明](#1-evm原理说明)
2. [数据模型](#2-数据模型)
3. [核心公式](#3-核心公式)
4. [API文档](#4-api文档)
5. [使用指南](#5-使用指南)
6. [案例分析](#6-案例分析)
7. [常见问题](#7-常见问题)

---

## 1. EVM原理说明

### 1.1 什么是EVM？

挣值管理（Earned Value Management，EVM）是一套**符合PMBOK标准**的项目绩效测量方法，通过整合项目范围、进度和成本三大约束，为项目管理提供客观的绩效数据。

### 1.2 EVM的核心价值

- ✅ **量化项目绩效**：用数据替代主观判断
- ✅ **早期预警**：提前发现进度和成本问题
- ✅ **预测完工状态**：基于当前趋势预测项目结果
- ✅ **支持决策**：为管理层提供客观依据

### 1.3 EVM三大核心指标

| 指标 | 英文 | 说明 | 示例 |
|------|------|------|------|
| **PV** | Planned Value | 计划价值：截至某时间点**应该**完成的工作的预算成本 | 计划完成50%，预算100万，PV=50万 |
| **EV** | Earned Value | 挣得价值：截至某时间点**实际**完成工作的预算成本 | 实际完成45%，预算100万，EV=45万 |
| **AC** | Actual Cost | 实际成本：截至某时间点**实际**发生的成本 | 实际花费48万，AC=48万 |

**关键理解**：
- PV基于**计划进度**计算
- EV基于**实际完成百分比**计算（不是实际成本）
- AC是真实花费的钱

---

## 2. 数据模型

### 2.1 EarnedValueData 表结构

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | Integer | 主键 |
| `project_id` | Integer | 项目ID |
| `period_type` | String(20) | 周期类型：WEEK/MONTH/QUARTER |
| `period_date` | Date | 周期截止日期 |
| `period_label` | String(50) | 周期标签（如：2026-02, 2026-W07） |
| **核心三要素** | | |
| `planned_value` | Decimal(18,4) | PV - 计划价值 |
| `earned_value` | Decimal(18,4) | EV - 挣得价值 |
| `actual_cost` | Decimal(18,4) | AC - 实际成本 |
| `budget_at_completion` | Decimal(18,4) | BAC - 完工预算 |
| **计算结果（自动）** | | |
| `schedule_variance` | Decimal(18,4) | SV - 进度偏差 |
| `cost_variance` | Decimal(18,4) | CV - 成本偏差 |
| `schedule_performance_index` | Decimal(10,6) | SPI - 进度绩效指数 |
| `cost_performance_index` | Decimal(10,6) | CPI - 成本绩效指数 |
| `estimate_at_completion` | Decimal(18,4) | EAC - 完工估算 |
| `estimate_to_complete` | Decimal(18,4) | ETC - 完工尚需估算 |
| `variance_at_completion` | Decimal(18,4) | VAC - 完工偏差 |
| `to_complete_performance_index` | Decimal(10,6) | TCPI - 完工尚需绩效指数 |

### 2.2 唯一约束

- 同一项目 + 同一周期类型 + 同一日期 只能有一条记录
- 确保数据不重复

---

## 3. 核心公式

### 3.1 偏差指标（Variance）

#### 进度偏差（Schedule Variance - SV）

```
SV = EV - PV
```

**判断标准**：
- `SV > 0`：进度超前 ✅
- `SV = 0`：进度符合计划 ✅
- `SV < 0`：进度落后 ⚠️

**示例**：
```
计划完成：PV = 50万
实际完成：EV = 45万
SV = 45万 - 50万 = -5万  → 进度落后5万元的工作量
```

#### 成本偏差（Cost Variance - CV）

```
CV = EV - AC
```

**判断标准**：
- `CV > 0`：成本节约 ✅
- `CV = 0`：成本符合预算 ✅
- `CV < 0`：成本超支 ⚠️

**示例**：
```
实际完成：EV = 45万
实际成本：AC = 48万
CV = 45万 - 48万 = -3万  → 成本超支3万元
```

---

### 3.2 绩效指数（Performance Index）

#### 进度绩效指数（Schedule Performance Index - SPI）

```
SPI = EV / PV
```

**判断标准**：
- `SPI > 1.0`：进度超前 ✅
- `SPI = 1.0`：进度符合计划 ✅
- `SPI < 1.0`：进度落后 ⚠️

**示例**：
```
SPI = 45万 / 50万 = 0.9  → 进度效率为90%，落后10%
```

**实际意义**：每投入1元计划成本，实际产出0.9元的价值

#### 成本绩效指数（Cost Performance Index - CPI）

```
CPI = EV / AC
```

**判断标准**：
- `CPI > 1.0`：成本效率高 ✅
- `CPI = 1.0`：成本符合预算 ✅
- `CPI < 1.0`：成本效率低 ⚠️

**示例**：
```
CPI = 45万 / 48万 = 0.9375  → 成本效率为93.75%
```

**实际意义**：每花费1元，实际产出0.94元的价值

---

### 3.3 预测指标（Forecast）

#### 完工估算（Estimate at Completion - EAC）

**标准公式**（假设当前成本绩效持续）：
```
EAC = AC + (BAC - EV) / CPI
```

**简化公式**（CPI无法计算时）：
```
EAC = AC + (BAC - EV)
```

**示例**：
```
AC = 48万
BAC = 100万
EV = 45万
CPI = 0.9375

EAC = 48万 + (100万 - 45万) / 0.9375
    = 48万 + 58.67万
    = 106.67万  → 预计完工需要106.67万
```

#### 完工尚需估算（Estimate to Complete - ETC）

```
ETC = EAC - AC
```

**示例**：
```
ETC = 106.67万 - 48万 = 58.67万  → 还需花费58.67万
```

#### 完工偏差（Variance at Completion - VAC）

```
VAC = BAC - EAC
```

**判断标准**：
- `VAC > 0`：预计节约 ✅
- `VAC = 0`：预计符合预算 ✅
- `VAC < 0`：预计超支 ⚠️

**示例**：
```
VAC = 100万 - 106.67万 = -6.67万  → 预计超支6.67万
```

#### 完工尚需绩效指数（To-Complete Performance Index - TCPI）

**基于BAC**（按原预算完成）：
```
TCPI = (BAC - EV) / (BAC - AC)
```

**基于EAC**（按修正预算完成）：
```
TCPI = (BAC - EV) / (EAC - AC)
```

**判断标准**：
- `TCPI > 1.0`：需要提高效率 ⚠️
- `TCPI = 1.0`：维持当前效率 ✅
- `TCPI < 1.0`：可以降低效率 ✅

**示例**：
```
TCPI = (100万 - 45万) / (100万 - 48万)
     = 55万 / 52万
     = 1.058  → 需要提高效率到105.8%才能按原预算完成
```

---

## 4. API文档

### 4.1 获取EVM综合分析

**端点**：`GET /api/v1/projects/{project_id}/costs/evm`

**权限**：`cost:read`

**响应示例**：
```json
{
  "project_id": 123,
  "project_code": "PRJ001",
  "project_name": "某智能制造项目",
  "analysis_date": "2026-02-14",
  "latest_data": {
    "id": 1,
    "period_type": "MONTH",
    "period_date": "2026-02-28",
    "period_label": "2026-02",
    "planned_value": 500000.00,
    "earned_value": 450000.00,
    "actual_cost": 480000.00,
    "budget_at_completion": 2000000.00,
    "schedule_variance": -50000.00,
    "cost_variance": -30000.00,
    "schedule_performance_index": 0.900000,
    "cost_performance_index": 0.937500,
    "estimate_at_completion": 2133333.33,
    "estimate_to_complete": 1653333.33,
    "variance_at_completion": -133333.33,
    "to_complete_performance_index": 1.032258,
    "planned_percent_complete": 25.00,
    "actual_percent_complete": 22.50
  },
  "performance_analysis": {
    "overall_status": "WARNING",
    "schedule_status": "WARNING",
    "schedule_description": "进度轻微落后",
    "cost_status": "WARNING",
    "cost_description": "成本轻微超支",
    "spi": 0.9,
    "cpi": 0.9375
  },
  "recommendations": [
    "⚠️ 进度轻微落后，建议密切监控关键路径任务，及时调整资源分配",
    "⚠️ 成本轻微超支，建议加强成本控制，审查采购和外协合同",
    "📊 TCPI=1.03，需要提高成本效率才能按预算完成项目"
  ]
}
```

---

### 4.2 获取EVM趋势数据

**端点**：`GET /api/v1/projects/{project_id}/costs/evm/trend`

**参数**：
- `period_type`：周期类型（WEEK/MONTH/QUARTER），默认MONTH
- `limit`：返回数据点数量（1-24），默认12

**权限**：`cost:read`

**响应示例**：
```json
{
  "project_id": 123,
  "period_type": "MONTH",
  "data_points": [
    {
      "period_label": "2026-02",
      "planned_value": 500000.00,
      "earned_value": 450000.00,
      "actual_cost": 480000.00,
      "spi": 0.90,
      "cpi": 0.9375
    },
    {
      "period_label": "2026-01",
      "planned_value": 250000.00,
      "earned_value": 240000.00,
      "actual_cost": 245000.00,
      "spi": 0.96,
      "cpi": 0.98
    }
  ],
  "trend_summary": {
    "data_points_count": 2,
    "period_range": {
      "from": "2026-01",
      "to": "2026-02"
    },
    "spi_trend": {
      "latest": 0.90,
      "oldest": 0.96,
      "change": -0.06,
      "direction": "DOWN"
    },
    "cpi_trend": {
      "latest": 0.9375,
      "oldest": 0.98,
      "change": -0.0425,
      "direction": "DOWN"
    },
    "overall_trend": {
      "direction": "DECLINING",
      "description": "绩效下降，需要关注"
    }
  }
}
```

---

### 4.3 记录EVM快照

**端点**：`POST /api/v1/projects/{project_id}/costs/evm/snapshot`

**权限**：`cost:write`

**请求体**：
```json
{
  "period_type": "MONTH",
  "period_date": "2026-02-28",
  "planned_value": 500000.00,
  "earned_value": 450000.00,
  "actual_cost": 480000.00,
  "budget_at_completion": 2000000.00,
  "currency": "CNY",
  "notes": "2月份EVM数据"
}
```

**响应**：返回创建的EVM数据对象（自动计算所有派生指标）

---

### 4.4 EVM公式计算器

**端点**：`GET /api/v1/projects/{project_id}/costs/evm/metrics`

**参数**：
- `pv`：计划价值
- `ev`：挣得价值
- `ac`：实际成本
- `bac`：完工预算

**权限**：`cost:read`

**用途**：快速验证EVM公式或进行假设分析（不保存数据库）

**响应示例**：
```json
{
  "pv": 500000.00,
  "ev": 450000.00,
  "ac": 480000.00,
  "bac": 2000000.00,
  "sv": -50000.00,
  "cv": -30000.00,
  "spi": 0.900000,
  "cpi": 0.937500,
  "eac": 2133333.33,
  "etc": 1653333.33,
  "vac": -133333.33,
  "tcpi": 1.032258,
  "planned_percent_complete": 25.00,
  "actual_percent_complete": 22.50
}
```

---

## 5. 使用指南

### 5.1 数据录入流程

#### 步骤1：确定BAC（完工预算）

在项目启动时，确定项目总预算（BAC），这是所有EVM计算的基准。

```python
# 示例：项目预算200万
BAC = 2000000.00
```

#### 步骤2：定期记录EVM数据

**建议频率**：
- 大型项目：每月
- 中型项目：每双周或每月
- 小型项目：每周或每双周

**需要收集的数据**：

1. **PV（计划价值）**：
   - 方法1：根据项目进度计划，计算截至本期应完成的工作量对应的预算
   - 方法2：`PV = BAC × 计划完成百分比`
   
   ```python
   # 示例：计划完成25%
   PV = 2000000 × 0.25 = 500000
   ```

2. **EV（挣得价值）**：
   - 根据实际完成的工作量计算
   - `EV = BAC × 实际完成百分比`
   
   ```python
   # 示例：实际完成22.5%
   EV = 2000000 × 0.225 = 450000
   ```

3. **AC（实际成本）**：
   - 从财务系统或成本核算模块获取
   - 包括：人工费、材料费、外协费、差旅费等
   
   ```python
   # 示例：实际花费48万
   AC = 480000
   ```

#### 步骤3：调用API记录数据

```bash
curl -X POST "http://your-domain/api/v1/projects/123/costs/evm/snapshot" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "period_type": "MONTH",
    "period_date": "2026-02-28",
    "planned_value": 500000.00,
    "earned_value": 450000.00,
    "actual_cost": 480000.00,
    "budget_at_completion": 2000000.00,
    "currency": "CNY",
    "notes": "2月份EVM数据"
  }'
```

系统会自动计算并保存所有派生指标。

---

### 5.2 如何计算实际完成百分比？

实际完成百分比是EVM的关键输入，有多种计算方法：

#### 方法1：0-100规则（适合小任务）

- 任务未完成：0%
- 任务已完成：100%

#### 方法2：50-50规则

- 任务开始：50%
- 任务完成：100%

#### 方法3：里程碑法

- 根据完成的里程碑数量计算

```python
完成百分比 = 已完成里程碑数 / 总里程碑数
```

#### 方法4：加权评估法（推荐）

- 将项目拆分为多个可度量的工作包
- 为每个工作包分配权重
- 根据完成情况加权求和

```python
# 示例
工作包A：权重30%，完成80% → 贡献24%
工作包B：权重40%，完成50% → 贡献20%
工作包C：权重30%，完成0%  → 贡献0%
总完成百分比 = 24% + 20% + 0% = 44%
```

---

### 5.3 绩效分析与决策

#### 场景1：进度落后 + 成本超支（双重危机）

**特征**：
- `SV < 0`，`CV < 0`
- `SPI < 1`，`CPI < 1`

**建议行动**：
1. 立即召开项目复盘会议
2. 分析根本原因（范围蔓延？资源不足？技术难题？）
3. 制定纠正措施：
   - 增加资源（人力/设备）
   - 优化流程（消除浪费）
   - 变更管理（调整范围或预算）
4. 加强监控频率（从月度改为周度）

#### 场景2：进度超前 + 成本节约（理想状态）

**特征**：
- `SV > 0`，`CV > 0`
- `SPI > 1`，`CPI > 1`

**建议行动**：
1. 总结成功经验，固化最佳实践
2. 警惕"过度乐观"（是否存在质量风险？）
3. 考虑提前完工或增加范围

#### 场景3：进度落后 + 成本节约

**特征**：
- `SV < 0`，`CV > 0`
- `SPI < 1`，`CPI > 1`

**分析**：
- 可能原因：资源投入不足
- 建议：增加资源投入，加快进度

#### 场景4：进度超前 + 成本超支

**特征**：
- `SV > 0`，`CV < 0`
- `SPI > 1`，`CPI < 1`

**分析**：
- 可能原因：赶工期导致成本上升
- 建议：评估赶工的必要性，平衡进度与成本

---

## 6. 案例分析

### 案例：某智能制造项目EVM分析

#### 项目背景

- **项目名称**：某工厂智能化改造项目
- **预算（BAC）**：200万元
- **计划工期**：8个月
- **当前时间**：第2个月末

#### 第2个月数据

```
计划进度：25%  → PV = 200万 × 0.25 = 50万
实际进度：22.5% → EV = 200万 × 0.225 = 45万
实际成本：48万  → AC = 48万
```

#### EVM指标计算

```
SV = EV - PV = 45万 - 50万 = -5万
CV = EV - AC = 45万 - 48万 = -3万

SPI = EV / PV = 45万 / 50万 = 0.90
CPI = EV / AC = 45万 / 48万 = 0.9375

EAC = AC + (BAC - EV) / CPI
    = 48万 + (200万 - 45万) / 0.9375
    = 48万 + 165.33万
    = 213.33万

ETC = EAC - AC = 213.33万 - 48万 = 165.33万

VAC = BAC - EAC = 200万 - 213.33万 = -13.33万

TCPI = (BAC - EV) / (BAC - AC)
     = (200万 - 45万) / (200万 - 48万)
     = 155万 / 152万
     = 1.02
```

#### 分析结论

1. **进度分析**：
   - SV = -5万，SPI = 0.9，进度落后10%
   - 原因：设备采购延迟2周

2. **成本分析**：
   - CV = -3万，CPI = 0.9375，成本效率为93.75%
   - 原因：部分材料价格上涨

3. **完工预测**：
   - EAC = 213.33万，VAC = -13.33万
   - 预计超支13.33万（6.67%）

4. **改进建议**：
   - TCPI = 1.02，需要将未来成本效率提升到102%
   - 建议：
     - 加快设备采购流程
     - 优化材料采购策略，寻找替代供应商
     - 加强成本控制，削减非必要开支

---

## 7. 常见问题

### Q1：EV和AC有什么区别？

**A：这是EVM最容易混淆的概念！**

- **EV（挣得价值）**：实际完成的工作量 × 预算单价
- **AC（实际成本）**：实际花费的钱

**举例**：
```
计划：挖10米管沟，预算1000元/米，总预算1万元
实际：挖了8米（实际完成），花了9000元（实际成本）

EV = 8米 × 1000元/米 = 8000元  （按预算单价计算）
AC = 9000元  （实际花费）

CV = EV - AC = 8000 - 9000 = -1000元  （成本超支）
```

---

### Q2：如何处理范围变更？

**A：范围变更应该调整BAC！**

1. 评审变更请求
2. 计算变更影响（时间+成本）
3. 审批通过后，更新BAC
4. 记录变更，在EVM数据的notes字段注明

```python
# 原BAC
BAC_original = 2000000

# 变更增加
BAC_change = 300000

# 新BAC
BAC_new = 2300000
```

⚠️ **注意**：BAC变更后，历史EVM数据的完成百分比会自动重新计算。

---

### Q3：CPI和SPI哪个更重要？

**A：CPI更重要！**

根据项目管理实践经验：
- **CPI**：成本偏差一旦发生，很难挽回（钱花了就回不来了）
- **SPI**：进度偏差可以通过赶工弥补（加班、增加资源）

**经验法则**：
- CPI < 0.9：高风险，需要立即干预
- SPI < 0.9：中风险，需要密切监控

---

### Q4：多久更新一次EVM数据？

**A：建议频率**

| 项目规模 | 工期 | 建议频率 |
|---------|------|---------|
| 小型项目 | < 3个月 | 每周 |
| 中型项目 | 3-12个月 | 每双周或每月 |
| 大型项目 | > 12个月 | 每月 |

**关键原则**：
- 频率太低：无法及时发现问题
- 频率太高：数据收集成本高，噪音大

---

### Q5：如何导出EVM报告？

**A：使用趋势API生成图表**

1. 调用 `GET /api/v1/projects/{id}/costs/evm/trend`
2. 获取历史数据
3. 使用前端图表库（如ECharts）绘制：
   - PV、EV、AC三线图
   - SPI、CPI趋势图
   - VAC预测图

---

## 📞 技术支持

如有问题，请联系：
- 📧 Email: support@example.com
- 📖 文档：[项目管理系统文档](https://docs.example.com)
- 🐛 问题反馈：[GitHub Issues](https://github.com/your-org/pms/issues)

---

**版本**：v1.0  
**更新日期**：2026-02-14  
**作者**：项目管理系统开发团队
