# 绩效管理系统重构方案

## 📋 需求分析

### 核心需求变更

**原设计**:
- 绩效管理作为独立模块
- HR/管理层为主要使用者
- 自上而下的考核模式

**新需求**:
- ✅ 绩效管理融入"个人中心"
- ✅ 每个员工每月提交工作总结（自我评价）
- ✅ 双重评价机制：部门经理 50% + 项目经理 50%
- ✅ 权重可由HR调整
- ✅ AI自动总结工作内容（减少手写工作量）
- ✅ 工作流：员工 → 部门经理审批 → 项目经理打分

---

## 🎯 新架构设计

### 1. 用户角色与权限

#### 普通员工
**个人中心 - 我的绩效**:
- ✅ 提交月度工作总结（自我评价）
- ✅ 使用AI辅助生成工作总结
- ✅ 查看个人绩效历史
- ✅ 查看评价结果和反馈
- ✅ 查看个人排名（可选）

#### 部门经理
**个人中心 - 我的绩效**: 同普通员工
**绩效管理模块**:
- ✅ 审批下属的月度工作总结
- ✅ 对下属进行绩效评分（占50%权重）
- ✅ 查看部门绩效统计
- ✅ 查看部门排名

#### 项目经理
**个人中心 - 我的绩效**: 同普通员工
**项目管理 - 团队绩效**:
- ✅ 接收项目成员的工作总结抄送
- ✅ 对项目成员进行绩效评分（占50%权重）
- ✅ 查看项目团队绩效

#### HR经理
**绩效管理模块**:
- ✅ 配置评价权重（部门经理 vs 项目经理）
- ✅ 配置绩效指标
- ✅ 查看全公司绩效统计
- ✅ 绩效排行榜
- ✅ 导出绩效报表

#### 董事长/总经理
**绩效管理模块**:
- ✅ 查看全公司绩效概览
- ✅ 查看绩效排行榜
- ✅ 查看部门绩效对比

---

## 🔄 工作流程设计

### 月度绩效评价流程

```
┌─────────────────────────────────────────────────────────────┐
│                     1. 员工自评阶段                          │
│                  (每月1-5号，员工填写)                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ↓
              ┌───────────────────────────────┐
              │  员工提交月度工作总结          │
              │  - 工作内容（AI辅助生成）      │
              │  - 自我评价                   │
              │  - 工作亮点                   │
              │  - 遇到的问题                 │
              │  - 下月计划                   │
              └───────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   2. 双重评价阶段                            │
│                (每月6-10号，上级评价)                         │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    ↓                   ↓
        ┌───────────────────┐   ┌───────────────────┐
        │  部门经理评价      │   │  项目经理评价      │
        │  (权重 50%)       │   │  (权重 50%)       │
        │                   │   │                   │
        │ - 工作态度        │   │ - 项目贡献        │
        │ - 团队协作        │   │ - 任务完成质量    │
        │ - 专业能力        │   │ - 交付及时性      │
        │ - 工作成果        │   │ - 问题解决能力    │
        └───────────────────┘   └───────────────────┘
                    │                   │
                    └─────────┬─────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   3. 系统计算阶段                            │
│                 (自动计算综合得分)                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ↓
              ┌───────────────────────────────┐
              │  综合得分 = 部门经理分×50%    │
              │           + 项目经理分×50%    │
              │  (权重可由HR调整)             │
              └───────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   4. 结果公示阶段                            │
│                 (每月11-15号，结果公示)                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ↓
              ┌───────────────────────────────┐
              │  员工查看结果                 │
              │  - 综合得分                   │
              │  - 等级评定                   │
              │  - 上级评语                   │
              │  - 改进建议                   │
              └───────────────────────────────┘
```

---

## 🗂️ 数据库设计调整

### 新增/修改表

#### 1. monthly_work_summary (月度工作总结表)
```sql
CREATE TABLE monthly_work_summary (
    id INT PRIMARY KEY AUTO_INCREMENT,
    employee_id INT NOT NULL,                    -- 员工ID
    employee_name VARCHAR(50),                   -- 员工姓名
    department_id INT,                           -- 部门ID
    department_name VARCHAR(100),                -- 部门名称

    period VARCHAR(20) NOT NULL,                 -- 周期（如 2026-01）
    submit_date DATE,                            -- 提交日期

    -- 工作总结内容
    work_content TEXT,                           -- 本月工作内容（AI辅助生成）
    self_evaluation TEXT,                        -- 自我评价
    work_highlights TEXT,                        -- 工作亮点
    problems_encountered TEXT,                   -- 遇到的问题
    next_month_plan TEXT,                        -- 下月计划

    -- AI相关
    ai_generated_summary TEXT,                   -- AI生成的工作总结
    is_ai_assisted BOOLEAN DEFAULT FALSE,        -- 是否使用AI辅助

    -- 关联项目
    related_projects JSON,                       -- 参与的项目列表

    -- 流程状态
    status VARCHAR(20) DEFAULT 'DRAFT',          -- 状态：草稿/已提交/评价中/已完成

    -- 评价信息
    dept_manager_id INT,                         -- 部门经理ID
    dept_manager_score DECIMAL(5,2),             -- 部门经理评分
    dept_manager_comment TEXT,                   -- 部门经理评语
    dept_manager_evaluate_date DATE,             -- 部门经理评价日期

    project_manager_ids JSON,                    -- 项目经理ID列表
    project_manager_scores JSON,                 -- 项目经理评分列表
    project_manager_comments JSON,               -- 项目经理评语列表

    -- 综合结果
    final_score DECIMAL(5,2),                    -- 综合得分
    performance_level VARCHAR(20),               -- 绩效等级

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_employee_period (employee_id, period),
    INDEX idx_period (period),
    INDEX idx_status (status)
);
```

#### 2. evaluation_weight_config (评价权重配置表)
```sql
CREATE TABLE evaluation_weight_config (
    id INT PRIMARY KEY AUTO_INCREMENT,
    config_name VARCHAR(100),                    -- 配置名称

    -- 权重配置
    dept_manager_weight DECIMAL(5,2) DEFAULT 50.00,  -- 部门经理权重（%）
    project_manager_weight DECIMAL(5,2) DEFAULT 50.00, -- 项目经理权重（%）

    -- 适用范围
    applicable_departments JSON,                 -- 适用部门
    applicable_roles JSON,                       -- 适用角色

    is_active BOOLEAN DEFAULT TRUE,              -- 是否启用
    effective_date DATE,                         -- 生效日期

    created_by INT,                              -- 创建人
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

#### 3. performance_evaluation_record (评价记录表)
```sql
CREATE TABLE performance_evaluation_record (
    id INT PRIMARY KEY AUTO_INCREMENT,
    summary_id INT NOT NULL,                     -- 关联工作总结ID
    employee_id INT NOT NULL,                    -- 被评价人ID
    evaluator_id INT NOT NULL,                   -- 评价人ID
    evaluator_role VARCHAR(50),                  -- 评价人角色（部门经理/项目经理）

    -- 评分详情
    score DECIMAL(5,2),                          -- 总分
    dimension_scores JSON,                       -- 各维度得分
    comment TEXT,                                -- 评语
    suggestions TEXT,                            -- 改进建议

    evaluate_date DATE,                          -- 评价日期
    weight DECIMAL(5,2),                         -- 权重

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_summary (summary_id),
    INDEX idx_employee (employee_id),
    INDEX idx_evaluator (evaluator_id)
);
```

---

## 📱 前端页面设计

### 个人中心 - 我的绩效模块

#### 1. 月度工作总结页面 (MonthlySummary.jsx)
**路径**: `/personal/monthly-summary`

**功能**:
- 📝 填写月度工作总结表单
- 🤖 AI辅助生成工作内容
- 📊 查看本月参与的项目列表（自动提取）
- 💾 保存草稿 / 提交
- 📜 查看历史总结

**表单字段**:
```
┌─────────────────────────────────────────┐
│  月度工作总结 - 2026年01月              │
├─────────────────────────────────────────┤
│  [AI辅助生成] 本月工作内容              │
│  ┌─────────────────────────────────┐   │
│  │ • 参与项目A的机械设计             │   │
│  │ • 完成项目B的图纸审核             │   │
│  │ • 参加技术评审会议3次             │   │
│  └─────────────────────────────────┘   │
│                                         │
│  自我评价                               │
│  ┌─────────────────────────────────┐   │
│  │ (员工填写)                        │   │
│  └─────────────────────────────────┘   │
│                                         │
│  工作亮点                               │
│  ┌─────────────────────────────────┐   │
│  │ (员工填写)                        │   │
│  └─────────────────────────────────┘   │
│                                         │
│  遇到的问题                             │
│  ┌─────────────────────────────────┐   │
│  │ (员工填写)                        │   │
│  └─────────────────────────────────┘   │
│                                         │
│  下月计划                               │
│  ┌─────────────────────────────────┐   │
│  │ (员工填写)                        │   │
│  └─────────────────────────────────┘   │
│                                         │
│  [保存草稿]  [提交]                     │
└─────────────────────────────────────────┘
```

---

#### 2. 我的绩效查看页面 (MyPerformance.jsx)
**路径**: `/personal/performance`

**功能**:
- 📊 查看个人绩效统计
- 📈 查看历史绩效趋势
- 👀 查看评价详情
- 🏆 查看个人排名（可选）

---

#### 3. 待评价列表页面 (EvaluationTasks.jsx)
**路径**: `/evaluation/pending`

**功能** (部门经理/项目经理):
- 📋 查看待评价员工列表
- ✍️ 对员工进行评价打分
- 💬 填写评语和建议
- ✅ 提交评价

---

### 绩效管理模块 (HR/管理层)

#### 1. 评价权重配置 (EvaluationWeightConfig.jsx)
**路径**: `/performance/weight-config`

**功能**:
- ⚖️ 配置部门经理和项目经理的权重比例
- 🏢 按部门/角色配置不同权重
- 📅 设置生效日期
- 💾 保存配置

---

## 🔌 API端点设计

### 工作总结相关

```javascript
// 月度工作总结
POST   /api/v1/performance/monthly-summary          // 创建/更新工作总结
GET    /api/v1/performance/monthly-summary          // 获取工作总结列表
GET    /api/v1/performance/monthly-summary/:id      // 获取单个总结详情
POST   /api/v1/performance/monthly-summary/:id/submit  // 提交总结

// AI辅助
POST   /api/v1/performance/ai-generate-summary      // AI生成工作总结
GET    /api/v1/performance/work-activities/:period  // 获取员工工作活动

// 评价相关
GET    /api/v1/performance/evaluation/pending       // 获取待评价列表
POST   /api/v1/performance/evaluation                // 提交评价
GET    /api/v1/performance/evaluation/:id           // 获取评价详情

// 权重配置
GET    /api/v1/performance/weight-config            // 获取权重配置
POST   /api/v1/performance/weight-config            // 创建权重配置
PUT    /api/v1/performance/weight-config/:id        // 更新权重配置
```

---

## 📋 导航菜单调整

### 个人中心（所有员工）
```javascript
personal: {
  label: '个人中心',
  items: [
    { name: '通知中心', path: '/notifications', icon: 'Bell' },
    { name: '我的绩效', path: '/personal/performance', icon: 'Award' },      // 新增
    { name: '月度总结', path: '/personal/monthly-summary', icon: 'FileText' }, // 新增
    { name: '工时填报', path: '/timesheet', icon: 'Clock' },
    { name: '个人设置', path: '/settings', icon: 'Settings' },
  ],
}
```

### 部门经理/项目经理
```javascript
{
  label: '团队管理',
  items: [
    { name: '待评价', path: '/evaluation/pending', icon: 'ClipboardCheck', badge: '5' }, // 新增
    { name: '团队绩效', path: '/team/performance', icon: 'Users' },  // 新增
    // ... 其他现有菜单
  ],
}
```

### HR经理
```javascript
performance_management: {
  label: '绩效管理',
  items: [
    { name: '绩效概览', path: '/performance', icon: 'Award' },
    { name: '绩效排行', path: '/performance/ranking', icon: 'TrendingUp' },
    { name: '指标配置', path: '/performance/indicators', icon: 'Settings' },
    { name: '权重配置', path: '/performance/weight-config', icon: 'Sliders' }, // 新增
    { name: '绩效结果', path: '/performance/results', icon: 'BarChart3' },
  ],
}
```

---

## 🤖 AI辅助功能设计

### AI工作总结生成逻辑

**数据来源**:
1. 项目任务记录（project_tasks）
2. 工时填报记录（timesheets）
3. 会议参与记录
4. 文档提交记录
5. 代码提交记录（如有）
6. 审批记录

**生成内容**:
```
本月您主要参与了以下工作：

【项目工作】
• 参与项目A（ICT测试设备）的机械设计工作，完成XX图纸设计
• 项目B（视觉检测设备）技术评审，提出XX改进建议
• 项目C的问题解决，协助解决XX技术难题

【日常工作】
• 参加技术评审会议3次
• 完成工时填报12天
• 提交技术文档5份
• 审批流程处理8项

【工作量统计】
• 总工时：176小时
• 项目A：80小时（45%）
• 项目B：60小时（34%）
• 其他工作：36小时（21%）
```

---

## 🚀 实施步骤

### Phase 1: 基础架构（Week 1）
- ✅ 数据库表设计和创建
- ✅ 后端API开发（工作总结CRUD）
- ✅ 前端页面：月度工作总结提交
- ✅ 前端页面：我的绩效查看

### Phase 2: 评价流程（Week 2）
- ✅ 评价工作流实现
- ✅ 前端页面：待评价列表
- ✅ 前端页面：评价打分界面
- ✅ 双重评价计算逻辑

### Phase 3: 权重配置（Week 3）
- ✅ 权重配置API
- ✅ 前端页面：权重配置界面
- ✅ 动态权重计算

### Phase 4: AI辅助（Week 4）
- ✅ 工作活动数据提取
- ✅ AI总结生成接口
- ✅ 前端集成AI辅助功能

### Phase 5: 完善优化（Week 5）
- ✅ 通知推送
- ✅ 导出报表
- ✅ 数据统计和分析

---

## 💡 关键特性

### 1. 双重评价机制
- 部门经理评价：关注态度、协作、专业能力
- 项目经理评价：关注项目贡献、交付质量
- 权重可配置，灵活适应不同团队

### 2. AI辅助减负
- 自动提取工作记录
- 生成工作总结初稿
- 员工只需补充和确认

### 3. 流程透明
- 员工可查看评价进度
- 评价结果及时反馈
- 历史记录可追溯

### 4. 灵活配置
- HR可调整权重
- 支持不同部门不同规则
- 适应组织变化

---

## 📊 与现有系统的集成

### 数据关联
```
员工工作活动
  ├─ 项目任务 (project_tasks)
  ├─ 工时记录 (timesheets)
  ├─ 会议参与 (meetings)
  ├─ 文档提交 (documents)
  └─ 审批处理 (approvals)
          ↓
   AI自动提取和总结
          ↓
    月度工作总结
          ↓
  部门经理 + 项目经理评价
          ↓
      综合绩效得分
```

---

## 🎯 预期效果

### 对员工
- ✅ 减少手写工作量（AI辅助）
- ✅ 清晰了解自己的工作成果
- ✅ 获得及时反馈和改进建议

### 对管理者
- ✅ 全面了解下属工作情况
- ✅ 更公平的评价机制
- ✅ 减少主观偏见

### 对HR
- ✅ 灵活的权重配置
- ✅ 全面的数据分析
- ✅ 高效的绩效管理

### 对公司
- ✅ 提升管理效率
- ✅ 激励员工成长
- ✅ 数据驱动决策

---

**文档版本**: v2.0
**创建时间**: 2026-01-07
**作者**: Claude Sonnet 4.5
