# 工程师绩效评价体系 - 完整设计文档

> **版本**: 1.0  
> **日期**: 2024年12月  
> **适用范围**: 非标自动化设备公司（约200人，80+工程师）  
> **涵盖岗位**: 机械工程师、测试工程师、电气工程师

---

## 目录

1. [项目概述](#一项目概述)
2. [统一评价框架](#二统一评价框架)
3. [机械工程师绩效体系](#三机械工程师绩效体系)
4. [测试工程师绩效体系](#四测试工程师绩效体系)
5. [电气工程师绩效体系](#五电气工程师绩效体系)
6. [多岗位统一平台](#六多岗位统一平台)
7. [数据库设计](#七数据库设计)
8. [API接口设计](#八api接口设计)
9. [前端页面设计](#九前端页面设计)
10. [实施路线图](#十实施路线图)
11. [附录](#十一附录)

---

## 一、项目概述

### 1.1 项目背景

公司现有约200名员工，其中工程师80+人，分布在机械设计、测试开发、电气控制三个核心技术部门。当前绩效评价存在以下问题：

- 评价标准不统一，主观性强
- 数据采集依赖人工，效率低
- 缺乏量化指标，难以横向对比
- 知识经验难以沉淀和复用

### 1.2 设计目标

```
┌─────────────────────────────────────────────────────────────────────┐
│                    工程师绩效评价体系目标                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  📊 量化评价    基于客观数据的量化评分，减少主观偏差                  │
│                                                                      │
│  🔄 自动采集    80%数据从现有系统自动提取，减少人工录入               │
│                                                                      │
│  ⚖️ 公平统一    同岗位同级别使用相同标准，确保评价公平               │
│                                                                      │
│  📈 持续改进    通过数据分析发现问题，驱动能力提升                    │
│                                                                      │
│  📚 知识沉淀    激励技术分享和模块复用，提升团队效率                  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.3 核心原则

| 原则 | 说明 |
|-----|------|
| **数据驱动** | 评价基于客观数据，非主观印象 |
| **公平透明** | 同岗位同级别使用相同标准，不针对个人调整权重 |
| **复用优先** | 最大化利用现有系统数据，减少额外录入 |
| **持续迭代** | 指标和权重可配置，支持动态优化 |

---

## 二、统一评价框架

### 2.1 五维评价体系

三类工程师共享统一的五维评价框架，每个维度内的具体指标根据岗位特点差异化设计：

```
                          统一五维评价框架
                                │
    ┌────────────┬────────────┬─┴──┬────────────┬────────────┐
    ▼            ▼            ▼    ▼            ▼            ▼
┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐
│技术能力│  │项目执行│  │成本/质量│  │知识沉淀│  │团队协作│
│  30%  │  │  25%  │  │  20%  │  │  15%  │  │  10%  │
└───┬────┘  └───┬────┘  └───┬────┘  └───┬────┘  └───┬────┘
    │           │           │           │           │
    ▼           ▼           ▼           ▼           ▼
 岗位专属    岗位专属     岗位专属    岗位专属    跨部门互评
  指标        指标         指标        指标        机制
```

### 2.2 各岗位指标对照表

| 维度 | 权重 | 机械工程师 | 测试工程师 | 电气工程师 |
|-----|------|-----------|-----------|-----------|
| **技术能力** | 30% | 设计一次通过率 ≥85%<br>ECN责任率 ≤10%<br>调试问题密度 ≤0.5 | 程序一次调通率 ≥80%<br>Bug修复时长 ≤4h<br>代码审查通过率 ≥90% | 图纸一次通过率 ≥85%<br>PLC一次调通率 ≥80%<br>调试效率 ≥90% |
| **项目执行** | 25% | 按时完成率 ≥90%<br>BOM提交及时率 ≥95%<br>难度加权产出 | 按时完成率 ≥90%<br>现场2h响应率 ≥95%<br>版本迭代效率 | 按时完成率 ≥90%<br>图纸交付及时率 ≥95%<br>现场4h响应率 ≥90% |
| **成本/质量** | 20% | 标准件使用率 ≥60%<br>设计复用率 ≥30%<br>成本节约贡献 | 程序稳定性 ≥95%<br>测试覆盖率 ≥90%<br>误测率 ≤0.1% | 标准件使用率 ≥70%<br>选型准确率 ≥95%<br>故障密度 ≤0.2 |
| **知识沉淀** | 15% | 文档贡献 ≥2篇/季<br>标准模板<br>被引用次数 | 模块复用率<br>代码库贡献 ≥2个/季<br>技术分享 | PLC模块贡献 ≥2个/季<br>标准模板<br>被复用次数 |
| **团队协作** | 10% | 电气配合评分 ≥4.0<br>测试配合评分 ≥4.0<br>新人带教 | 机械配合评分 ≥4.0<br>电气配合评分 ≥4.0<br>代码审查参与 | 机械配合评分 ≥4.0<br>测试配合评分 ≥4.0<br>接口文档完整性 |

### 2.3 权重配置原则

**【重要】权重只能按「岗位类型 + 职级」配置，不能针对个人！**

```
┌─────────────────────────────────────────────────────────────┐
│                    权重配置层级结构                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   配置维度：岗位类型 × 职级                                  │
│                                                              │
│   ┌─────────────┐                                           │
│   │ 机械工程师   │───┬── 全部级别（通用）  → 35人            │
│   └─────────────┘   ├── 初级工程师        → 8人             │
│                     ├── 中级工程师        → 15人            │
│                     ├── 高级工程师        → 10人            │
│                     └── 资深/专家         → 2人             │
│                                                              │
│   ┌─────────────┐                                           │
│   │ 测试工程师   │───── 全部级别（通用）  → 15人            │
│   └─────────────┘                                           │
│                                                              │
│   ┌─────────────┐                                           │
│   │ 电气工程师   │───── 全部级别（通用）  → 30人            │
│   └─────────────┘                                           │
│                                                              │
│   ❌ 不支持针对个人的单独配置                                 │
│   ✅ 同一岗位同一级别 = 相同评价标准                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 2.4 等级划分规则

| 等级 | 名称 | 分数范围 | 颜色标识 |
|-----|------|---------|---------|
| S | 优秀 | 85-100分 | 🟢 绿色 |
| A | 良好 | 70-84分 | 🔵 蓝色 |
| B | 合格 | 60-69分 | 🟡 黄色 |
| C | 待改进 | 40-59分 | 🟠 橙色 |
| D | 不合格 | 0-39分 | 🔴 红色 |

### 2.5 跨部门协作评价

三类工程师需要相互配合完成项目，引入跨部门互评机制：

```
              评价者
被评价者    机械部    测试部    电气部
  ─────────────────────────────────
  机械部      -      配合度    接口配合
  测试部    需求响应    -      通讯配合  
  电气部    图纸准确  程序接口    -
```

评价维度：
- 沟通配合（1-5分）
- 响应速度（1-5分）
- 交付质量（1-5分）
- 接口规范（1-5分）

---

## 三、机械工程师绩效体系

### 3.1 岗位特点分析

机械工程师主要负责非标自动化设备的结构设计工作：

| 特点 | 说明 |
|-----|------|
| **工具** | SolidWorks/AutoCAD进行3D/2D设计 |
| **交付物** | 3D模型、2D图纸、BOM清单 |
| **评审机制** | 设计评审 → 发布 → 可能产生ECN |
| **质量体现** | 调试阶段暴露的设计问题数量 |

### 3.2 五维指标详解

#### 3.2.1 技术能力（30%）

| 指标 | 权重 | 目标 | 计算方式 | 数据来源 |
|-----|------|------|---------|---------|
| 设计一次通过率 | 35% | ≥85% | 一次通过评审的设计数/总设计数 | design_review表 |
| ECN责任率 | 25% | ≤10% | 因设计问题产生的ECN数/参与项目数 | design_change表 |
| 调试问题密度 | 25% | ≤0.5 | 调试阶段机械问题数/参与项目数 | debug_issue表 |
| 任务难度系数 | 15% | ≥3.0 | 完成任务的平均难度（1-5） | project_task表 |

**计算公式**:
```
技术得分 = 一次通过率得分×35% + ECN得分×25% + 问题密度得分×25% + 难度系数得分×15%

其中：
- 一次通过率得分 = min(实际值/目标值, 1.2) × 100
- ECN得分 = min(目标值/实际值, 1.2) × 100  // 越低越好
- 问题密度得分 = min(目标值/实际值, 1.2) × 100  // 越低越好
```

#### 3.2.2 项目执行（25%）

| 指标 | 权重 | 目标 | 计算方式 |
|-----|------|------|---------|
| 按时完成率 | 40% | ≥90% | 按时完成任务数/总任务数 |
| BOM交付及时率 | 30% | ≥95% | 按时提交BOM数/需提交BOM数 |
| 难度加权产出 | 30% | - | Σ(任务数×难度系数) |

#### 3.2.3 成本/质量（20%）

| 指标 | 权重 | 目标 | 说明 |
|-----|------|------|------|
| 标准件使用率 | 50% | ≥60% | BOM中标准件占比 |
| 设计复用率 | 50% | ≥30% | 复用已有设计的比例 |

#### 3.2.4 知识沉淀（15%）

| 指标 | 权重 | 目标 |
|-----|------|------|
| 技术文档贡献 | 40% | ≥2篇/季度 |
| 标准模板贡献 | 30% | ≥1个/季度 |
| 被引用次数 | 30% | 越多越好 |

#### 3.2.5 团队协作（10%）

| 指标 | 权重 | 目标 |
|-----|------|------|
| 电气部配合评分 | 40% | ≥4.0 |
| 测试部配合评分 | 40% | ≥4.0 |
| 新人带教 | 20% | 有加分 |

### 3.3 数据采集策略

```
┌─────────────────────────────────────────────────────────────┐
│                    数据采集来源                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  现有系统（自动提取 80%）                                     │
│  ├─ project_task        → 任务完成情况、难度、工时           │
│  ├─ pmo_resource_allocation → 资源分配、参与项目            │
│  ├─ design_change       → ECN记录                          │
│  └─ bom_submission      → BOM提交记录                       │
│                                                              │
│  新增采集（人工录入 20%）                                     │
│  ├─ design_review       → 设计评审记录                       │
│  ├─ debug_issue         → 调试问题记录                       │
│  └─ collaboration_rating → 跨部门互评                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 四、测试工程师绩效体系

### 4.1 岗位特点分析

测试工程师主要负责自动化测试设备的软件开发：

| 特点 | 说明 |
|-----|------|
| **技术栈** | LabVIEW、C#、Python |
| **交付物** | 测试程序、上位机软件、测试报告 |
| **质量体现** | 程序一次调通、Bug数量、运行稳定性 |
| **特殊要求** | 现场快速响应、多项目并行 |

### 4.2 五维指标详解

#### 4.2.1 技术能力（30%）

| 指标 | 权重 | 目标 | 说明 |
|-----|------|------|------|
| 程序一次调通率 | 35% | ≥80% | 首次部署即通过调试的比例 |
| Bug修复时长 | 30% | ≤4h | 从发现到修复的平均时长 |
| 代码审查通过率 | 20% | ≥90% | 代码审查一次通过比例 |
| 任务难度系数 | 15% | ≥3.0 | 完成任务的平均难度 |

#### 4.2.2 项目执行（25%）

| 指标 | 权重 | 目标 |
|-----|------|------|
| 按时完成率 | 35% | ≥90% |
| 现场响应率 | 35% | ≥95%（2小时内响应） |
| 版本迭代效率 | 30% | 合理的迭代周期 |

#### 4.2.3 成本/质量（20%）

| 指标 | 权重 | 目标 |
|-----|------|------|
| 程序稳定性 | 40% | ≥95%（30天无重大故障） |
| 测试覆盖率 | 30% | ≥90% |
| 误测率 | 30% | ≤0.1% |

#### 4.2.4 知识沉淀（15%）

| 指标 | 权重 | 目标 |
|-----|------|------|
| 代码模块复用率 | 40% | ≥30% |
| 公共模块贡献 | 40% | ≥2个/季度 |
| 技术分享 | 20% | ≥1次/季度 |

#### 4.2.5 团队协作（10%）

| 指标 | 权重 | 目标 |
|-----|------|------|
| 机械部配合评分 | 35% | ≥4.0 |
| 电气部配合评分 | 35% | ≥4.0 |
| 代码审查参与 | 30% | 积极参与 |

### 4.3 Bug跟踪与分析

测试工程师特有的Bug管理机制：

```sql
-- Bug严重程度定义
致命(Critical): 导致设备停机或安全问题
严重(Major): 功能无法使用
一般(Normal): 功能受限但可绕过
轻微(Minor): 界面或体验问题

-- Bug统计维度
1. 按发现阶段：内部调试/现场调试/客户验收/售后运行
2. 按责任归属：自身代码/外部接口/需求变更
3. 按修复时效：<2h/<4h/<8h/<24h/>24h
```

### 4.4 代码复用库

建立公共代码模块库，促进知识沉淀：

| 模块类型 | 示例 |
|---------|------|
| 通讯模块 | 串口通讯、TCP/IP、Modbus |
| 数据处理 | 数据采集、滤波算法、统计分析 |
| 界面组件 | 通用控件、图表、报表 |
| 硬件驱动 | 运动控制、IO操作、仪器驱动 |
| 工具类 | 日志、配置、加密 |

---

## 五、电气工程师绩效体系

### 5.1 岗位特点分析

电气工程师主要负责PLC编程和电气设计：

| 特点 | 说明 |
|-----|------|
| **技术栈** | 西门子/三菱/欧姆龙 PLC、EPLAN电气设计 |
| **交付物** | 电气图纸（原理图/接线图/布局图）、PLC程序、HMI界面 |
| **质量体现** | 图纸评审通过率、PLC一次调通率、选型准确率 |
| **特殊要求** | 多品牌PLC兼容、元器件标准化 |

### 5.2 五维指标详解

#### 5.2.1 技术能力（30%）

| 指标 | 权重 | 目标 | 说明 |
|-----|------|------|------|
| 图纸一次通过率 | 30% | ≥85% | 电气图纸评审一次通过比例 |
| PLC一次调通率 | 30% | ≥80% | PLC程序首次调试通过比例 |
| 故障密度 | 25% | ≤0.2/项目 | 电气相关故障数量 |
| 调试效率 | 15% | ≥90% | 实际调试时间/计划时间 |

#### 5.2.2 项目执行（25%）

| 指标 | 权重 | 目标 |
|-----|------|------|
| 按时完成率 | 35% | ≥90% |
| 图纸交付及时率 | 35% | ≥95% |
| 现场响应率 | 30% | ≥90%（4小时内） |

#### 5.2.3 成本/质量（20%）

| 指标 | 权重 | 目标 | 说明 |
|-----|------|------|------|
| 标准件使用率 | 40% | ≥70% | 使用公司标准元器件比例 |
| 选型准确率 | 40% | ≥95% | 元器件选型无需更换比例 |
| 库存件优先使用 | 20% | ≥60% | 优先使用库存件 |

#### 5.2.4 知识沉淀（15%）

| 指标 | 权重 | 目标 |
|-----|------|------|
| PLC模块贡献 | 40% | ≥2个/季度 |
| 标准模板贡献 | 30% | ≥1个/季度 |
| 技术文档 | 30% | ≥2篇/季度 |

#### 5.2.5 团队协作（10%）

| 指标 | 权重 | 目标 |
|-----|------|------|
| 机械部配合评分 | 40% | ≥4.0 |
| 测试部配合评分 | 40% | ≥4.0 |
| 接口文档完整性 | 20% | ≥90% |

### 5.3 PLC品牌管理

支持多品牌PLC的统计分析：

| 品牌 | 颜色标识 | 常用场景 |
|-----|---------|---------|
| 西门子 | 🔷 青色 | 高端设备、复杂控制 |
| 三菱 | 🔴 红色 | 中端设备、快速开发 |
| 欧姆龙 | 🔵 蓝色 | 精密控制、视觉集成 |
| 倍福 | 🟠 橙色 | 高速运动、EtherCAT |
| 汇川 | 🟢 绿色 | 国产替代、成本敏感 |

### 5.4 PLC模块库

建立公共PLC功能块库：

| 模块类型 | 示例功能块 |
|---------|-----------|
| 运动控制 | 单轴定位、多轴插补、凸轮 |
| IO处理 | 防抖滤波、边沿检测、批量操作 |
| 通讯 | Modbus主/从站、TCP通讯 |
| 数据处理 | 配方管理、数据记录、统计 |
| 报警处理 | 报警分类、历史记录、推送 |
| 工艺流程 | 步进控制、状态机、并行处理 |

---

## 六、多岗位统一平台

### 6.1 平台架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                    多岗位工程师绩效管理平台                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐          │
│   │  机械工程师  │     │  测试工程师  │     │  电气工程师  │          │
│   │   35人      │     │   15人      │     │   30人      │          │
│   └──────┬──────┘     └──────┬──────┘     └──────┬──────┘          │
│          │                   │                   │                  │
│          └───────────────────┼───────────────────┘                  │
│                              ▼                                      │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │                      统一评价框架                            │  │
│   │  ┌─────────┬─────────┬─────────┬─────────┬─────────┐        │  │
│   │  │技术能力 │项目执行 │成本/质量│知识沉淀 │团队协作 │        │  │
│   │  │  30%   │  25%   │  20%   │  15%   │  10%   │        │  │
│   │  └─────────┴─────────┴─────────┴─────────┴─────────┘        │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                              ▼                                      │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │  跨部门互评  +  知识贡献  +  统一排名  =  综合绩效管理        │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.2 功能模块

| 模块 | 功能说明 |
|-----|---------|
| **首页总览** | 公司整体概况、三类岗位对比、等级分布、趋势分析 |
| **绩效排名** | 综合排名、分岗位排名、多维度筛选 |
| **个人绩效** | 五维雷达图、指标明细、项目记录、趋势分析 |
| **跨部门协作** | 协作矩阵、互评录入、评价统计 |
| **知识贡献** | 贡献排行、资源库、复用统计 |
| **岗位专区** | 各岗位专属功能（设计评审/Bug跟踪/图纸管理等） |
| **系统配置** | 权重配置、指标配置、等级规则 |

### 6.3 数据流转

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  项目管理系统  │───▶│  绩效计算引擎  │───▶│  绩效展示平台  │
│  (数据源)    │    │  (数据处理)   │    │  (可视化)    │
└─────────────┘    └─────────────┘    └─────────────┘
       │                  │                  │
       ▼                  ▼                  ▼
   project_task      performance_      排名/雷达图/
   pmo_resource      summary表        趋势分析
   design_change     (汇总结果)       对比分析
   ...
```

---

## 七、数据库设计

### 7.1 表结构总览

```
数据库表结构
│
├── 通用表（所有岗位共享）
│   ├── engineer_info           工程师基础信息
│   ├── performance_dimension   评价维度配置
│   ├── performance_metric      评价指标配置
│   ├── performance_weight      权重配置（按岗位+级别）
│   ├── performance_summary     绩效汇总表
│   ├── collaboration_rating    跨部门互评记录
│   ├── knowledge_contribution  知识贡献记录
│   └── grade_rule              等级规则配置
│
├── 机械工程师专用表
│   ├── design_review           设计评审记录
│   ├── mechanical_debug_issue  调试问题记录
│   └── design_reuse_record     设计复用记录
│
├── 测试工程师专用表
│   ├── test_program_version    测试程序版本
│   ├── test_bug_record         Bug跟踪记录
│   ├── code_review_record      代码审查记录
│   └── test_code_module        公共代码模块库
│
└── 电气工程师专用表
    ├── electrical_drawing_version  电气图纸版本
    ├── plc_program_version         PLC程序版本
    ├── electrical_component_selection  元器件选型
    ├── electrical_fault_record     电气故障记录
    ├── plc_module_library          PLC模块库
    └── plc_module_reuse            模块复用记录
```

### 7.2 核心通用表DDL

```sql
-- ============================================================
-- 1. 工程师信息表
-- ============================================================
CREATE TABLE engineer_info (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    employee_id BIGINT NOT NULL COMMENT '员工ID',
    employee_name VARCHAR(50) NOT NULL,
    
    -- 岗位信息
    job_type ENUM('mechanical','test','electrical') NOT NULL COMMENT '岗位类型',
    job_level ENUM('初级','中级','高级','资深','专家') DEFAULT '中级',
    department_id BIGINT,
    department_name VARCHAR(100),
    
    -- 专业技能标签
    skill_tags JSON COMMENT '技能标签，如["SolidWorks","EPLAN","西门子"]',
    primary_skill VARCHAR(50) COMMENT '主要技能',
    
    -- 入职信息
    join_date DATE,
    status ENUM('active','inactive') DEFAULT 'active',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_employee (employee_id),
    INDEX idx_job_type (job_type),
    INDEX idx_department (department_id)
) COMMENT '工程师信息表';


-- ============================================================
-- 2. 评价维度配置表
-- ============================================================
CREATE TABLE performance_dimension (
    id INT PRIMARY KEY AUTO_INCREMENT,
    dimension_code VARCHAR(30) NOT NULL COMMENT '维度编码',
    dimension_name VARCHAR(50) NOT NULL COMMENT '维度名称',
    description TEXT COMMENT '维度描述',
    display_order INT DEFAULT 0 COMMENT '显示顺序',
    is_active BOOLEAN DEFAULT TRUE,
    
    UNIQUE KEY uk_code (dimension_code)
) COMMENT '评价维度配置表';

-- 初始化五个维度
INSERT INTO performance_dimension (dimension_code, dimension_name, display_order) VALUES
('technical', '技术能力', 1),
('execution', '项目执行', 2),
('cost_quality', '成本/质量', 3),
('knowledge', '知识沉淀', 4),
('collaboration', '团队协作', 5);


-- ============================================================
-- 3. 评价指标配置表
-- ============================================================
CREATE TABLE performance_metric (
    id INT PRIMARY KEY AUTO_INCREMENT,
    
    -- 归属
    dimension_code VARCHAR(30) NOT NULL COMMENT '所属维度',
    job_type ENUM('mechanical','test','electrical','all') NOT NULL COMMENT '适用岗位',
    
    -- 指标定义
    metric_code VARCHAR(50) NOT NULL COMMENT '指标编码',
    metric_name VARCHAR(100) NOT NULL COMMENT '指标名称',
    description TEXT COMMENT '指标说明',
    
    -- 计算方式
    calc_type ENUM('percentage','count','average','ratio','score') COMMENT '计算类型',
    calc_formula TEXT COMMENT '计算公式/SQL',
    data_source VARCHAR(100) COMMENT '数据来源表',
    
    -- 目标值
    target_value DECIMAL(10,2) COMMENT '目标值',
    target_direction ENUM('higher_better','lower_better','equal_better') DEFAULT 'higher_better',
    
    -- 权重
    weight_in_dimension INT DEFAULT 25 COMMENT '在维度内的权重(%)',
    
    -- 显示
    unit VARCHAR(20) COMMENT '单位',
    display_format VARCHAR(50) COMMENT '显示格式',
    
    is_active BOOLEAN DEFAULT TRUE,
    
    UNIQUE KEY uk_metric (job_type, metric_code),
    INDEX idx_dimension (dimension_code),
    INDEX idx_job_type (job_type)
) COMMENT '评价指标配置表';


-- ============================================================
-- 4. 权重配置表
-- 【重要原则】权重只能按"岗位类型+级别"配置，不能针对个人！
-- ============================================================
CREATE TABLE performance_weight (
    id INT PRIMARY KEY AUTO_INCREMENT,
    
    -- 配置范围（岗位+级别，不涉及个人）
    job_type ENUM('mechanical','test','electrical') NOT NULL COMMENT '岗位类型',
    job_level ENUM('初级','中级','高级','资深','专家','all') DEFAULT 'all' COMMENT '适用级别',
    
    -- 维度权重
    dimension_code VARCHAR(30) NOT NULL,
    weight INT NOT NULL COMMENT '权重百分比',
    
    -- 版本控制
    effective_date DATE NOT NULL COMMENT '生效日期',
    expire_date DATE COMMENT '失效日期',
    version INT DEFAULT 1 COMMENT '版本号',
    
    -- 审批信息
    created_by BIGINT,
    approved_by BIGINT COMMENT '审批人',
    approved_at DATETIME COMMENT '审批时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_weight (job_type, job_level, dimension_code, effective_date)
) COMMENT '权重配置表（按岗位+级别，不针对个人）';

-- 初始化默认权重
INSERT INTO performance_weight (job_type, job_level, dimension_code, weight, effective_date) VALUES
-- 机械工程师
('mechanical', 'all', 'technical', 30, '2024-01-01'),
('mechanical', 'all', 'execution', 25, '2024-01-01'),
('mechanical', 'all', 'cost_quality', 20, '2024-01-01'),
('mechanical', 'all', 'knowledge', 15, '2024-01-01'),
('mechanical', 'all', 'collaboration', 10, '2024-01-01'),
-- 测试工程师
('test', 'all', 'technical', 30, '2024-01-01'),
('test', 'all', 'execution', 25, '2024-01-01'),
('test', 'all', 'cost_quality', 20, '2024-01-01'),
('test', 'all', 'knowledge', 15, '2024-01-01'),
('test', 'all', 'collaboration', 10, '2024-01-01'),
-- 电气工程师
('electrical', 'all', 'technical', 30, '2024-01-01'),
('electrical', 'all', 'execution', 25, '2024-01-01'),
('electrical', 'all', 'cost_quality', 20, '2024-01-01'),
('electrical', 'all', 'knowledge', 15, '2024-01-01'),
('electrical', 'all', 'collaboration', 10, '2024-01-01');


-- ============================================================
-- 5. 统一绩效汇总表
-- ============================================================
CREATE TABLE performance_summary (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    
    -- 工程师信息
    engineer_id BIGINT NOT NULL,
    engineer_name VARCHAR(50),
    job_type ENUM('mechanical','test','electrical') NOT NULL,
    job_level VARCHAR(20),
    department_id BIGINT,
    
    -- 周期
    period_type ENUM('monthly','quarterly','yearly') NOT NULL,
    period_value VARCHAR(10) NOT NULL COMMENT '如 2024-11, 2024Q4, 2024',
    period_start DATE,
    period_end DATE,
    
    -- 维度得分
    dimension_scores JSON COMMENT '{"technical":85,"execution":82,...}',
    technical_score DECIMAL(5,2),
    execution_score DECIMAL(5,2),
    cost_quality_score DECIMAL(5,2),
    knowledge_score DECIMAL(5,2),
    collaboration_score DECIMAL(5,2),
    
    -- 指标明细
    metric_details JSON COMMENT '存储所有具体指标值',
    
    -- 综合结果
    total_score DECIMAL(5,2) NOT NULL,
    grade ENUM('S','A','B','C','D'),
    grade_cn VARCHAR(10) COMMENT '中文等级',
    
    -- 排名
    department_rank INT,
    department_total INT,
    job_type_rank INT,
    job_type_total INT,
    company_rank INT,
    
    -- 同比环比
    prev_period_score DECIMAL(5,2),
    score_change DECIMAL(5,2),
    
    -- 计算信息
    calculated_at DATETIME,
    calculation_version VARCHAR(20),
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_engineer_period (engineer_id, period_type, period_value),
    INDEX idx_job_type (job_type),
    INDEX idx_period (period_type, period_value),
    INDEX idx_score (total_score DESC)
) COMMENT '工程师绩效汇总表';


-- ============================================================
-- 6. 跨部门协作评价表
-- ============================================================
CREATE TABLE collaboration_rating (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    
    -- 评价周期
    rating_period VARCHAR(10) NOT NULL COMMENT '评价周期，如 2024Q4',
    
    -- 被评价人
    rated_engineer_id BIGINT NOT NULL,
    rated_engineer_name VARCHAR(50),
    rated_job_type ENUM('mechanical','test','electrical') NOT NULL,
    rated_department_id BIGINT,
    
    -- 评价人
    rater_engineer_id BIGINT NOT NULL,
    rater_engineer_name VARCHAR(50),
    rater_job_type ENUM('mechanical','test','electrical') NOT NULL,
    rater_department_id BIGINT,
    
    -- 评分项
    communication_score DECIMAL(2,1) COMMENT '沟通配合(1-5)',
    response_score DECIMAL(2,1) COMMENT '响应速度(1-5)',
    quality_score DECIMAL(2,1) COMMENT '交付质量(1-5)',
    interface_score DECIMAL(2,1) COMMENT '接口规范(1-5)',
    avg_score DECIMAL(3,2),
    
    -- 评语
    comments TEXT,
    project_id BIGINT COMMENT '关联项目',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_rating (rated_engineer_id, rater_engineer_id, rating_period),
    INDEX idx_rated (rated_engineer_id, rating_period)
) COMMENT '跨部门协作评价表';


-- ============================================================
-- 7. 知识贡献记录表
-- ============================================================
CREATE TABLE knowledge_contribution (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    
    -- 贡献者
    engineer_id BIGINT NOT NULL,
    engineer_name VARCHAR(50),
    job_type ENUM('mechanical','test','electrical') NOT NULL,
    
    -- 贡献类型
    contribution_type ENUM(
        'document',          -- 技术文档
        'template',          -- 标准模板
        'module',            -- 代码/程序模块
        'training',          -- 培训分享
        'patent',            -- 专利
        'standard'           -- 企业标准
    ) NOT NULL,
    
    -- 贡献内容
    title VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(50),
    tags JSON,
    attachments JSON,
    
    -- 状态
    status ENUM('draft','reviewing','published','deprecated') DEFAULT 'draft',
    published_at DATETIME,
    
    -- 使用统计
    view_count INT DEFAULT 0,
    download_count INT DEFAULT 0,
    reuse_count INT DEFAULT 0,
    rating DECIMAL(2,1),
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_engineer (engineer_id),
    INDEX idx_job_type (job_type),
    INDEX idx_type (contribution_type)
) COMMENT '知识贡献记录表';


-- ============================================================
-- 8. 等级规则配置表
-- ============================================================
CREATE TABLE grade_rule (
    id INT PRIMARY KEY AUTO_INCREMENT,
    
    job_type ENUM('mechanical','test','electrical','all') DEFAULT 'all',
    
    grade_code VARCHAR(10) NOT NULL,
    grade_name VARCHAR(20) NOT NULL,
    min_score DECIMAL(5,2) NOT NULL,
    max_score DECIMAL(5,2),
    color_code VARCHAR(20),
    
    display_order INT,
    is_active BOOLEAN DEFAULT TRUE,
    effective_date DATE
) COMMENT '等级规则配置表';

INSERT INTO grade_rule (job_type, grade_code, grade_name, min_score, max_score, color_code, display_order, effective_date) VALUES
('all', 'S', '优秀', 85, 100, '#22c55e', 1, '2024-01-01'),
('all', 'A', '良好', 70, 84.99, '#3b82f6', 2, '2024-01-01'),
('all', 'B', '合格', 60, 69.99, '#f59e0b', 3, '2024-01-01'),
('all', 'C', '待改进', 40, 59.99, '#f97316', 4, '2024-01-01'),
('all', 'D', '不合格', 0, 39.99, '#ef4444', 5, '2024-01-01');
```

### 7.3 机械工程师专用表DDL

```sql
-- ============================================================
-- 设计评审记录表
-- ============================================================
CREATE TABLE design_review (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    
    -- 关联信息
    project_id BIGINT NOT NULL,
    task_id BIGINT,
    engineer_id BIGINT NOT NULL,
    
    -- 评审信息
    design_name VARCHAR(200) NOT NULL,
    design_type ENUM('3D模型','2D图纸','装配图','零件图') NOT NULL,
    version VARCHAR(20),
    
    -- 评审结果
    review_status ENUM('pending','approved','rejected','conditional') NOT NULL,
    review_round INT DEFAULT 1 COMMENT '评审轮次',
    first_pass BOOLEAN COMMENT '是否一次通过',
    
    -- 评审人
    reviewer_id BIGINT,
    reviewer_name VARCHAR(50),
    review_date DATE,
    review_comments TEXT,
    
    -- 问题记录
    issue_count INT DEFAULT 0,
    issue_details JSON,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_engineer (engineer_id),
    INDEX idx_project (project_id),
    INDEX idx_status (review_status)
) COMMENT '设计评审记录表';


-- ============================================================
-- 机械调试问题记录表
-- ============================================================
CREATE TABLE mechanical_debug_issue (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    
    -- 关联信息
    project_id BIGINT NOT NULL,
    engineer_id BIGINT NOT NULL COMMENT '责任工程师',
    
    -- 问题信息
    issue_title VARCHAR(200) NOT NULL,
    issue_description TEXT,
    issue_type ENUM('设计缺陷','尺寸错误','干涉问题','装配困难','强度不足','其他') NOT NULL,
    severity ENUM('致命','严重','一般','轻微') DEFAULT '一般',
    
    -- 发现阶段
    found_stage ENUM('内部调试','现场调试','客户验收','售后运行') NOT NULL,
    found_date DATE,
    
    -- 解决情况
    resolve_status ENUM('open','resolving','resolved','closed') DEFAULT 'open',
    resolve_date DATE,
    resolve_hours DECIMAL(5,1),
    
    -- 是否需要ECN
    need_ecn BOOLEAN DEFAULT FALSE,
    ecn_id BIGINT,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_engineer (engineer_id),
    INDEX idx_project (project_id)
) COMMENT '机械调试问题记录表';
```

### 7.4 测试工程师专用表DDL

```sql
-- ============================================================
-- 测试程序版本表
-- ============================================================
CREATE TABLE test_program_version (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    
    -- 关联信息
    project_id BIGINT NOT NULL,
    task_id BIGINT,
    developer_id BIGINT NOT NULL,
    
    -- 程序信息
    program_name VARCHAR(200) NOT NULL,
    program_type ENUM('LabVIEW','C#','Python','混合') NOT NULL,
    version VARCHAR(20) NOT NULL,
    
    -- 代码统计
    code_lines INT COMMENT '代码行数',
    function_count INT COMMENT '函数数量',
    module_count INT COMMENT '模块数量',
    
    -- 调试结果
    first_debug_pass BOOLEAN COMMENT '是否一次调通',
    debug_hours DECIMAL(5,1) COMMENT '调试工时',
    planned_debug_hours DECIMAL(5,1) COMMENT '计划调试工时',
    
    -- 稳定性
    stability_30d DECIMAL(5,2) COMMENT '30天稳定性(%)',
    
    -- 部署信息
    deploy_date DATE,
    deploy_status ENUM('development','testing','deployed','deprecated'),
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_developer (developer_id),
    INDEX idx_project (project_id)
) COMMENT '测试程序版本表';


-- ============================================================
-- Bug跟踪记录表
-- ============================================================
CREATE TABLE test_bug_record (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    
    -- 关联信息
    project_id BIGINT NOT NULL,
    program_id BIGINT,
    
    -- Bug信息
    bug_title VARCHAR(200) NOT NULL,
    bug_description TEXT,
    bug_type ENUM('功能缺陷','性能问题','界面问题','兼容性','安全问题','其他') NOT NULL,
    severity ENUM('致命','严重','一般','轻微') DEFAULT '一般',
    
    -- 责任归属
    responsible_id BIGINT COMMENT '责任人',
    responsibility_type ENUM('自身代码','外部接口','需求变更','环境问题') DEFAULT '自身代码',
    
    -- 发现阶段
    found_stage ENUM('开发自测','代码审查','集成测试','现场调试','客户验收','售后运行') NOT NULL,
    found_date DATETIME,
    found_by BIGINT,
    
    -- 解决情况
    status ENUM('open','assigned','fixing','testing','resolved','closed','wontfix') DEFAULT 'open',
    assigned_to BIGINT,
    resolve_date DATETIME,
    resolve_hours DECIMAL(5,1) COMMENT '解决耗时(小时)',
    
    -- 验证
    verified_by BIGINT,
    verified_date DATETIME,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_project (project_id),
    INDEX idx_responsible (responsible_id),
    INDEX idx_status (status)
) COMMENT 'Bug跟踪记录表';


-- ============================================================
-- 公共代码模块库
-- ============================================================
CREATE TABLE test_code_module (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    
    -- 模块信息
    module_name VARCHAR(100) NOT NULL,
    module_type ENUM('通讯','数据处理','界面组件','硬件驱动','算法','工具类') NOT NULL,
    tech_stack ENUM('LabVIEW','C#','Python','通用') NOT NULL,
    
    -- 描述
    description TEXT,
    usage_guide TEXT COMMENT '使用说明',
    
    -- 作者
    author_id BIGINT NOT NULL,
    author_name VARCHAR(50),
    
    -- 版本
    current_version VARCHAR(20),
    
    -- 使用统计
    reuse_count INT DEFAULT 0,
    rating DECIMAL(2,1),
    
    -- 状态
    status ENUM('draft','published','deprecated') DEFAULT 'draft',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_author (author_id),
    INDEX idx_type (module_type)
) COMMENT '公共代码模块库';
```

### 7.5 电气工程师专用表DDL

```sql
-- ============================================================
-- 电气图纸版本表
-- ============================================================
CREATE TABLE electrical_drawing_version (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    
    -- 关联信息
    project_id BIGINT NOT NULL,
    task_id BIGINT,
    designer_id BIGINT NOT NULL,
    
    -- 图纸信息
    drawing_no VARCHAR(50) NOT NULL COMMENT '图纸编号',
    drawing_name VARCHAR(200) NOT NULL,
    drawing_type ENUM('原理图','布局图','接线图','端子图','线缆清单','PLC程序','HMI') NOT NULL,
    version VARCHAR(20) NOT NULL,
    
    -- 评审信息
    review_status ENUM('pending','approved','rejected') DEFAULT 'pending',
    review_count INT DEFAULT 0 COMMENT '评审次数',
    first_pass BOOLEAN COMMENT '是否一次通过',
    reviewer_id BIGINT,
    review_date DATE,
    review_comments TEXT,
    
    -- 统计
    page_count INT COMMENT '页数',
    component_count INT COMMENT '元器件数量',
    
    -- 日期
    planned_date DATE,
    actual_date DATE,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_designer (designer_id),
    INDEX idx_project (project_id)
) COMMENT '电气图纸版本表';


-- ============================================================
-- PLC程序版本表
-- ============================================================
CREATE TABLE plc_program_version (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    
    -- 关联信息
    project_id BIGINT NOT NULL,
    task_id BIGINT,
    developer_id BIGINT NOT NULL,
    
    -- 程序信息
    program_name VARCHAR(200) NOT NULL,
    plc_brand ENUM('西门子','三菱','欧姆龙','倍福','汇川','台达','其他') NOT NULL,
    plc_model VARCHAR(50),
    program_type ENUM('主程序','功能块','数据块','HMI') NOT NULL,
    version VARCHAR(20) NOT NULL,
    
    -- 代码统计
    program_steps INT COMMENT '程序步数',
    function_blocks INT COMMENT '功能块数量',
    io_points INT COMMENT 'IO点数',
    axis_count INT COMMENT '轴数',
    
    -- 调试结果
    first_debug_pass BOOLEAN,
    debug_hours DECIMAL(5,1),
    planned_debug_hours DECIMAL(5,1),
    
    -- 稳定性
    stability_30d DECIMAL(5,2) COMMENT '30天稳定性',
    
    -- 部署
    deploy_date DATE,
    deploy_status ENUM('development','testing','deployed','deprecated'),
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_developer (developer_id),
    INDEX idx_project (project_id),
    INDEX idx_brand (plc_brand)
) COMMENT 'PLC程序版本表';


-- ============================================================
-- 元器件选型记录表
-- ============================================================
CREATE TABLE electrical_component_selection (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    
    -- 关联信息
    project_id BIGINT NOT NULL,
    engineer_id BIGINT NOT NULL,
    
    -- 元器件信息
    component_type ENUM('PLC','HMI','伺服驱动','伺服电机','变频器','继电器','接触器','断路器','开关电源','传感器','线缆','端子') NOT NULL,
    component_brand VARCHAR(50),
    component_model VARCHAR(100),
    quantity INT DEFAULT 1,
    
    -- 选型标记
    is_standard BOOLEAN DEFAULT FALSE COMMENT '是否标准件',
    is_stock BOOLEAN DEFAULT FALSE COMMENT '是否库存件',
    selection_correct BOOLEAN DEFAULT TRUE COMMENT '选型是否正确',
    
    -- 变更记录
    has_changed BOOLEAN DEFAULT FALSE,
    change_reason VARCHAR(200),
    
    -- 成本信息
    unit_price DECIMAL(10,2),
    total_price DECIMAL(12,2),
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_engineer (engineer_id),
    INDEX idx_project (project_id)
) COMMENT '元器件选型记录表';


-- ============================================================
-- 电气故障记录表
-- ============================================================
CREATE TABLE electrical_fault_record (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    
    -- 关联信息
    project_id BIGINT NOT NULL,
    responsible_id BIGINT COMMENT '责任工程师',
    
    -- 故障信息
    fault_title VARCHAR(200) NOT NULL,
    fault_description TEXT,
    fault_type ENUM('接线错误','选型错误','程序Bug','设计缺陷','元器件损坏','通讯故障','其他') NOT NULL,
    severity ENUM('致命','严重','一般','轻微') DEFAULT '一般',
    
    -- 发现阶段
    found_stage ENUM('内部调试','现场调试','客户验收','售后运行') NOT NULL,
    found_date DATE,
    
    -- 责任判定
    is_design_fault BOOLEAN DEFAULT FALSE COMMENT '是否设计责任',
    
    -- 解决情况
    resolve_status ENUM('open','resolving','resolved','closed') DEFAULT 'open',
    resolve_date DATE,
    resolve_hours DECIMAL(5,1),
    resolve_method TEXT,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_responsible (responsible_id),
    INDEX idx_project (project_id)
) COMMENT '电气故障记录表';


-- ============================================================
-- PLC公共模块库
-- ============================================================
CREATE TABLE plc_module_library (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    
    -- 模块信息
    module_name VARCHAR(100) NOT NULL,
    module_type ENUM('运动控制','IO处理','通讯','数据处理','报警处理','配方管理','工艺流程','通用工具') NOT NULL,
    plc_brand ENUM('西门子','三菱','欧姆龙','倍福','汇川','通用') NOT NULL,
    
    -- 描述
    description TEXT,
    usage_guide TEXT,
    
    -- 作者
    author_id BIGINT NOT NULL,
    author_name VARCHAR(50),
    
    -- 版本和状态
    current_version VARCHAR(20),
    status ENUM('draft','published','deprecated') DEFAULT 'draft',
    
    -- 使用统计
    reuse_count INT DEFAULT 0,
    rating DECIMAL(2,1),
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_author (author_id),
    INDEX idx_type (module_type),
    INDEX idx_brand (plc_brand)
) COMMENT 'PLC公共模块库';
```

---

## 八、API接口设计

### 8.1 接口总览

```
/api/v1/performance
├── /summary                  # 综合概览
│   ├── GET /company          # 公司整体概览
│   ├── GET /department/{id}  # 部门概览
│   └── GET /job-type/{type}  # 按岗位类型概览
│
├── /ranking                  # 排名
│   ├── GET /                 # 综合排名
│   ├── GET /by-department    # 按部门排名
│   └── GET /by-job-type      # 按岗位排名
│
├── /engineer                 # 工程师绩效
│   ├── GET /{id}             # 个人绩效详情
│   ├── GET /{id}/trend       # 个人趋势
│   ├── GET /{id}/comparison  # 对比分析
│   └── GET /{id}/metrics     # 指标明细
│
├── /collaboration            # 协作评价
│   ├── GET /matrix           # 协作矩阵
│   ├── GET /received/{id}    # 收到的评价
│   ├── GET /given/{id}       # 给出的评价
│   └── POST /                # 提交评价
│
├── /knowledge                # 知识贡献
│   ├── GET /                 # 贡献列表
│   ├── GET /ranking          # 贡献排行
│   └── POST /                # 提交贡献
│
├── /metrics                  # 岗位专属数据
│   ├── /mechanical/*         # 机械专属接口
│   ├── /test/*               # 测试专属接口
│   └── /electrical/*         # 电气专属接口
│
├── /config                   # 配置管理
│   ├── GET /weights          # 获取权重配置列表
│   ├── GET /weights/{job_type}/{level}  # 获取指定配置
│   ├── PUT /weights          # 更新权重配置
│   └── GET /grades           # 获取等级规则
│
└── /calculate                # 计算任务
    ├── POST /trigger         # 触发计算
    └── GET /status/{taskId}  # 计算状态
```

### 8.2 核心接口示例

#### 公司整体概览

```yaml
GET /api/v1/performance/summary/company?period_type=monthly&period_value=2024-11

Response:
{
  "code": 200,
  "data": {
    "period": { "type": "monthly", "value": "2024-11" },
    "overview": {
      "total_engineers": 80,
      "avg_score": 81.5,
      "score_change": 1.2,
      "by_job_type": [
        { "job_type": "mechanical", "count": 35, "avg_score": 82.1 },
        { "job_type": "test", "count": 15, "avg_score": 83.2 },
        { "job_type": "electrical", "count": 30, "avg_score": 80.5 }
      ],
      "grade_distribution": [
        { "grade": "S", "count": 15, "percentage": 18.75 },
        { "grade": "A", "count": 35, "percentage": 43.75 },
        { "grade": "B", "count": 25, "percentage": 31.25 },
        { "grade": "C", "count": 5, "percentage": 6.25 }
      ]
    },
    "dimension_comparison": {
      "mechanical": { "technical": 84, "execution": 82, "cost_quality": 80, "knowledge": 75, "collaboration": 85 },
      "test": { "technical": 86, "execution": 84, "cost_quality": 82, "knowledge": 78, "collaboration": 88 },
      "electrical": { "technical": 83, "execution": 80, "cost_quality": 78, "knowledge": 72, "collaboration": 84 }
    }
  }
}
```

#### 个人绩效详情

```yaml
GET /api/v1/performance/engineer/1001?period_type=monthly&period_value=2024-11

Response:
{
  "code": 200,
  "data": {
    "engineer": {
      "id": 1001,
      "name": "张三",
      "job_type": "mechanical",
      "job_type_name": "机械工程师",
      "level": "高级工程师",
      "department": "机械设计部"
    },
    "summary": {
      "total_score": 85.5,
      "grade": "S",
      "grade_name": "优秀",
      "department_rank": 2,
      "department_total": 35,
      "score_change": 2.5
    },
    "dimension_scores": {
      "technical": { "score": 88, "weight": 30, "weighted": 26.4 },
      "execution": { "score": 85, "weight": 25, "weighted": 21.25 },
      "cost_quality": { "score": 82, "weight": 20, "weighted": 16.4 },
      "knowledge": { "score": 80, "weight": 15, "weighted": 12.0 },
      "collaboration": { "score": 88, "weight": 10, "weighted": 8.8 }
    },
    "metrics": {
      "technical": [
        { "code": "first_pass_rate", "name": "设计一次通过率", "value": 90, "target": 85, "status": "good" }
      ]
    }
  }
}
```

#### 权重配置更新

```yaml
PUT /api/v1/performance/config/weights

Request:
{
  "job_type": "mechanical",
  "job_level": "all",
  "dimensions": [
    { "code": "technical", "name": "技术能力", "weight": 30 },
    { "code": "execution", "name": "项目执行", "weight": 25 },
    { "code": "cost_quality", "name": "成本/质量", "weight": 20 },
    { "code": "knowledge", "name": "知识沉淀", "weight": 15 },
    { "code": "collaboration", "name": "团队协作", "weight": 10 }
  ],
  "effective_date": "2024-12-01"
}

Response:
{
  "code": 200,
  "data": {
    "job_type": "mechanical",
    "affected_count": 35,
    "message": "配置已更新，将影响 35 名工程师，于 2024-12-01 生效"
  }
}
```

---

## 九、前端页面设计

### 9.1 页面结构

```
多岗位工程师绩效管理平台
│
├── 🏠 首页总览
│   ├── 公司整体绩效概况（4个统计卡片）
│   ├── 三类岗位对比卡片
│   ├── 五维能力雷达图对比
│   ├── 等级分布饼图
│   ├── 月度趋势折线图
│   └── TOP 10 工程师排行
│
├── 📊 绩效排名
│   ├── 筛选器（岗位/部门/等级）
│   ├── 综合排名表格
│   └── 导出功能
│
├── 👤 个人绩效
│   ├── 工程师选择器
│   ├── 综合得分大卡片
│   ├── 五维雷达图
│   ├── 指标明细（5个维度tab）
│   ├── 跨部门协作评价
│   └── 历史趋势图
│
├── 🤝 跨部门协作
│   ├── 协作矩阵（3×3表格）
│   ├── 协作评价录入表单
│   └── 评价统计
│
├── 📚 知识贡献
│   ├── 热门贡献TOP 10
│   ├── 贡献者排行榜
│   └── 提交新贡献
│
├── 🔧 岗位专区
│   ├── 机械工程师（设计评审、ECN统计）
│   ├── 测试工程师（Bug跟踪、代码库）
│   └── 电气工程师（图纸管理、PLC模块库）
│
└── ⚙️ 系统配置
    ├── 权重配置（按岗位+级别）
    ├── 指标目标值配置
    └── 等级规则配置
```

### 9.2 关键页面设计要点

#### 首页总览
- 顶部4个统计卡片：工程师总数、公司平均分、优秀率、待改进人数
- 三类岗位对比卡片：每个岗位显示人数、平均分、3个关键指标
- 雷达图：三类岗位五维能力叠加对比
- 趋势图：近6个月三类岗位得分变化

#### 个人绩效
- 大号得分卡片：突出显示综合分、等级、排名
- 雷达图：个人五维能力 vs 部门平均
- 指标明细：分维度展示各项指标的实际值vs目标值
- 协作评价：来自其他部门的评分和评语

#### 配置页面
- 明确提示"按岗位+级别配置，不针对个人"
- 显示当前配置影响的人数
- 权重滑块实时显示总和（必须=100%）

---

## 十、实施路线图

### 10.1 总体规划

```
┌─────────────────────────────────────────────────────────────────────┐
│                        实施路线图                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  第一阶段（2周）          第二阶段（3周）          第三阶段（2周）     │
│  ┌─────────────┐        ┌─────────────┐        ┌─────────────┐      │
│  │  基础架构    │   →    │  数据采集    │   →    │  功能完善    │      │
│  │             │        │             │        │             │      │
│  │ ·数据库建表  │        │ ·现有系统对接│        │ ·知识库功能  │      │
│  │ ·核心API开发│        │ ·数据提取SQL │        │ ·报表导出    │      │
│  │ ·基础页面   │        │ ·增量录入功能│        │ ·权限管理    │      │
│  └─────────────┘        └─────────────┘        └─────────────┘      │
│                                                                      │
│  第四阶段（2周）          第五阶段（持续）                            │
│  ┌─────────────┐        ┌─────────────┐                             │
│  │  试运行     │   →    │  持续优化    │                             │
│  │             │        │             │                             │
│  │ ·小范围试用 │        │ ·指标调优    │                             │
│  │ ·问题修复   │        │ ·功能迭代    │                             │
│  │ ·培训推广   │        │ ·数据分析    │                             │
│  └─────────────┘        └─────────────┘                             │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 10.2 各阶段详细任务

#### 第一阶段：基础架构（2周）

| 任务 | 负责人 | 工时 | 输出物 |
|-----|-------|------|-------|
| 数据库表创建 | 后端 | 2天 | DDL脚本 |
| 初始化配置数据 | 后端 | 1天 | 配置数据 |
| 核心API开发 | 后端 | 5天 | API接口 |
| 基础前端页面 | 前端 | 5天 | 页面原型 |

#### 第二阶段：数据采集（3周）

| 任务 | 负责人 | 工时 | 输出物 |
|-----|-------|------|-------|
| 现有系统数据对接 | 后端 | 3天 | 对接接口 |
| 数据提取SQL开发 | 后端 | 3天 | SQL脚本 |
| 设计评审录入功能 | 全栈 | 3天 | 录入页面 |
| Bug/故障录入功能 | 全栈 | 3天 | 录入页面 |
| 跨部门互评功能 | 全栈 | 3天 | 互评页面 |

#### 第三阶段：功能完善（2周）

| 任务 | 负责人 | 工时 | 输出物 |
|-----|-------|------|-------|
| 知识库功能 | 全栈 | 4天 | 知识库模块 |
| 报表导出 | 后端 | 2天 | 导出功能 |
| 权限管理 | 后端 | 2天 | 权限模块 |
| 页面优化 | 前端 | 2天 | 优化页面 |

#### 第四阶段：试运行（2周）

| 任务 | 负责人 | 工时 | 输出物 |
|-----|-------|------|-------|
| 小范围试用 | 产品 | 5天 | 反馈报告 |
| 问题修复 | 开发 | 3天 | 修复版本 |
| 用户培训 | 产品 | 2天 | 培训材料 |

### 10.3 风险与应对

| 风险 | 影响 | 应对措施 |
|-----|------|---------|
| 现有系统数据不完整 | 指标无法计算 | 设计数据补录机制 |
| 用户抵触新系统 | 推广困难 | 强调客观公正，减少主观评价 |
| 指标设计不合理 | 评价失真 | 预留配置接口，支持快速调整 |

---

## 十一、附录

### 附录A：与项目管理系统对接

本绩效系统需要从现有项目管理系统中提取以下数据：

| 数据表 | 提取内容 | 用途 |
|-------|---------|------|
| project_task | 任务完成情况、工时、难度 | 项目执行指标 |
| pmo_resource_allocation | 人员分配、参与项目 | 工作量统计 |
| design_change | ECN记录 | 设计质量指标 |
| bom_submission | BOM提交记录 | 交付及时性 |
| project_info | 项目信息 | 关联分析 |

### 附录B：绩效计算公式

```
综合得分 = Σ(维度得分 × 维度权重)

维度得分 = Σ(指标得分 × 指标权重)

指标得分计算：
- 越高越好类：min(实际值/目标值, 1.2) × 100
- 越低越好类：min(目标值/实际值, 1.2) × 100
- 得分上限120分，超出目标有加分

等级判定：
- S级(优秀): 85-100分
- A级(良好): 70-84分
- B级(合格): 60-69分
- C级(待改进): 40-59分
- D级(不合格): 0-39分
```

### 附录C：文件清单

本项目包含以下交付文件：

| 文件名 | 类型 | 说明 |
|-------|------|------|
| engineer-performance-system-complete.md | 文档 | 完整设计文档（本文件） |
| multi-role-performance-platform.html | 原型 | 多岗位平台前端原型 |
| multi_role_performance_api.py | 代码 | FastAPI后端实现 |
| mechanical-engineer-performance-prototype.html | 原型 | 机械工程师专属页面 |
| test-engineer-performance-prototype.html | 原型 | 测试工程师专属页面 |
| electrical-engineer-performance-prototype.html | 原型 | 电气工程师专属页面 |

---

> **文档版本**: 1.0  
> **最后更新**: 2024年12月  
> **维护者**: 研发部
