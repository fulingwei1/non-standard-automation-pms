# 机械工程师绩效评价系统 - 数据整合方案

## 一、整合策略：复用为主，补充为辅

### 1.1 核心原则

```
┌─────────────────────────────────────────────────────────────────┐
│                     数据整合策略                                  │
├─────────────────────────────────────────────────────────────────┤
│  现有系统数据（80%）          新增数据（20%）                      │
│  ├─ 任务管理表                ├─ 任务表补充字段                    │
│  ├─ ECN设计变更表             │   · first_pass                   │
│  ├─ 问题跟踪表                │   · rework_count                 │
│  ├─ BOM管理表                 │   · quality_score                │
│  ├─ 资源分配表                │   · difficulty_level             │
│  └─ 里程碑表                  ├─ 协作评价表（新增）                │
│                               └─ 绩效汇总表（新增）                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 二、现有数据提取映射

### 2.1 技术能力指标（权重30%）

| 指标 | 数据来源 | SQL提取逻辑 |
|-----|---------|------------|
| **一次通过率** | project_task | 需补充 `first_pass` 字段 |
| **设计变更责任率** | ECN表 | 见下方SQL |
| **调试问题密度** | 问题跟踪表 | 见下方SQL |

```sql
-- 一次通过率（任务表补充 first_pass 字段后）
SELECT 
    engineer_id,
    COUNT(*) as total_tasks,
    SUM(CASE WHEN first_pass = 1 THEN 1 ELSE 0 END) as passed_tasks,
    ROUND(SUM(CASE WHEN first_pass = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as first_pass_rate
FROM project_task
WHERE actual_end BETWEEN '2024-11-01' AND '2024-11-30'
  AND task_type IN ('方案设计', '详细设计', 'BOM编制')
GROUP BY engineer_id;

-- 设计变更责任率（从现有ECN表直接提取）
SELECT 
    engineer_id,
    COUNT(*) as total_ecn,
    SUM(CASE WHEN change_reason = '设计缺陷' AND is_responsible = 1 THEN 1 ELSE 0 END) as responsible_ecn,
    ROUND(SUM(CASE WHEN change_reason = '设计缺陷' AND is_responsible = 1 THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 2) as responsible_rate
FROM design_change  -- 你现有的ECN表名
WHERE created_at BETWEEN '2024-11-01' AND '2024-11-30'
GROUP BY engineer_id;

-- 调试问题密度（从现有问题跟踪表提取）
SELECT 
    t.responsible_engineer as engineer_id,
    COUNT(DISTINCT t.project_id) as project_count,
    COUNT(t.id) as issue_count,
    ROUND(COUNT(t.id) * 1.0 / NULLIF(COUNT(DISTINCT t.project_id), 0), 2) as issue_density
FROM debug_issue t  -- 你现有的问题表名
WHERE t.root_cause IN ('设计问题', '选型问题')  -- 只统计设计相关问题
  AND t.created_at BETWEEN '2024-11-01' AND '2024-11-30'
GROUP BY t.responsible_engineer;
```

### 2.2 项目执行指标（权重25%）

| 指标 | 数据来源 | SQL提取逻辑 |
|-----|---------|------------|
| **按时完成率** | project_task | 直接提取 |
| **BOM提交及时性** | BOM表 | 直接提取 |
| **难度加权产出** | project_task | 需补充 `difficulty_level` 字段 |

```sql
-- 按时完成率（从现有任务表直接提取）
SELECT 
    engineer_id,
    COUNT(*) as total_tasks,
    SUM(CASE WHEN actual_end <= planned_end THEN 1 ELSE 0 END) as on_time_tasks,
    ROUND(SUM(CASE WHEN actual_end <= planned_end THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as on_time_rate
FROM project_task
WHERE status = '已完成'
  AND actual_end BETWEEN '2024-11-01' AND '2024-11-30'
GROUP BY engineer_id;

-- BOM提交及时性
SELECT 
    engineer_id,
    COUNT(*) as total_bom,
    SUM(CASE WHEN actual_submit_date <= planned_submit_date THEN 1 ELSE 0 END) as on_time_bom,
    ROUND(SUM(CASE WHEN actual_submit_date <= planned_submit_date THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as bom_on_time_rate
FROM bom_submission  -- 你现有的BOM表
WHERE actual_submit_date BETWEEN '2024-11-01' AND '2024-11-30'
GROUP BY engineer_id;

-- 难度加权产出（需补充 difficulty_level 字段）
SELECT 
    engineer_id,
    COUNT(*) as task_count,
    SUM(difficulty_level) as weighted_output,
    ROUND(SUM(difficulty_level) * 1.0 / 22, 2) as daily_weighted_output  -- 22为月工作日
FROM project_task
WHERE status = '已完成'
  AND actual_end BETWEEN '2024-11-01' AND '2024-11-30'
GROUP BY engineer_id;
```

### 2.3 成本控制指标（权重20%）

| 指标 | 数据来源 | SQL提取逻辑 |
|-----|---------|------------|
| **标准件使用率** | BOM明细表 | 直接提取或自动计算 |
| **设计复用率** | BOM明细表 | 需增加物料标记 |

```sql
-- 标准件使用率（从BOM明细自动计算）
SELECT 
    b.engineer_id,
    COUNT(d.id) as total_items,
    SUM(CASE WHEN m.is_standard = 1 THEN 1 ELSE 0 END) as standard_items,
    ROUND(SUM(CASE WHEN m.is_standard = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(d.id), 2) as standard_rate
FROM bom_submission b
JOIN bom_detail d ON b.id = d.bom_id
JOIN material m ON d.material_id = m.id  -- 物料主数据表
WHERE b.actual_submit_date BETWEEN '2024-11-01' AND '2024-11-30'
GROUP BY b.engineer_id;

-- 设计复用率（基于物料编码前缀判断）
SELECT 
    b.engineer_id,
    COUNT(d.id) as total_items,
    SUM(CASE 
        WHEN m.material_code LIKE 'STD-%'   -- 标准件
          OR m.material_code LIKE 'COM-%'   -- 通用件
          OR m.reuse_count > 0              -- 已复用过
        THEN 1 ELSE 0 
    END) as reused_items,
    ROUND(SUM(CASE WHEN m.reuse_count > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(d.id), 2) as reuse_rate
FROM bom_submission b
JOIN bom_detail d ON b.id = d.bom_id
JOIN material m ON d.material_id = m.id
WHERE b.actual_submit_date BETWEEN '2024-11-01' AND '2024-11-30'
GROUP BY b.engineer_id;
```

### 2.4 知识沉淀指标（权重15%）

| 指标 | 数据来源 | SQL提取逻辑 |
|-----|---------|------------|
| **文档贡献数量** | 知识库表 | 直接提取 |
| **被引用次数** | 知识库表 | 直接提取 |

```sql
-- 知识贡献统计（从知识库表提取）
SELECT 
    author_id as engineer_id,
    COUNT(*) as doc_count,
    SUM(usage_count) as total_usage
FROM knowledge_contribution  -- 或 knowledge_base_articles
WHERE status = '已发布'
  AND created_at BETWEEN '2024-11-01' AND '2024-11-30'
GROUP BY author_id;
```

### 2.5 团队协作指标（权重10%）

| 指标 | 数据来源 | SQL提取逻辑 |
|-----|---------|------------|
| **跨部门协作评分** | 协作评价表（新增） | 季度采集 |
| **新人带教** | 员工关系表 | 统计导师关系 |

```sql
-- 跨部门协作评分（从新增的协作评价表）
SELECT 
    rated_engineer_id as engineer_id,
    AVG(communication_score) as avg_comm,
    AVG(response_score) as avg_response,
    AVG(quality_score) as avg_quality,
    AVG((communication_score + response_score + quality_score) / 3.0) as avg_collaboration
FROM engineer_collaboration_rating
WHERE rating_period = '2024Q4'
GROUP BY rated_engineer_id;

-- 新人带教统计
SELECT 
    mentor_id as engineer_id,
    COUNT(*) as mentee_count
FROM employee
WHERE mentor_id IS NOT NULL
  AND join_date BETWEEN '2024-10-01' AND '2024-12-31'
GROUP BY mentor_id;
```

---

## 三、需要补充的字段

### 3.1 project_task 表补充字段

```sql
ALTER TABLE project_task 
ADD COLUMN first_pass TINYINT(1) DEFAULT NULL COMMENT '是否一次通过：0否 1是',
ADD COLUMN rework_count INT DEFAULT 0 COMMENT '返工次数',
ADD COLUMN quality_score DECIMAL(3,1) DEFAULT NULL COMMENT '审核人评分(1-5)',
ADD COLUMN difficulty_level INT DEFAULT 3 COMMENT '任务难度(1-5)';

-- 默认难度设置建议
UPDATE project_task SET difficulty_level = 
    CASE task_type
        WHEN '方案设计' THEN 4
        WHEN '详细设计' THEN 3
        WHEN 'BOM编制' THEN 2
        WHEN '现场调试' THEN 4
        ELSE 3
    END
WHERE difficulty_level IS NULL;
```

### 3.2 新增协作评价表

```sql
CREATE TABLE engineer_collaboration_rating (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    rated_engineer_id BIGINT NOT NULL COMMENT '被评价人',
    rater_engineer_id BIGINT NOT NULL COMMENT '评价人',
    rater_department VARCHAR(50) COMMENT '评价人部门',
    project_id BIGINT COMMENT '关联项目(可选)',
    
    communication_score INT NOT NULL COMMENT '沟通配合(1-5)',
    response_score INT NOT NULL COMMENT '响应速度(1-5)',
    quality_score INT NOT NULL COMMENT '交付质量(1-5)',
    comments TEXT COMMENT '评价说明',
    
    rating_period VARCHAR(10) NOT NULL COMMENT '评价周期(2024Q4)',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_rated (rated_engineer_id),
    INDEX idx_period (rating_period),
    UNIQUE KEY uk_rating (rated_engineer_id, rater_engineer_id, rating_period)
) COMMENT '工程师协作评价表';
```

### 3.3 新增绩效汇总表

```sql
CREATE TABLE engineer_performance_summary (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    engineer_id BIGINT NOT NULL COMMENT '工程师ID',
    engineer_name VARCHAR(50) COMMENT '工程师姓名',
    department VARCHAR(50) COMMENT '部门',
    
    period_type ENUM('monthly', 'quarterly', 'yearly') NOT NULL COMMENT '周期类型',
    period_value VARCHAR(10) NOT NULL COMMENT '周期值(2024-11/2024Q4/2024)',
    
    -- 各维度得分（百分制）
    technical_score DECIMAL(5,2) COMMENT '技术能力得分',
    execution_score DECIMAL(5,2) COMMENT '项目执行得分',
    cost_control_score DECIMAL(5,2) COMMENT '成本控制得分',
    knowledge_score DECIMAL(5,2) COMMENT '知识沉淀得分',
    collaboration_score DECIMAL(5,2) COMMENT '团队协作得分',
    
    -- 明细指标
    task_count INT COMMENT '完成任务数',
    on_time_rate DECIMAL(5,2) COMMENT '按时完成率(%)',
    first_pass_rate DECIMAL(5,2) COMMENT '一次通过率(%)',
    ecn_count INT COMMENT '设计变更总数',
    responsible_ecn_count INT COMMENT '责任变更数',
    debug_issue_count INT COMMENT '调试问题数',
    standard_parts_rate DECIMAL(5,2) COMMENT '标准件使用率(%)',
    reuse_rate DECIMAL(5,2) COMMENT '设计复用率(%)',
    doc_contribution_count INT COMMENT '文档贡献数',
    doc_usage_count INT COMMENT '文档被引用数',
    
    -- 综合结果
    total_score DECIMAL(5,2) COMMENT '综合得分',
    grade ENUM('优秀', '良好', '合格', '待改进') COMMENT '评价等级',
    department_rank INT COMMENT '部门排名',
    
    -- 系统字段
    calculated_at DATETIME COMMENT '计算时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_engineer_period (engineer_id, period_type, period_value),
    INDEX idx_period (period_type, period_value),
    INDEX idx_score (total_score DESC)
) COMMENT '工程师绩效汇总表';
```

---

## 四、绩效计算存储过程

```sql
DELIMITER //

CREATE PROCEDURE calculate_engineer_performance(
    IN p_period_type VARCHAR(10),  -- 'monthly' 或 'quarterly'
    IN p_period_value VARCHAR(10)  -- '2024-11' 或 '2024Q4'
)
BEGIN
    DECLARE v_start_date DATE;
    DECLARE v_end_date DATE;
    
    -- 确定日期范围
    IF p_period_type = 'monthly' THEN
        SET v_start_date = CONCAT(p_period_value, '-01');
        SET v_end_date = LAST_DAY(v_start_date);
    ELSEIF p_period_type = 'quarterly' THEN
        -- 解析季度 2024Q4 -> 2024-10-01 to 2024-12-31
        SET v_start_date = CASE RIGHT(p_period_value, 2)
            WHEN 'Q1' THEN CONCAT(LEFT(p_period_value, 4), '-01-01')
            WHEN 'Q2' THEN CONCAT(LEFT(p_period_value, 4), '-04-01')
            WHEN 'Q3' THEN CONCAT(LEFT(p_period_value, 4), '-07-01')
            WHEN 'Q4' THEN CONCAT(LEFT(p_period_value, 4), '-10-01')
        END;
        SET v_end_date = DATE_ADD(DATE_ADD(v_start_date, INTERVAL 3 MONTH), INTERVAL -1 DAY);
    END IF;
    
    -- 插入或更新绩效数据
    INSERT INTO engineer_performance_summary (
        engineer_id, engineer_name, department,
        period_type, period_value,
        task_count, on_time_rate, first_pass_rate,
        ecn_count, responsible_ecn_count, debug_issue_count,
        standard_parts_rate, reuse_rate,
        doc_contribution_count, doc_usage_count,
        technical_score, execution_score, cost_control_score,
        knowledge_score, collaboration_score,
        total_score, grade, department_rank,
        calculated_at
    )
    SELECT 
        e.id as engineer_id,
        e.name as engineer_name,
        e.department,
        p_period_type,
        p_period_value,
        -- 明细指标
        COALESCE(t.task_count, 0),
        COALESCE(t.on_time_rate, 0),
        COALESCE(t.first_pass_rate, 0),
        COALESCE(ecn.total_ecn, 0),
        COALESCE(ecn.responsible_ecn, 0),
        COALESCE(issue.issue_count, 0),
        COALESCE(bom.standard_rate, 0),
        COALESCE(bom.reuse_rate, 0),
        COALESCE(kb.doc_count, 0),
        COALESCE(kb.total_usage, 0),
        -- 维度得分计算（简化版，实际需要更复杂的标准化）
        LEAST(100, COALESCE(t.first_pass_rate, 0) * 0.6 + (100 - COALESCE(ecn.responsible_rate, 0)) * 0.4),
        LEAST(100, COALESCE(t.on_time_rate, 0) * 0.7 + 80 * 0.3),  -- BOM及时性暂用80
        LEAST(100, COALESCE(bom.standard_rate, 0) * 0.5 + COALESCE(bom.reuse_rate, 0) * 1.5),
        LEAST(100, COALESCE(kb.doc_count, 0) * 20 + COALESCE(kb.total_usage, 0) * 5),
        COALESCE(collab.avg_collaboration, 80) * 20,  -- 协作评分转百分制
        -- 综合得分
        (
            LEAST(100, COALESCE(t.first_pass_rate, 0) * 0.6 + (100 - COALESCE(ecn.responsible_rate, 0)) * 0.4) * 0.30 +
            LEAST(100, COALESCE(t.on_time_rate, 0) * 0.7 + 80 * 0.3) * 0.25 +
            LEAST(100, COALESCE(bom.standard_rate, 0) * 0.5 + COALESCE(bom.reuse_rate, 0) * 1.5) * 0.20 +
            LEAST(100, COALESCE(kb.doc_count, 0) * 20 + COALESCE(kb.total_usage, 0) * 5) * 0.15 +
            COALESCE(collab.avg_collaboration, 80) * 20 * 0.10
        ),
        -- 等级
        CASE 
            WHEN (/* 综合得分计算 */) >= 85 THEN '优秀'
            WHEN (/* 综合得分计算 */) >= 70 THEN '良好'
            WHEN (/* 综合得分计算 */) >= 60 THEN '合格'
            ELSE '待改进'
        END,
        0,  -- 排名稍后更新
        NOW()
    FROM engineer_profile e
    LEFT JOIN (
        -- 任务统计子查询
        SELECT 
            engineer_id,
            COUNT(*) as task_count,
            ROUND(SUM(CASE WHEN actual_end <= planned_end THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as on_time_rate,
            ROUND(SUM(CASE WHEN first_pass = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as first_pass_rate
        FROM project_task
        WHERE actual_end BETWEEN v_start_date AND v_end_date
        GROUP BY engineer_id
    ) t ON e.id = t.engineer_id
    LEFT JOIN (
        -- ECN统计子查询
        SELECT 
            engineer_id,
            COUNT(*) as total_ecn,
            SUM(CASE WHEN change_reason = '设计缺陷' AND is_responsible = 1 THEN 1 ELSE 0 END) as responsible_ecn,
            ROUND(SUM(CASE WHEN change_reason = '设计缺陷' AND is_responsible = 1 THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 2) as responsible_rate
        FROM design_change
        WHERE created_at BETWEEN v_start_date AND v_end_date
        GROUP BY engineer_id
    ) ecn ON e.id = ecn.engineer_id
    LEFT JOIN (
        -- 问题统计子查询
        SELECT 
            responsible_engineer as engineer_id,
            COUNT(*) as issue_count
        FROM debug_issue
        WHERE root_cause IN ('设计问题', '选型问题')
          AND created_at BETWEEN v_start_date AND v_end_date
        GROUP BY responsible_engineer
    ) issue ON e.id = issue.engineer_id
    LEFT JOIN (
        -- BOM统计子查询（简化）
        SELECT 
            engineer_id,
            60 as standard_rate,  -- 需要根据实际BOM表结构调整
            30 as reuse_rate
        FROM bom_submission
        WHERE actual_submit_date BETWEEN v_start_date AND v_end_date
        GROUP BY engineer_id
    ) bom ON e.id = bom.engineer_id
    LEFT JOIN (
        -- 知识贡献子查询
        SELECT 
            author_id as engineer_id,
            COUNT(*) as doc_count,
            SUM(usage_count) as total_usage
        FROM knowledge_contribution
        WHERE status = '已发布'
          AND created_at BETWEEN v_start_date AND v_end_date
        GROUP BY author_id
    ) kb ON e.id = kb.engineer_id
    LEFT JOIN (
        -- 协作评分子查询
        SELECT 
            rated_engineer_id as engineer_id,
            AVG((communication_score + response_score + quality_score) / 3.0) as avg_collaboration
        FROM engineer_collaboration_rating
        WHERE rating_period = CASE 
            WHEN p_period_type = 'quarterly' THEN p_period_value
            ELSE CONCAT(LEFT(p_period_value, 4), 'Q', QUARTER(v_start_date))
        END
        GROUP BY rated_engineer_id
    ) collab ON e.id = collab.engineer_id
    WHERE e.department = '机械设计'
    ON DUPLICATE KEY UPDATE
        task_count = VALUES(task_count),
        on_time_rate = VALUES(on_time_rate),
        first_pass_rate = VALUES(first_pass_rate),
        ecn_count = VALUES(ecn_count),
        responsible_ecn_count = VALUES(responsible_ecn_count),
        debug_issue_count = VALUES(debug_issue_count),
        standard_parts_rate = VALUES(standard_parts_rate),
        reuse_rate = VALUES(reuse_rate),
        doc_contribution_count = VALUES(doc_contribution_count),
        doc_usage_count = VALUES(doc_usage_count),
        technical_score = VALUES(technical_score),
        execution_score = VALUES(execution_score),
        cost_control_score = VALUES(cost_control_score),
        knowledge_score = VALUES(knowledge_score),
        collaboration_score = VALUES(collaboration_score),
        total_score = VALUES(total_score),
        grade = VALUES(grade),
        calculated_at = NOW();
    
    -- 更新排名
    SET @rank = 0;
    UPDATE engineer_performance_summary
    SET department_rank = (@rank := @rank + 1)
    WHERE period_type = p_period_type 
      AND period_value = p_period_value
    ORDER BY total_score DESC;
    
END //

DELIMITER ;

-- 调用示例
CALL calculate_engineer_performance('monthly', '2024-11');
CALL calculate_engineer_performance('quarterly', '2024Q4');
```

---

## 五、数据流转架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      日常业务操作                                │
├─────────────────────────────────────────────────────────────────┤
│  任务管理    ECN管理    问题跟踪    BOM管理    知识库           │
│     ↓           ↓          ↓          ↓         ↓              │
│  [任务完成]  [变更提交] [问题登记] [BOM提交] [文档发布]         │
│     ↓           ↓          ↓          ↓         ↓              │
│  first_pass  change_    root_     standard_  usage_            │
│  quality_    reason     cause     parts_     count             │
│  score       is_resp             reuse                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    定时计算任务（每月1日）                        │
├─────────────────────────────────────────────────────────────────┤
│  calculate_engineer_performance('monthly', '2024-11')          │
│                              ↓                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 1. 从各业务表提取原始数据                                 │   │
│  │ 2. 计算各维度得分（标准化处理）                           │   │
│  │ 3. 加权汇总得综合分                                       │   │
│  │ 4. 评定等级和排名                                         │   │
│  │ 5. 写入 engineer_performance_summary                     │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      绩效看板展示                                │
├─────────────────────────────────────────────────────────────────┤
│  部门总览    个人绩效    对比分析    趋势报告                    │
│  - 排名榜    - 五维图    - 人员对比  - 月度趋势                  │
│  - 分布图    - 指标明细  - 差距分析  - 同比环比                  │
│  - 预警      - 项目列表  - 改进建议  - 目标跟踪                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 六、实施步骤

### 第一周：数据层准备
1. [ ] 在 project_task 表增加 4 个字段
2. [ ] 创建 engineer_collaboration_rating 表
3. [ ] 创建 engineer_performance_summary 表
4. [ ] 编写绩效计算存储过程

### 第二周：数据采集入口
1. [ ] 任务完成时增加「一次通过」确认弹窗
2. [ ] ECN审批时增加责任判定
3. [ ] 问题关闭时增加根因归属

### 第三周：前端开发
1. [ ] 部门总览页面
2. [ ] 个人绩效详情页面
3. [ ] 对比分析页面
4. [ ] 指标配置页面

### 第四周：测试上线
1. [ ] 导入历史数据（估算）
2. [ ] 试运行一个月
3. [ ] 收集反馈调整权重
4. [ ] 正式发布
