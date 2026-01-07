-- ============================================================
-- PMO、任务中心、售前支持模块 DDL - SQLite 版本
-- 创建日期：2026-01-04
-- ============================================================

-- ==================== PMO 项目管理部 ====================

-- 项目立项申请表
CREATE TABLE IF NOT EXISTS pmo_project_initiation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_no VARCHAR(50) NOT NULL UNIQUE,              -- 申请编号
    project_id INTEGER,                                      -- 项目ID(审批通过后关联)
    project_name VARCHAR(200) NOT NULL,                      -- 项目名称
    project_type VARCHAR(20) DEFAULT 'NEW',                  -- 项目类型:NEW/UPGRADE/MAINTAIN
    project_level VARCHAR(5),                                -- 建议级别:A/B/C
    customer_name VARCHAR(100) NOT NULL,                     -- 客户名称
    contract_no VARCHAR(50),                                 -- 合同编号
    contract_amount DECIMAL(14,2),                          -- 合同金额
    required_start_date DATE,                                -- 要求开始日期
    required_end_date DATE,                                  -- 要求交付日期
    technical_solution_id INTEGER,                           -- 关联技术方案ID
    requirement_summary TEXT,                                -- 需求概述
    technical_difficulty VARCHAR(20),                        -- 技术难度:LOW/MEDIUM/HIGH
    estimated_hours INTEGER,                                 -- 预估工时
    resource_requirements TEXT,                              -- 资源需求说明
    risk_assessment TEXT,                                    -- 初步风险评估
    applicant_id INTEGER NOT NULL,                           -- 申请人ID
    applicant_name VARCHAR(50),                              -- 申请人姓名
    apply_time DATETIME DEFAULT CURRENT_TIMESTAMP,           -- 申请时间
    status VARCHAR(20) DEFAULT 'DRAFT',                      -- 状态:DRAFT/SUBMITTED/REVIEWING/APPROVED/REJECTED
    review_result TEXT,                                      -- 评审结论
    approved_pm_id INTEGER,                                  -- 指定项目经理ID
    approved_level VARCHAR(5),                               -- 评定级别
    approved_at DATETIME,                                    -- 审批时间
    approved_by INTEGER,                                     -- 审批人
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pmo_init_no ON pmo_project_initiation(application_no);
CREATE INDEX IF NOT EXISTS idx_pmo_init_status ON pmo_project_initiation(status);
CREATE INDEX IF NOT EXISTS idx_pmo_init_applicant ON pmo_project_initiation(applicant_id);

-- 项目阶段表
CREATE TABLE IF NOT EXISTS pmo_project_phase (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,                             -- 项目ID
    phase_code VARCHAR(20) NOT NULL,                         -- 阶段编码
    phase_name VARCHAR(50) NOT NULL,                         -- 阶段名称
    phase_order INTEGER DEFAULT 0,                           -- 阶段顺序
    plan_start_date DATE,                                    -- 计划开始
    plan_end_date DATE,                                      -- 计划结束
    actual_start_date DATE,                                  -- 实际开始
    actual_end_date DATE,                                    -- 实际结束
    status VARCHAR(20) DEFAULT 'PENDING',                    -- 状态:PENDING/IN_PROGRESS/COMPLETED/SKIPPED
    progress INTEGER DEFAULT 0,                              -- 进度(%)
    entry_criteria TEXT,                                     -- 入口条件
    exit_criteria TEXT,                                      -- 出口条件
    entry_check_result TEXT,                                 -- 入口检查结果
    exit_check_result TEXT,                                  -- 出口检查结果
    review_required INTEGER DEFAULT 1,                       -- 是否需要评审
    review_date DATE,                                        -- 评审日期
    review_result VARCHAR(20),                               -- 评审结果:PASSED/CONDITIONAL/FAILED
    review_notes TEXT,                                       -- 评审记录
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pmo_phase_project ON pmo_project_phase(project_id);
CREATE INDEX IF NOT EXISTS idx_pmo_phase_code ON pmo_project_phase(phase_code);

-- 项目变更申请表
CREATE TABLE IF NOT EXISTS pmo_change_request (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,                             -- 项目ID
    change_no VARCHAR(50) NOT NULL UNIQUE,                   -- 变更编号
    change_type VARCHAR(20) NOT NULL,                        -- 变更类型:SCOPE/SCHEDULE/COST/RESOURCE/REQUIREMENT/OTHER
    change_level VARCHAR(20) DEFAULT 'MINOR',                -- 变更级别:MINOR/MAJOR/CRITICAL
    title VARCHAR(200) NOT NULL,                             -- 变更标题
    description TEXT NOT NULL,                               -- 变更描述
    reason TEXT,                                             -- 变更原因
    schedule_impact TEXT,                                    -- 进度影响
    cost_impact DECIMAL(12,2),                              -- 成本影响
    quality_impact TEXT,                                     -- 质量影响
    resource_impact TEXT,                                    -- 资源影响
    requestor_id INTEGER NOT NULL,                           -- 申请人ID
    requestor_name VARCHAR(50),                              -- 申请人
    request_time DATETIME DEFAULT CURRENT_TIMESTAMP,         -- 申请时间
    status VARCHAR(20) DEFAULT 'DRAFT',                      -- 状态
    pm_approval INTEGER,                                     -- 项目经理审批
    pm_approval_time DATETIME,                               -- 项目经理审批时间
    manager_approval INTEGER,                                -- 部门经理审批
    manager_approval_time DATETIME,                          -- 部门经理审批时间
    customer_approval INTEGER,                               -- 客户确认
    customer_approval_time DATETIME,                         -- 客户确认时间
    execution_status VARCHAR(20),                            -- 执行状态
    execution_notes TEXT,                                    -- 执行说明
    completed_time DATETIME,                                 -- 完成时间
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pmo_change_project ON pmo_change_request(project_id);
CREATE INDEX IF NOT EXISTS idx_pmo_change_no ON pmo_change_request(change_no);
CREATE INDEX IF NOT EXISTS idx_pmo_change_status ON pmo_change_request(status);

-- 项目风险表
CREATE TABLE IF NOT EXISTS pmo_project_risk (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,                             -- 项目ID
    risk_no VARCHAR(50) NOT NULL UNIQUE,                     -- 风险编号
    risk_category VARCHAR(20) NOT NULL,                      -- 风险类别
    risk_name VARCHAR(200) NOT NULL,                         -- 风险名称
    description TEXT,                                        -- 风险描述
    probability VARCHAR(20),                                 -- 发生概率:LOW/MEDIUM/HIGH
    impact VARCHAR(20),                                      -- 影响程度
    risk_level VARCHAR(20),                                  -- 风险等级
    response_strategy VARCHAR(20),                           -- 应对策略:AVOID/MITIGATE/TRANSFER/ACCEPT
    response_plan TEXT,                                      -- 应对措施
    owner_id INTEGER,                                        -- 责任人ID
    owner_name VARCHAR(50),                                  -- 责任人
    status VARCHAR(20) DEFAULT 'IDENTIFIED',                 -- 状态
    follow_up_date DATE,                                     -- 跟踪日期
    last_update TEXT,                                        -- 最新进展
    trigger_condition TEXT,                                  -- 触发条件
    is_triggered INTEGER DEFAULT 0,                          -- 是否已触发
    triggered_date DATE,                                     -- 触发日期
    closed_date DATE,                                        -- 关闭日期
    closed_reason TEXT,                                      -- 关闭原因
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pmo_risk_project ON pmo_project_risk(project_id);
CREATE INDEX IF NOT EXISTS idx_pmo_risk_level ON pmo_project_risk(risk_level);
CREATE INDEX IF NOT EXISTS idx_pmo_risk_status ON pmo_project_risk(status);

-- 项目成本表
CREATE TABLE IF NOT EXISTS pmo_project_cost (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,                             -- 项目ID
    cost_category VARCHAR(50) NOT NULL,                      -- 成本类别
    cost_item VARCHAR(100) NOT NULL,                         -- 成本项
    budget_amount DECIMAL(12,2) DEFAULT 0,                  -- 预算金额
    actual_amount DECIMAL(12,2) DEFAULT 0,                  -- 实际金额
    cost_month VARCHAR(7),                                   -- 成本月份(YYYY-MM)
    record_date DATE,                                        -- 记录日期
    source_type VARCHAR(50),                                 -- 来源类型
    source_id INTEGER,                                       -- 来源ID
    source_no VARCHAR(50),                                   -- 来源单号
    remarks TEXT,                                            -- 备注
    created_by INTEGER,                                      -- 创建人ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pmo_cost_project ON pmo_project_cost(project_id);
CREATE INDEX IF NOT EXISTS idx_pmo_cost_category ON pmo_project_cost(cost_category);
CREATE INDEX IF NOT EXISTS idx_pmo_cost_month ON pmo_project_cost(cost_month);

-- 项目会议表
CREATE TABLE IF NOT EXISTS pmo_meeting (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,                                      -- 项目ID
    meeting_type VARCHAR(20) NOT NULL,                       -- 会议类型
    meeting_name VARCHAR(200) NOT NULL,                      -- 会议名称
    meeting_date DATE NOT NULL,                              -- 会议日期
    start_time TIME,                                         -- 开始时间
    end_time TIME,                                           -- 结束时间
    location VARCHAR(100),                                   -- 会议地点
    organizer_id INTEGER,                                    -- 组织者ID
    organizer_name VARCHAR(50),                              -- 组织者
    attendees TEXT,                                          -- 参会人员(JSON)
    agenda TEXT,                                             -- 会议议程
    minutes TEXT,                                            -- 会议纪要
    decisions TEXT,                                          -- 会议决议
    action_items TEXT,                                       -- 待办事项(JSON)
    attachments TEXT,                                        -- 会议附件(JSON)
    status VARCHAR(20) DEFAULT 'SCHEDULED',                  -- 状态
    created_by INTEGER,                                      -- 创建人ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pmo_meeting_project ON pmo_meeting(project_id);
CREATE INDEX IF NOT EXISTS idx_pmo_meeting_date ON pmo_meeting(meeting_date);
CREATE INDEX IF NOT EXISTS idx_pmo_meeting_type ON pmo_meeting(meeting_type);

-- 项目资源分配表
CREATE TABLE IF NOT EXISTS pmo_resource_allocation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,                             -- 项目ID
    task_id INTEGER,                                         -- 任务ID
    resource_id INTEGER NOT NULL,                            -- 资源ID(人员ID)
    resource_name VARCHAR(50),                               -- 资源名称
    resource_dept VARCHAR(50),                               -- 所属部门
    resource_role VARCHAR(50),                               -- 项目角色
    allocation_percent INTEGER DEFAULT 100,                  -- 分配比例(%)
    start_date DATE,                                         -- 开始日期
    end_date DATE,                                           -- 结束日期
    planned_hours INTEGER,                                   -- 计划工时
    actual_hours INTEGER DEFAULT 0,                          -- 实际工时
    status VARCHAR(20) DEFAULT 'PLANNED',                    -- 状态
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pmo_alloc_project ON pmo_resource_allocation(project_id);
CREATE INDEX IF NOT EXISTS idx_pmo_alloc_resource ON pmo_resource_allocation(resource_id);

-- 项目结项表
CREATE TABLE IF NOT EXISTS pmo_project_closure (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL UNIQUE,                      -- 项目ID
    acceptance_date DATE,                                    -- 验收日期
    acceptance_result VARCHAR(20),                           -- 验收结果
    acceptance_notes TEXT,                                   -- 验收说明
    project_summary TEXT,                                    -- 项目总结
    achievement TEXT,                                        -- 项目成果
    lessons_learned TEXT,                                    -- 经验教训
    improvement_suggestions TEXT,                            -- 改进建议
    final_budget DECIMAL(14,2),                             -- 最终预算
    final_cost DECIMAL(14,2),                               -- 最终成本
    cost_variance DECIMAL(14,2),                            -- 成本偏差
    final_planned_hours INTEGER,                             -- 最终计划工时
    final_actual_hours INTEGER,                              -- 最终实际工时
    hours_variance INTEGER,                                  -- 工时偏差
    plan_duration INTEGER,                                   -- 计划周期(天)
    actual_duration INTEGER,                                 -- 实际周期(天)
    schedule_variance INTEGER,                               -- 进度偏差(天)
    quality_score INTEGER,                                   -- 质量评分
    customer_satisfaction INTEGER,                           -- 客户满意度
    archive_status VARCHAR(20),                              -- 归档状态
    archive_path VARCHAR(500),                               -- 归档路径
    closure_date DATE,                                       -- 结项日期
    reviewed_by INTEGER,                                     -- 评审人
    review_date DATE,                                        -- 评审日期
    review_result VARCHAR(20),                               -- 评审结果
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);


-- ==================== 个人任务中心 ====================

-- 统一任务表
CREATE TABLE IF NOT EXISTS task_unified (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_code VARCHAR(50) NOT NULL UNIQUE,                   -- 任务编号
    title VARCHAR(200) NOT NULL,                             -- 任务标题
    description TEXT,                                        -- 任务描述
    task_type VARCHAR(20) NOT NULL,                          -- 任务类型
    source_type VARCHAR(50),                                 -- 来源类型
    source_id INTEGER,                                       -- 来源ID
    source_name VARCHAR(200),                                -- 来源名称
    parent_task_id INTEGER,                                  -- 父任务ID
    project_id INTEGER,                                      -- 关联项目ID
    project_code VARCHAR(50),                                -- 项目编号
    project_name VARCHAR(200),                               -- 项目名称
    wbs_code VARCHAR(50),                                    -- WBS编码
    assignee_id INTEGER NOT NULL,                            -- 执行人ID
    assignee_name VARCHAR(50),                               -- 执行人姓名
    assigner_id INTEGER,                                     -- 指派人ID
    assigner_name VARCHAR(50),                               -- 指派人姓名
    plan_start_date DATE,                                    -- 计划开始日期
    plan_end_date DATE,                                      -- 计划结束日期
    actual_start_date DATE,                                  -- 实际开始日期
    actual_end_date DATE,                                    -- 实际完成日期
    deadline DATETIME,                                       -- 截止时间
    estimated_hours DECIMAL(10,2),                          -- 预估工时
    actual_hours DECIMAL(10,2) DEFAULT 0,                   -- 实际工时
    status VARCHAR(20) DEFAULT 'PENDING',                    -- 状态
    progress INTEGER DEFAULT 0,                              -- 进度百分比
    priority VARCHAR(20) DEFAULT 'MEDIUM',                   -- 优先级
    is_urgent INTEGER DEFAULT 0,                             -- 是否紧急
    is_recurring INTEGER DEFAULT 0,                          -- 是否周期性
    recurrence_rule VARCHAR(200),                            -- 周期规则
    recurrence_end_date DATE,                                -- 周期结束日期
    is_transferred INTEGER DEFAULT 0,                        -- 是否转办
    transfer_from_id INTEGER,                                -- 转办来源人ID
    transfer_from_name VARCHAR(50),                          -- 转办来源人
    transfer_reason TEXT,                                    -- 转办原因
    transfer_time DATETIME,                                  -- 转办时间
    deliverables TEXT,                                       -- 交付物清单(JSON)
    attachments TEXT,                                        -- 附件列表(JSON)
    tags TEXT,                                               -- 标签(JSON)
    category VARCHAR(50),                                    -- 分类
    reminder_enabled INTEGER DEFAULT 1,                      -- 是否开启提醒
    reminder_before_hours INTEGER DEFAULT 24,                -- 提前提醒小时数
    created_by INTEGER,                                      -- 创建人ID
    updated_by INTEGER,                                      -- 更新人ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_task_id) REFERENCES task_unified(id)
);

CREATE INDEX IF NOT EXISTS idx_task_code ON task_unified(task_code);
CREATE INDEX IF NOT EXISTS idx_task_assignee ON task_unified(assignee_id);
CREATE INDEX IF NOT EXISTS idx_task_project ON task_unified(project_id);
CREATE INDEX IF NOT EXISTS idx_task_status ON task_unified(status);
CREATE INDEX IF NOT EXISTS idx_task_type ON task_unified(task_type);
CREATE INDEX IF NOT EXISTS idx_task_deadline ON task_unified(deadline);
CREATE INDEX IF NOT EXISTS idx_task_priority ON task_unified(priority);

-- 岗位职责任务模板表
CREATE TABLE IF NOT EXISTS job_duty_template (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    position_id INTEGER NOT NULL,                            -- 岗位ID
    position_name VARCHAR(100),                              -- 岗位名称
    department_id INTEGER,                                   -- 部门ID
    duty_name VARCHAR(200) NOT NULL,                         -- 职责名称
    duty_description TEXT,                                   -- 职责描述
    frequency VARCHAR(20) NOT NULL,                          -- 频率
    day_of_week INTEGER,                                     -- 周几(1-7)
    day_of_month INTEGER,                                    -- 几号(1-31)
    month_of_year INTEGER,                                   -- 几月(1-12)
    auto_generate INTEGER DEFAULT 1,                         -- 自动生成任务
    generate_before_days INTEGER DEFAULT 3,                  -- 提前几天生成
    deadline_offset_days INTEGER DEFAULT 0,                  -- 截止日期偏移
    default_priority VARCHAR(20) DEFAULT 'MEDIUM',           -- 默认优先级
    estimated_hours DECIMAL(10,2),                          -- 预估工时
    is_active INTEGER DEFAULT 1,                             -- 是否启用
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_duty_position ON job_duty_template(position_id);
CREATE INDEX IF NOT EXISTS idx_duty_frequency ON job_duty_template(frequency);

-- 任务操作日志表
CREATE TABLE IF NOT EXISTS task_operation_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,                                -- 任务ID
    operation_type VARCHAR(50) NOT NULL,                     -- 操作类型
    operation_desc TEXT,                                     -- 操作描述
    old_value TEXT,                                          -- 变更前值(JSON)
    new_value TEXT,                                          -- 变更后值(JSON)
    operator_id INTEGER,                                     -- 操作人ID
    operator_name VARCHAR(50),                               -- 操作人
    operation_time DATETIME DEFAULT CURRENT_TIMESTAMP,       -- 操作时间
    FOREIGN KEY (task_id) REFERENCES task_unified(id)
);

CREATE INDEX IF NOT EXISTS idx_task_log_task ON task_operation_log(task_id);
CREATE INDEX IF NOT EXISTS idx_task_log_operator ON task_operation_log(operator_id);

-- 任务评论表
CREATE TABLE IF NOT EXISTS task_comment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,                                -- 任务ID
    content TEXT NOT NULL,                                   -- 评论内容
    comment_type VARCHAR(20) DEFAULT 'COMMENT',              -- 评论类型
    parent_id INTEGER,                                       -- 回复的评论ID
    commenter_id INTEGER,                                    -- 评论人ID
    commenter_name VARCHAR(50),                              -- 评论人
    mentioned_users TEXT,                                    -- @的用户(JSON)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES task_unified(id),
    FOREIGN KEY (parent_id) REFERENCES task_comment(id)
);

CREATE INDEX IF NOT EXISTS idx_task_comment_task ON task_comment(task_id);

-- 任务提醒表
CREATE TABLE IF NOT EXISTS task_reminder (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,                                -- 任务ID
    user_id INTEGER NOT NULL,                                -- 用户ID
    reminder_type VARCHAR(20) NOT NULL,                      -- 提醒类型
    remind_at DATETIME NOT NULL,                             -- 提醒时间
    is_sent INTEGER DEFAULT 0,                               -- 是否已发送
    sent_at DATETIME,                                        -- 发送时间
    channel VARCHAR(20) DEFAULT 'SYSTEM',                    -- 通知渠道
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES task_unified(id)
);

CREATE INDEX IF NOT EXISTS idx_reminder_task ON task_reminder(task_id);
CREATE INDEX IF NOT EXISTS idx_reminder_user ON task_reminder(user_id);
CREATE INDEX IF NOT EXISTS idx_reminder_time ON task_reminder(remind_at);


-- ==================== 售前技术支持 ====================

-- 售前支持工单表
CREATE TABLE IF NOT EXISTS presale_support_ticket (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_no VARCHAR(50) NOT NULL UNIQUE,                   -- 工单编号
    title VARCHAR(200) NOT NULL,                             -- 工单标题
    ticket_type VARCHAR(20) NOT NULL,                        -- 工单类型
    urgency VARCHAR(20) DEFAULT 'NORMAL',                    -- 紧急程度
    description TEXT,                                        -- 详细描述
    customer_id INTEGER,                                     -- 客户ID
    customer_name VARCHAR(100),                              -- 客户名称
    opportunity_id INTEGER,                                  -- 关联商机ID
    project_id INTEGER,                                      -- 关联项目ID
    applicant_id INTEGER NOT NULL,                           -- 申请人ID
    applicant_name VARCHAR(50),                              -- 申请人姓名
    applicant_dept VARCHAR(100),                             -- 申请人部门
    apply_time DATETIME DEFAULT CURRENT_TIMESTAMP,           -- 申请时间
    assignee_id INTEGER,                                     -- 指派处理人ID
    assignee_name VARCHAR(50),                               -- 处理人姓名
    accept_time DATETIME,                                    -- 接单时间
    expected_date DATE,                                      -- 期望完成日期
    deadline DATETIME,                                       -- 截止时间
    status VARCHAR(20) DEFAULT 'PENDING',                    -- 状态
    complete_time DATETIME,                                  -- 完成时间
    actual_hours DECIMAL(10,2),                             -- 实际工时
    satisfaction_score INTEGER,                              -- 满意度评分(1-5)
    feedback TEXT,                                           -- 反馈意见
    created_by INTEGER,                                      -- 创建人ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_presale_ticket_no ON presale_support_ticket(ticket_no);
CREATE INDEX IF NOT EXISTS idx_presale_ticket_status ON presale_support_ticket(status);
CREATE INDEX IF NOT EXISTS idx_presale_ticket_applicant ON presale_support_ticket(applicant_id);
CREATE INDEX IF NOT EXISTS idx_presale_ticket_assignee ON presale_support_ticket(assignee_id);
CREATE INDEX IF NOT EXISTS idx_presale_ticket_customer ON presale_support_ticket(customer_id);

-- 工单交付物表
CREATE TABLE IF NOT EXISTS presale_ticket_deliverable (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,                              -- 工单ID
    name VARCHAR(200) NOT NULL,                              -- 文件名称
    file_type VARCHAR(50),                                   -- 文件类型
    file_path VARCHAR(500),                                  -- 文件路径
    file_size INTEGER,                                       -- 文件大小(bytes)
    version VARCHAR(20) DEFAULT 'V1.0',                      -- 版本号
    status VARCHAR(20) DEFAULT 'DRAFT',                      -- 状态
    reviewer_id INTEGER,                                     -- 审核人ID
    review_time DATETIME,                                    -- 审核时间
    review_comment TEXT,                                     -- 审核意见
    created_by INTEGER,                                      -- 创建人ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticket_id) REFERENCES presale_support_ticket(id)
);

CREATE INDEX IF NOT EXISTS idx_deliverable_ticket ON presale_ticket_deliverable(ticket_id);

-- 工单进度记录表
CREATE TABLE IF NOT EXISTS presale_ticket_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,                              -- 工单ID
    progress_type VARCHAR(20) NOT NULL,                      -- 进度类型
    content TEXT,                                            -- 进度内容
    progress_percent INTEGER,                                -- 进度百分比
    operator_id INTEGER NOT NULL,                            -- 操作人ID
    operator_name VARCHAR(50),                               -- 操作人
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticket_id) REFERENCES presale_support_ticket(id)
);

CREATE INDEX IF NOT EXISTS idx_progress_ticket ON presale_ticket_progress(ticket_id);

-- 技术方案表
CREATE TABLE IF NOT EXISTS presale_solution (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    solution_no VARCHAR(50) NOT NULL UNIQUE,                 -- 方案编号
    name VARCHAR(200) NOT NULL,                              -- 方案名称
    solution_type VARCHAR(20) DEFAULT 'CUSTOM',              -- 方案类型
    industry VARCHAR(50),                                    -- 所属行业
    test_type VARCHAR(100),                                  -- 测试类型
    ticket_id INTEGER,                                       -- 关联工单ID
    customer_id INTEGER,                                     -- 客户ID
    opportunity_id INTEGER,                                  -- 商机ID
    requirement_summary TEXT,                                -- 需求概述
    solution_overview TEXT,                                  -- 方案概述
    technical_spec TEXT,                                     -- 技术规格
    estimated_cost DECIMAL(12,2),                           -- 预估成本
    suggested_price DECIMAL(12,2),                          -- 建议报价
    cost_breakdown TEXT,                                     -- 成本明细(JSON)
    estimated_hours INTEGER,                                 -- 预估工时
    estimated_duration INTEGER,                              -- 预估周期
    status VARCHAR(20) DEFAULT 'DRAFT',                      -- 状态
    version VARCHAR(20) DEFAULT 'V1.0',                      -- 版本
    parent_id INTEGER,                                       -- 父版本ID
    reviewer_id INTEGER,                                     -- 审核人
    review_time DATETIME,                                    -- 审核时间
    review_status VARCHAR(20),                               -- 审核状态
    review_comment TEXT,                                     -- 审核意见
    author_id INTEGER NOT NULL,                              -- 编制人ID
    author_name VARCHAR(50),                                 -- 编制人姓名
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticket_id) REFERENCES presale_support_ticket(id),
    FOREIGN KEY (parent_id) REFERENCES presale_solution(id)
);

CREATE INDEX IF NOT EXISTS idx_solution_no ON presale_solution(solution_no);
CREATE INDEX IF NOT EXISTS idx_solution_ticket ON presale_solution(ticket_id);
CREATE INDEX IF NOT EXISTS idx_solution_customer ON presale_solution(customer_id);
CREATE INDEX IF NOT EXISTS idx_solution_industry ON presale_solution(industry);

-- 方案成本明细表
CREATE TABLE IF NOT EXISTS presale_solution_cost (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    solution_id INTEGER NOT NULL,                            -- 方案ID
    category VARCHAR(50) NOT NULL,                           -- 成本类别
    item_name VARCHAR(200) NOT NULL,                         -- 项目名称
    specification VARCHAR(200),                              -- 规格型号
    unit VARCHAR(20),                                        -- 单位
    quantity DECIMAL(10,2),                                 -- 数量
    unit_price DECIMAL(12,2),                               -- 单价
    amount DECIMAL(12,2),                                   -- 金额
    remark VARCHAR(500),                                     -- 备注
    sort_order INTEGER DEFAULT 0,                            -- 排序
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (solution_id) REFERENCES presale_solution(id)
);

CREATE INDEX IF NOT EXISTS idx_cost_solution ON presale_solution_cost(solution_id);

-- 方案模板库表
CREATE TABLE IF NOT EXISTS presale_solution_template (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_no VARCHAR(50) NOT NULL UNIQUE,                 -- 模板编号
    name VARCHAR(200) NOT NULL,                              -- 模板名称
    industry VARCHAR(50),                                    -- 适用行业
    test_type VARCHAR(100),                                  -- 测试类型
    description TEXT,                                        -- 模板描述
    content_template TEXT,                                   -- 内容模板
    cost_template TEXT,                                      -- 成本模板(JSON)
    attachments TEXT,                                        -- 附件列表(JSON)
    use_count INTEGER DEFAULT 0,                             -- 使用次数
    is_active INTEGER DEFAULT 1,                             -- 是否启用
    created_by INTEGER,                                      -- 创建人ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_template_no ON presale_solution_template(template_no);
CREATE INDEX IF NOT EXISTS idx_template_industry ON presale_solution_template(industry);

-- 售前人员工作负荷表
CREATE TABLE IF NOT EXISTS presale_workload (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,                                -- 人员ID
    stat_date DATE NOT NULL,                                 -- 统计日期
    pending_tickets INTEGER DEFAULT 0,                       -- 待处理工单数
    processing_tickets INTEGER DEFAULT 0,                    -- 进行中工单数
    completed_tickets INTEGER DEFAULT 0,                     -- 已完成工单数
    planned_hours DECIMAL(10,2) DEFAULT 0,                  -- 计划工时
    actual_hours DECIMAL(10,2) DEFAULT 0,                   -- 实际工时
    solutions_count INTEGER DEFAULT 0,                       -- 方案数量
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, stat_date)
);

CREATE INDEX IF NOT EXISTS idx_workload_date ON presale_workload(stat_date);

-- 客户技术档案表
CREATE TABLE IF NOT EXISTS presale_customer_tech_profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL UNIQUE,                     -- 客户ID
    industry VARCHAR(50),                                    -- 所属行业
    business_scope TEXT,                                     -- 业务范围
    common_test_types VARCHAR(500),                          -- 常见测试类型
    technical_requirements TEXT,                             -- 技术要求特点
    quality_standards VARCHAR(500),                          -- 质量标准要求
    existing_equipment TEXT,                                 -- 现有设备情况
    it_infrastructure TEXT,                                  -- IT基础设施
    mes_system VARCHAR(100),                                 -- MES系统类型
    cooperation_history TEXT,                                -- 合作历史
    success_cases TEXT,                                      -- 成功案例
    technical_contacts TEXT,                                 -- 技术联系人(JSON)
    notes TEXT,                                              -- 备注
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 投标记录表
CREATE TABLE IF NOT EXISTS presale_tender_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER,                                       -- 关联工单ID
    opportunity_id INTEGER,                                  -- 关联商机ID
    tender_no VARCHAR(50),                                   -- 招标编号
    tender_name VARCHAR(200) NOT NULL,                       -- 项目名称
    customer_name VARCHAR(100),                              -- 招标单位
    publish_date DATE,                                       -- 发布日期
    deadline DATETIME,                                       -- 投标截止时间
    bid_opening_date DATE,                                   -- 开标日期
    budget_amount DECIMAL(14,2),                            -- 预算金额
    qualification_requirements TEXT,                         -- 资质要求
    technical_requirements TEXT,                             -- 技术要求
    our_bid_amount DECIMAL(14,2),                           -- 我方报价
    technical_score DECIMAL(5,2),                           -- 技术得分
    commercial_score DECIMAL(5,2),                          -- 商务得分
    total_score DECIMAL(5,2),                               -- 总得分
    competitors TEXT,                                        -- 竞争对手信息(JSON)
    result VARCHAR(20) DEFAULT 'PENDING',                    -- 结果
    result_reason TEXT,                                      -- 中标/落标原因分析
    leader_id INTEGER,                                       -- 投标负责人
    team_members TEXT,                                       -- 投标团队(JSON)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticket_id) REFERENCES presale_support_ticket(id)
);

CREATE INDEX IF NOT EXISTS idx_tender_opportunity ON presale_tender_record(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_tender_result ON presale_tender_record(result);

