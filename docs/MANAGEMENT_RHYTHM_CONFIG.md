# 管理节律系统配置指南

## 一、配置概述

管理节律系统通过节律配置来定义各层级的会议模板、关键指标和输出成果。管理员可以根据企业实际情况自定义这些配置。

## 二、配置项说明

### 2.1 节律层级（Rhythm Level）

系统支持四个层级：

- **STRATEGIC**：战略层
- **OPERATIONAL**：经营层
- **OPERATION**：运营层
- **TASK**：任务层

### 2.2 周期类型（Cycle Type）

系统支持四种周期：

- **QUARTERLY**：季度
- **MONTHLY**：月度
- **WEEKLY**：周度
- **DAILY**：每日

### 2.3 会议模板配置（Meeting Template）

会议模板是一个JSON对象，包含以下字段：

```json
{
  "agenda_template": [
    "议题1：战略方向校准",
    "议题2：资源分配讨论",
    "议题3：关键决策"
  ],
  "required_metrics": [
    "收入",
    "利润率",
    "现金流"
  ],
  "output_artifacts": [
    "战略地图",
    "平衡计分卡",
    "OGSMT"
  ],
  "decision_framework": "四问四不做",
  "duration_minutes": 120
}
```

**字段说明**：
- `agenda_template`：会议议程模板（数组）
- `required_metrics`：必需的关键指标（数组）
- `output_artifacts`：输出成果清单（数组）
- `decision_framework`：决策框架（字符串）
- `duration_minutes`：会议时长（分钟）

### 2.4 关键指标清单（Key Metrics）

关键指标是一个JSON数组，每个指标包含以下字段：

```json
[
  {
    "name": "收入",
    "type": "financial",
    "target": 1000,
    "unit": "万元",
    "description": "月度收入目标"
  },
  {
    "name": "利润率",
    "type": "financial",
    "target": 0.15,
    "unit": "%",
    "description": "目标利润率"
  }
]
```

**字段说明**：
- `name`：指标名称
- `type`：指标类型（financial/project/operation/task）
- `target`：目标值
- `unit`：单位
- `description`：指标描述

### 2.5 输出成果清单（Output Artifacts）

输出成果是一个字符串数组：

```json
[
  "战略地图",
  "平衡计分卡",
  "OGSMT",
  "组织三图三表"
]
```

## 三、配置示例

### 3.1 战略层季度会议配置

```json
{
  "rhythm_level": "STRATEGIC",
  "cycle_type": "QUARTERLY",
  "config_name": "季度战略研讨会",
  "description": "每季度召开的战略方向校准会议",
  "meeting_template": {
    "agenda_template": [
      "议题1：五层战略结构推演",
      "  - 使命/愿景：我们要成为什么？",
      "  - 战略机会：我们凭什么能赢？（四点合一分析）",
      "  - 战略定位：我们在哪个战场打，用什么方式取胜？",
      "  - 战略目标：我们要实现什么结果？（可验证逻辑）",
      "  - 战略路径：我们怎么实现？（价值流路径）",
      "议题2：行业趋势分析（五看）",
      "议题3：战略目标调整（三定）",
      "议题4：资源再分配",
      "议题5：关键决策"
    ],
    "required_metrics": [
      "市场占有率",
      "新业务收入占比",
      "核心能力建设进度"
    ],
    "output_artifacts": [
      "五层战略结构",
      "战略地图",
      "平衡计分卡",
      "OGSMT"
    ],
    "decision_framework": "四问四不做",
    "duration_minutes": 180
  },
  "key_metrics": [
    {
      "name": "市场占有率",
      "type": "strategic",
      "target": 0.25,
      "unit": "%",
      "description": "目标市场占有率"
    }
  ],
  "output_artifacts": [
    "战略地图",
    "平衡计分卡",
    "OGSMT",
    "组织三图三表"
  ]
}
```

### 3.2 经营层月度会议配置

```json
{
  "rhythm_level": "OPERATIONAL",
  "cycle_type": "MONTHLY",
  "config_name": "月度经营分析会",
  "description": "每月召开的财务健康度诊断会议",
  "meeting_template": {
    "agenda_template": [
      "议题1：财务指标回顾",
      "议题2：差距分析",
      "议题3：改善措施讨论",
      "议题4：预算调整"
    ],
    "required_metrics": [
      "收入",
      "成本",
      "利润",
      "现金流",
      "毛利率",
      "净利润率"
    ],
    "output_artifacts": [
      "经营分析报告",
      "改善计划",
      "预算调整方案"
    ],
    "decision_framework": "差距分析与改善",
    "duration_minutes": 120
  },
  "key_metrics": [
    {
      "name": "收入",
      "type": "financial",
      "target": 1000,
      "unit": "万元",
      "description": "月度收入目标"
    },
    {
      "name": "利润率",
      "type": "financial",
      "target": 0.15,
      "unit": "%",
      "description": "目标利润率"
    }
  ],
  "output_artifacts": [
    "经营分析报告",
    "改善计划",
    "预算调整方案"
  ]
}
```

### 3.3 运营层周度会议配置

```json
{
  "rhythm_level": "OPERATION",
  "cycle_type": "WEEKLY",
  "config_name": "周运营例会",
  "description": "每周召开的流程效率复盘会议",
  "meeting_template": {
    "agenda_template": [
      "议题1：流程指标回顾",
      "议题2：项目进展汇报",
      "议题3：异常处理",
      "议题4：改进计划"
    ],
    "required_metrics": [
      "订单交付周期",
      "生产良率",
      "招聘达成率"
    ],
    "output_artifacts": [
      "运营周报",
      "行动清单"
    ],
    "decision_framework": "问题解决与改进",
    "duration_minutes": 60
  },
  "key_metrics": [
    {
      "name": "订单交付周期",
      "type": "operation",
      "target": 30,
      "unit": "天",
      "description": "平均订单交付周期"
    }
  ],
  "output_artifacts": [
    "运营周报",
    "行动清单"
  ]
}
```

### 3.4 任务层每日会议配置

```json
{
  "rhythm_level": "TASK",
  "cycle_type": "DAILY",
  "config_name": "日清会",
  "description": "每日召开的任务对齐会议",
  "meeting_template": {
    "agenda_template": [
      "议题1：昨日任务完成情况",
      "议题2：今日任务计划",
      "议题3：障碍与问题",
      "议题4：明日计划"
    ],
    "required_metrics": [
      "任务完成率",
      "障碍数量"
    ],
    "output_artifacts": [
      "日清报告"
    ],
    "decision_framework": "三讲三不讲",
    "duration_minutes": 15
  },
  "key_metrics": [
    {
      "name": "任务完成率",
      "type": "task",
      "target": 0.95,
      "unit": "%",
      "description": "当日任务完成率"
    }
  ],
  "output_artifacts": [
    "日清报告"
  ]
}
```

## 四、配置操作

### 4.1 创建配置

1. 进入"节律配置管理"页面
2. 点击"创建配置"
3. 填写配置信息：
   - 选择层级和周期类型
   - 填写配置名称和描述
   - 配置会议模板（JSON格式）
   - 配置关键指标（JSON格式）
   - 配置输出成果（数组）
4. 点击"保存"

### 4.2 编辑配置

1. 在配置列表中，点击"编辑"
2. 修改配置信息
3. 点击"保存"

### 4.3 启用/停用配置

1. 在配置列表中，切换"启用"状态
2. 停用的配置不会在创建会议时显示

## 五、健康度计算规则

系统根据以下规则计算各层级的健康状态：

### 5.1 健康状态判断

- **GREEN（绿色）**：
  - 所有关键指标正常
  - 行动项按时完成率 >= 90%

- **YELLOW（黄色）**：
  - 部分指标异常
  - 行动项按时完成率 70% - 90%

- **RED（红色）**：
  - 关键指标异常
  - 行动项按时完成率 < 70%

### 5.2 完成率计算

```
完成率 = (已完成行动项数 / 总行动项数) × 100%
```

### 5.3 逾期判断

行动项在截止日期当天仍未完成，系统会自动标记为"OVERDUE"状态。

## 六、权限配置

### 6.1 层级权限

- **战略层会议**：仅高管可见
- **经营层会议**：部门负责人及以上
- **运营层会议**：项目组及相关人员
- **任务层会议**：执行层人员

### 6.2 配置权限

- 只有系统管理员可以创建和编辑节律配置
- 普通用户只能查看配置

## 七、数据集成

### 7.1 财务数据集成

经营分析会可以集成以下财务数据：
- 收入、成本、利润
- 现金流
- 毛利率、净利润率

**API端点**：`GET /api/v1/rhythm-integration/financial-metrics`

### 7.2 项目数据集成

运营例会可以集成以下项目数据：
- 项目进展
- 项目健康度
- 里程碑完成情况

**API端点**：`GET /api/v1/rhythm-integration/project-metrics`

### 7.3 任务数据集成

日清会可以集成以下任务数据：
- 任务完成情况
- 任务逾期情况
- 任务工作量

**API端点**：`GET /api/v1/rhythm-integration/task-metrics`

## 八、注意事项

1. **配置修改影响**：修改配置不会影响已创建的会议，只影响新创建的会议
2. **JSON格式**：会议模板和关键指标必须使用有效的JSON格式
3. **指标单位**：建议统一指标单位，便于对比分析
4. **模板更新**：更新模板后，建议通知相关人员

## 九、五层战略结构模板

系统提供了五层战略结构的标准模板，可以通过以下API获取：

**端点**：`GET /api/v1/management-rhythm/strategic-structure-template`

模板包含五层的标准表达格式和关键问题，帮助企业在战略会上正确推演。

详细使用指南请参考：[五层战略结构框架使用指南](./STRATEGIC_STRUCTURE_FRAMEWORK.md)

## 十、技术支持

如有配置问题，请联系系统管理员。
