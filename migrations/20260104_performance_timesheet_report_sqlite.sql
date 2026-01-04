-- ============================================================
-- 绩效、工时、报表中心模块 DDL - SQLite 版本
-- 创建日期：2026-01-04
-- ============================================================

-- ==================== 绩效管理 ====================

-- 绩效考核周期表
CREATE TABLE IF NOT EXISTS performance_period (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    period_code VARCHAR(20) NOT NULL UNIQUE,                 -- 周期编码
    period_name VARCHAR(100) NOT NULL,                       -- 周期名称
    period_type VARCHAR(20) NOT NULL,                        -- 周期类型
    start_date DATE NOT NULL,                                -- 开始日期
    end_date DATE NOT NULL,                                  -- 结束日期
    status VARCHAR(20) DEFAULT 'PENDING',                    -- 状态
    is_active INTEGER DEFAULT 1,                             -- 是否当前周期
    calculate_date DATE,                                     -- 计算日期
    review_deadline DATE,                                    -- 评审截止日期
    finalize_date DATE,                                      -- 定稿日期
    remarks TEXT,                                            -- 备注
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_perf_period_code ON performance_period(period_code);
CREATE INDEX IF NOT EXISTS idx_perf_period_dates ON performance_period(start_date, end_date);

-- 绩效考核指标配置表
CREATE TABLE IF NOT EXISTS performance_indicator (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    indicator_code VARCHAR(50) NOT NULL UNIQUE,              -- 指标编码
    indicator_name VARCHAR(100) NOT NULL,                    -- 指标名称
    indicator_type VARCHAR(20) NOT NULL,                     -- 指标类型
    calculation_formula TEXT,                                -- 计算公式说明
    data_source VARCHAR(100),                                -- 数据来源
    weight DECIMAL(5,2) DEFAULT 0,                          -- 权重(%)
    scoring_rules TEXT,                                      -- 评分规则(JSON)
    max_score INTEGER DEFAULT 100,                           -- 最高分
    min_score INTEGER DEFAULT 0,                             -- 最低分
    apply_to_roles TEXT,                                     -- 适用角色列表(JSON)
    apply_to_depts TEXT,                                     -- 适用部门列表(JSON)
    is_active INTEGER DEFAULT 1,                             -- 是否启用
    sort_order INTEGER DEFAULT 0,                            -- 排序
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_perf_indicator_code ON performance_indicator(indicator_code);
CREATE INDEX IF NOT EXISTS idx_perf_indicator_type ON performance_indicator(indicator_type);

-- 绩效结果表
CREATE TABLE IF NOT EXISTS performance_result (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    period_id INTEGER NOT NULL,                              -- 考核周期ID
    user_id INTEGER NOT NULL,                                -- 用户ID
    user_name VARCHAR(50),                                   -- 用户姓名
    department_id INTEGER,                                   -- 部门ID
    department_name VARCHAR(100),                            -- 部门名称
    total_score DECIMAL(5,2),                               -- 综合得分
    level VARCHAR(20),                                       -- 绩效等级
    workload_score DECIMAL(5,2),                            -- 工作量得分
    task_score DECIMAL(5,2),                                -- 任务得分
    quality_score DECIMAL(5,2),                             -- 质量得分
    collaboration_score DECIMAL(5,2),                       -- 协作得分
    growth_score DECIMAL(5,2),                              -- 成长得分
    indicator_scores TEXT,                                   -- 各指标详细得分(JSON)
    dept_rank INTEGER,                                       -- 部门排名
    company_rank INTEGER,                                    -- 公司排名
    score_change DECIMAL(5,2),                              -- 得分变化
    rank_change INTEGER,                                     -- 排名变化
    highlights TEXT,                                         -- 亮点(JSON)
    improvements TEXT,                                       -- 待改进(JSON)
    status VARCHAR(20) DEFAULT 'CALCULATED',                 -- 状态
    calculated_at DATETIME,                                  -- 计算时间
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (period_id) REFERENCES performance_period(id)
);

CREATE INDEX IF NOT EXISTS idx_perf_result_period ON performance_result(period_id);
CREATE INDEX IF NOT EXISTS idx_perf_result_user ON performance_result(user_id);
CREATE INDEX IF NOT EXISTS idx_perf_result_dept ON performance_result(department_id);
CREATE INDEX IF NOT EXISTS idx_perf_result_score ON performance_result(total_score);

-- 绩效评价表
CREATE TABLE IF NOT EXISTS performance_evaluation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    result_id INTEGER NOT NULL,                              -- 绩效结果ID
    evaluator_id INTEGER NOT NULL,                           -- 评价人ID
    evaluator_name VARCHAR(50),                              -- 评价人姓名
    evaluator_role VARCHAR(50),                              -- 评价人角色
    overall_comment TEXT,                                    -- 总体评价
    strength_comment TEXT,                                   -- 优点评价
    improvement_comment TEXT,                                -- 改进建议
    adjusted_level VARCHAR(20),                              -- 调整后等级
    adjustment_reason TEXT,                                  -- 调整原因
    evaluated_at DATETIME DEFAULT CURRENT_TIMESTAMP,         -- 评价时间
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (result_id) REFERENCES performance_result(id)
);

CREATE INDEX IF NOT EXISTS idx_perf_eval_result ON performance_evaluation(result_id);
CREATE INDEX IF NOT EXISTS idx_perf_eval_evaluator ON performance_evaluation(evaluator_id);

-- 绩效申诉表
CREATE TABLE IF NOT EXISTS performance_appeal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    result_id INTEGER NOT NULL,                              -- 绩效结果ID
    appellant_id INTEGER NOT NULL,                           -- 申诉人ID
    appellant_name VARCHAR(50),                              -- 申诉人姓名
    appeal_reason TEXT NOT NULL,                             -- 申诉理由
    expected_score DECIMAL(5,2),                            -- 期望得分
    supporting_evidence TEXT,                                -- 支撑证据
    attachments TEXT,                                        -- 附件(JSON)
    appeal_time DATETIME DEFAULT CURRENT_TIMESTAMP,          -- 申诉时间
    status VARCHAR(20) DEFAULT 'PENDING',                    -- 状态
    handler_id INTEGER,                                      -- 处理人ID
    handler_name VARCHAR(50),                                -- 处理人
    handle_time DATETIME,                                    -- 处理时间
    handle_result TEXT,                                      -- 处理结果
    new_score DECIMAL(5,2),                                 -- 调整后得分
    new_level VARCHAR(20),                                   -- 调整后等级
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (result_id) REFERENCES performance_result(id)
);

CREATE INDEX IF NOT EXISTS idx_appeal_result ON performance_appeal(result_id);
CREATE INDEX IF NOT EXISTS idx_appeal_appellant ON performance_appeal(appellant_id);
CREATE INDEX IF NOT EXISTS idx_appeal_status ON performance_appeal(status);

-- 项目贡献记录表
CREATE TABLE IF NOT EXISTS project_contribution (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    period_id INTEGER NOT NULL,                              -- 考核周期ID
    user_id INTEGER NOT NULL,                                -- 用户ID
    project_id INTEGER NOT NULL,                             -- 项目ID
    project_code VARCHAR(50),                                -- 项目编号
    project_name VARCHAR(200),                               -- 项目名称
    task_count INTEGER DEFAULT 0,                            -- 任务数
    completed_tasks INTEGER DEFAULT 0,                       -- 完成任务数
    on_time_tasks INTEGER DEFAULT 0,                         -- 按时完成数
    hours_spent DECIMAL(10,2) DEFAULT 0,                    -- 投入工时
    hours_percentage DECIMAL(5,2),                          -- 工时占比(%)
    contribution_level VARCHAR(20),                          -- 贡献等级
    role_in_project VARCHAR(50),                             -- 项目中角色
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (period_id) REFERENCES performance_period(id)
);

CREATE INDEX IF NOT EXISTS idx_contrib_period ON project_contribution(period_id);
CREATE INDEX IF NOT EXISTS idx_contrib_user ON project_contribution(user_id);
CREATE INDEX IF NOT EXISTS idx_contrib_project ON project_contribution(project_id);

-- 排行榜快照表
CREATE TABLE IF NOT EXISTS performance_ranking_snapshot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    period_id INTEGER NOT NULL,                              -- 考核周期ID
    scope_type VARCHAR(20) NOT NULL,                         -- 范围类型
    scope_id INTEGER,                                        -- 范围ID
    scope_name VARCHAR(100),                                 -- 范围名称
    total_members INTEGER,                                   -- 总人数
    avg_score DECIMAL(5,2),                                 -- 平均分
    max_score DECIMAL(5,2),                                 -- 最高分
    min_score DECIMAL(5,2),                                 -- 最低分
    median_score DECIMAL(5,2),                              -- 中位数
    level_distribution TEXT,                                 -- 等级分布(JSON)
    ranking_data TEXT,                                       -- 排名数据(JSON)
    snapshot_time DATETIME DEFAULT CURRENT_TIMESTAMP,        -- 快照时间
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (period_id) REFERENCES performance_period(id)
);

CREATE INDEX IF NOT EXISTS idx_ranking_period ON performance_ranking_snapshot(period_id);
CREATE INDEX IF NOT EXISTS idx_ranking_scope ON performance_ranking_snapshot(scope_type, scope_id);


-- ==================== 工时管理 ====================

-- 工时记录表
CREATE TABLE IF NOT EXISTS timesheet (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timesheet_no VARCHAR(50),                                -- 工时单号
    user_id INTEGER NOT NULL,                                -- 用户ID
    user_name VARCHAR(50),                                   -- 用户姓名
    department_id INTEGER,                                   -- 部门ID
    department_name VARCHAR(100),                            -- 部门名称
    project_id INTEGER NOT NULL,                             -- 项目ID
    project_code VARCHAR(50),                                -- 项目编号
    project_name VARCHAR(200),                               -- 项目名称
    task_id INTEGER,                                         -- 任务ID
    task_name VARCHAR(200),                                  -- 任务名称
    assign_id INTEGER,                                       -- 任务分配ID
    work_date DATE NOT NULL,                                 -- 工作日期
    hours DECIMAL(5,2) NOT NULL,                            -- 工时(小时)
    overtime_type VARCHAR(20) DEFAULT 'NORMAL',              -- 加班类型
    work_content TEXT,                                       -- 工作内容
    work_result TEXT,                                        -- 工作成果
    progress_before INTEGER,                                 -- 更新前进度(%)
    progress_after INTEGER,                                  -- 更新后进度(%)
    status VARCHAR(20) DEFAULT 'DRAFT',                      -- 状态
    submit_time DATETIME,                                    -- 提交时间
    approver_id INTEGER,                                     -- 审核人ID
    approver_name VARCHAR(50),                               -- 审核人
    approve_time DATETIME,                                   -- 审核时间
    approve_comment TEXT,                                    -- 审核意见
    created_by INTEGER,                                      -- 创建人ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ts_user ON timesheet(user_id);
CREATE INDEX IF NOT EXISTS idx_ts_project ON timesheet(project_id);
CREATE INDEX IF NOT EXISTS idx_ts_date ON timesheet(work_date);
CREATE INDEX IF NOT EXISTS idx_ts_status ON timesheet(status);
CREATE INDEX IF NOT EXISTS idx_ts_user_date ON timesheet(user_id, work_date);

-- 工时批次表（周工时表）
CREATE TABLE IF NOT EXISTS timesheet_batch (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_no VARCHAR(50) NOT NULL UNIQUE,                    -- 批次编号
    user_id INTEGER NOT NULL,                                -- 用户ID
    user_name VARCHAR(50),                                   -- 用户姓名
    department_id INTEGER,                                   -- 部门ID
    week_start DATE NOT NULL,                                -- 周开始日期
    week_end DATE NOT NULL,                                  -- 周结束日期
    year INTEGER,                                            -- 年份
    week_number INTEGER,                                     -- 周数
    total_hours DECIMAL(6,2) DEFAULT 0,                     -- 总工时
    normal_hours DECIMAL(6,2) DEFAULT 0,                    -- 正常工时
    overtime_hours DECIMAL(6,2) DEFAULT 0,                  -- 加班工时
    entries_count INTEGER DEFAULT 0,                         -- 记录条数
    status VARCHAR(20) DEFAULT 'DRAFT',                      -- 状态
    submit_time DATETIME,                                    -- 提交时间
    approver_id INTEGER,                                     -- 审核人ID
    approver_name VARCHAR(50),                               -- 审核人
    approve_time DATETIME,                                   -- 审核时间
    approve_comment TEXT,                                    -- 审核意见
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_batch_user ON timesheet_batch(user_id);
CREATE INDEX IF NOT EXISTS idx_batch_week ON timesheet_batch(week_start, week_end);
CREATE INDEX IF NOT EXISTS idx_batch_status ON timesheet_batch(status);
CREATE UNIQUE INDEX IF NOT EXISTS idx_batch_user_week ON timesheet_batch(user_id, week_start);

-- 工时汇总表
CREATE TABLE IF NOT EXISTS timesheet_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    summary_type VARCHAR(20) NOT NULL,                       -- 汇总类型
    user_id INTEGER,                                         -- 用户ID
    project_id INTEGER,                                      -- 项目ID
    department_id INTEGER,                                   -- 部门ID
    year INTEGER NOT NULL,                                   -- 年份
    month INTEGER NOT NULL,                                  -- 月份
    total_hours DECIMAL(8,2) DEFAULT 0,                     -- 总工时
    normal_hours DECIMAL(8,2) DEFAULT 0,                    -- 正常工时
    overtime_hours DECIMAL(8,2) DEFAULT 0,                  -- 加班工时
    weekend_hours DECIMAL(8,2) DEFAULT 0,                   -- 周末工时
    holiday_hours DECIMAL(8,2) DEFAULT 0,                   -- 节假日工时
    standard_hours DECIMAL(8,2),                            -- 标准工时
    work_days INTEGER,                                       -- 工作日数
    entries_count INTEGER DEFAULT 0,                         -- 记录条数
    projects_count INTEGER DEFAULT 0,                        -- 参与项目数
    project_breakdown TEXT,                                  -- 项目分布(JSON)
    daily_breakdown TEXT,                                    -- 每日分布(JSON)
    task_breakdown TEXT,                                     -- 任务分布(JSON)
    status_breakdown TEXT,                                   -- 状态分布(JSON)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_summary_user_month ON timesheet_summary(user_id, year, month);
CREATE INDEX IF NOT EXISTS idx_summary_project_month ON timesheet_summary(project_id, year, month);
CREATE INDEX IF NOT EXISTS idx_summary_dept_month ON timesheet_summary(department_id, year, month);

-- 加班申请表
CREATE TABLE IF NOT EXISTS overtime_application (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_no VARCHAR(50) NOT NULL UNIQUE,              -- 申请编号
    applicant_id INTEGER NOT NULL,                           -- 申请人ID
    applicant_name VARCHAR(50),                              -- 申请人姓名
    department_id INTEGER,                                   -- 部门ID
    overtime_type VARCHAR(20) NOT NULL,                      -- 加班类型
    overtime_date DATE NOT NULL,                             -- 加班日期
    start_time DATETIME,                                     -- 开始时间
    end_time DATETIME,                                       -- 结束时间
    planned_hours DECIMAL(5,2) NOT NULL,                    -- 计划加班时长
    project_id INTEGER,                                      -- 项目ID
    project_name VARCHAR(200),                               -- 项目名称
    reason TEXT NOT NULL,                                    -- 加班原因
    work_content TEXT,                                       -- 加班内容
    status VARCHAR(20) DEFAULT 'PENDING',                    -- 状态
    approver_id INTEGER,                                     -- 审批人ID
    approver_name VARCHAR(50),                               -- 审批人
    approve_time DATETIME,                                   -- 审批时间
    approve_comment TEXT,                                    -- 审批意见
    actual_hours DECIMAL(5,2),                              -- 实际加班时长
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_overtime_applicant ON overtime_application(applicant_id);
CREATE INDEX IF NOT EXISTS idx_overtime_date ON overtime_application(overtime_date);
CREATE INDEX IF NOT EXISTS idx_overtime_status ON overtime_application(status);

-- 工时审批记录表
CREATE TABLE IF NOT EXISTS timesheet_approval_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timesheet_id INTEGER,                                    -- 工时记录ID
    batch_id INTEGER,                                        -- 工时批次ID
    approver_id INTEGER NOT NULL,                            -- 审批人ID
    approver_name VARCHAR(50),                               -- 审批人
    action VARCHAR(20) NOT NULL,                             -- 审批动作
    comment TEXT,                                            -- 审批意见
    approved_at DATETIME DEFAULT CURRENT_TIMESTAMP,          -- 审批时间
    FOREIGN KEY (timesheet_id) REFERENCES timesheet(id),
    FOREIGN KEY (batch_id) REFERENCES timesheet_batch(id)
);

CREATE INDEX IF NOT EXISTS idx_approval_timesheet ON timesheet_approval_log(timesheet_id);
CREATE INDEX IF NOT EXISTS idx_approval_batch ON timesheet_approval_log(batch_id);
CREATE INDEX IF NOT EXISTS idx_approval_approver ON timesheet_approval_log(approver_id);

-- 工时填报规则表
CREATE TABLE IF NOT EXISTS timesheet_rule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_code VARCHAR(50) NOT NULL UNIQUE,                   -- 规则编码
    rule_name VARCHAR(100) NOT NULL,                         -- 规则名称
    apply_to_depts TEXT,                                     -- 适用部门(JSON)
    apply_to_roles TEXT,                                     -- 适用角色(JSON)
    standard_daily_hours DECIMAL(4,2) DEFAULT 8,            -- 标准日工时
    max_daily_hours DECIMAL(4,2) DEFAULT 12,                -- 每日最大工时
    min_entry_hours DECIMAL(4,2) DEFAULT 0.5,               -- 最小记录单位
    submit_deadline_day INTEGER DEFAULT 1,                   -- 提交截止日
    allow_backfill_days INTEGER DEFAULT 7,                   -- 允许补录天数
    require_approval INTEGER DEFAULT 1,                      -- 是否需要审批
    remind_unfilled INTEGER DEFAULT 1,                       -- 未填报提醒
    remind_time VARCHAR(10) DEFAULT '09:00',                 -- 提醒时间
    is_active INTEGER DEFAULT 1,                             -- 是否启用
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_rule_code ON timesheet_rule(rule_code);


-- ==================== 报表中心 ====================

-- 报表模板表
CREATE TABLE IF NOT EXISTS report_template (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_code VARCHAR(50) NOT NULL UNIQUE,               -- 模板编码
    template_name VARCHAR(100) NOT NULL,                     -- 模板名称
    report_type VARCHAR(30) NOT NULL,                        -- 报表类型
    description TEXT,                                        -- 模板描述
    sections TEXT,                                           -- 模块配置(JSON)
    metrics_config TEXT,                                     -- 指标配置(JSON)
    charts_config TEXT,                                      -- 图表配置(JSON)
    filters_config TEXT,                                     -- 筛选器配置(JSON)
    style_config TEXT,                                       -- 样式配置(JSON)
    default_for_roles TEXT,                                  -- 默认适用角色(JSON)
    use_count INTEGER DEFAULT 0,                             -- 使用次数
    is_system INTEGER DEFAULT 0,                             -- 是否系统内置
    is_active INTEGER DEFAULT 1,                             -- 是否启用
    created_by INTEGER,                                      -- 创建人ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_rpt_tpl_code ON report_template(template_code);
CREATE INDEX IF NOT EXISTS idx_rpt_tpl_type ON report_template(report_type);

-- 报表定义表
CREATE TABLE IF NOT EXISTS report_definition (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_code VARCHAR(50) NOT NULL UNIQUE,                 -- 报表编码
    report_name VARCHAR(100) NOT NULL,                       -- 报表名称
    template_id INTEGER,                                     -- 模板ID
    report_type VARCHAR(30) NOT NULL,                        -- 报表类型
    period_type VARCHAR(20) DEFAULT 'MONTHLY',               -- 周期类型
    scope_type VARCHAR(20),                                  -- 范围类型
    scope_ids TEXT,                                          -- 范围ID列表(JSON)
    filters TEXT,                                            -- 过滤条件(JSON)
    sections TEXT,                                           -- 模块配置(JSON)
    metrics TEXT,                                            -- 指标配置(JSON)
    owner_id INTEGER NOT NULL,                               -- 所有者ID
    owner_name VARCHAR(50),                                  -- 所有者
    is_shared INTEGER DEFAULT 0,                             -- 是否共享
    shared_to TEXT,                                          -- 共享给(JSON)
    is_active INTEGER DEFAULT 1,                             -- 是否启用
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (template_id) REFERENCES report_template(id)
);

CREATE INDEX IF NOT EXISTS idx_rpt_def_code ON report_definition(report_code);
CREATE INDEX IF NOT EXISTS idx_rpt_def_owner ON report_definition(owner_id);
CREATE INDEX IF NOT EXISTS idx_rpt_def_type ON report_definition(report_type);

-- 报表生成记录表
CREATE TABLE IF NOT EXISTS report_generation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_definition_id INTEGER,                            -- 报表定义ID
    template_id INTEGER,                                     -- 模板ID
    report_type VARCHAR(30) NOT NULL,                        -- 报表类型
    report_title VARCHAR(200),                               -- 报表标题
    period_type VARCHAR(20),                                 -- 周期类型
    period_start DATE,                                       -- 周期开始
    period_end DATE,                                         -- 周期结束
    scope_type VARCHAR(20),                                  -- 范围类型
    scope_id INTEGER,                                        -- 范围ID
    viewer_role VARCHAR(50),                                 -- 查看角色
    report_data TEXT,                                        -- 报表数据(JSON)
    status VARCHAR(20) DEFAULT 'GENERATED',                  -- 状态
    generated_by INTEGER,                                    -- 生成人ID
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,         -- 生成时间
    export_format VARCHAR(10),                               -- 导出格式
    export_path VARCHAR(500),                                -- 导出路径
    exported_at DATETIME,                                    -- 导出时间
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (report_definition_id) REFERENCES report_definition(id),
    FOREIGN KEY (template_id) REFERENCES report_template(id)
);

CREATE INDEX IF NOT EXISTS idx_rpt_gen_definition ON report_generation(report_definition_id);
CREATE INDEX IF NOT EXISTS idx_rpt_gen_type ON report_generation(report_type);
CREATE INDEX IF NOT EXISTS idx_rpt_gen_time ON report_generation(generated_at);

-- 报表订阅表
CREATE TABLE IF NOT EXISTS report_subscription (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subscriber_id INTEGER NOT NULL,                          -- 订阅人ID
    subscriber_name VARCHAR(50),                             -- 订阅人
    report_definition_id INTEGER,                            -- 报表定义ID
    template_id INTEGER,                                     -- 模板ID
    report_type VARCHAR(30) NOT NULL,                        -- 报表类型
    scope_type VARCHAR(20),                                  -- 范围类型
    scope_id INTEGER,                                        -- 范围ID
    frequency VARCHAR(20) NOT NULL,                          -- 频率
    send_day INTEGER,                                        -- 发送日
    send_time VARCHAR(10) DEFAULT '09:00',                   -- 发送时间
    channels TEXT,                                           -- 发送渠道(JSON)
    email VARCHAR(100),                                      -- 邮箱
    export_format VARCHAR(10) DEFAULT 'PDF',                 -- 导出格式
    is_active INTEGER DEFAULT 1,                             -- 是否启用
    last_sent_at DATETIME,                                   -- 上次发送时间
    next_send_at DATETIME,                                   -- 下次发送时间
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (report_definition_id) REFERENCES report_definition(id),
    FOREIGN KEY (template_id) REFERENCES report_template(id)
);

CREATE INDEX IF NOT EXISTS idx_subscription_user ON report_subscription(subscriber_id);
CREATE INDEX IF NOT EXISTS idx_subscription_type ON report_subscription(report_type);

-- 数据导入任务表
CREATE TABLE IF NOT EXISTS data_import_task (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_no VARCHAR(50) NOT NULL UNIQUE,                     -- 任务编号
    import_type VARCHAR(50) NOT NULL,                        -- 导入类型
    target_table VARCHAR(100),                               -- 目标表
    file_name VARCHAR(200) NOT NULL,                         -- 文件名
    file_path VARCHAR(500),                                  -- 文件路径
    file_size INTEGER,                                       -- 文件大小
    status VARCHAR(20) DEFAULT 'PENDING',                    -- 状态
    total_rows INTEGER DEFAULT 0,                            -- 总行数
    success_rows INTEGER DEFAULT 0,                          -- 成功行数
    failed_rows INTEGER DEFAULT 0,                           -- 失败行数
    skipped_rows INTEGER DEFAULT 0,                          -- 跳过行数
    validation_errors TEXT,                                  -- 校验错误(JSON)
    imported_by INTEGER NOT NULL,                            -- 导入人ID
    started_at DATETIME,                                     -- 开始时间
    completed_at DATETIME,                                   -- 完成时间
    error_message TEXT,                                      -- 错误信息
    error_log_path VARCHAR(500),                             -- 错误日志路径
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_import_task_no ON data_import_task(task_no);
CREATE INDEX IF NOT EXISTS idx_import_type ON data_import_task(import_type);
CREATE INDEX IF NOT EXISTS idx_import_status ON data_import_task(status);
CREATE INDEX IF NOT EXISTS idx_import_user ON data_import_task(imported_by);

-- 数据导出任务表
CREATE TABLE IF NOT EXISTS data_export_task (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_no VARCHAR(50) NOT NULL UNIQUE,                     -- 任务编号
    export_type VARCHAR(50) NOT NULL,                        -- 导出类型
    export_format VARCHAR(10) DEFAULT 'XLSX',                -- 导出格式
    query_params TEXT,                                       -- 查询参数(JSON)
    status VARCHAR(20) DEFAULT 'PENDING',                    -- 状态
    file_name VARCHAR(200),                                  -- 文件名
    file_path VARCHAR(500),                                  -- 文件路径
    file_size INTEGER,                                       -- 文件大小
    total_rows INTEGER DEFAULT 0,                            -- 总行数
    exported_by INTEGER NOT NULL,                            -- 导出人ID
    started_at DATETIME,                                     -- 开始时间
    completed_at DATETIME,                                   -- 完成时间
    expires_at DATETIME,                                     -- 过期时间
    download_count INTEGER DEFAULT 0,                        -- 下载次数
    last_download_at DATETIME,                               -- 最后下载时间
    error_message TEXT,                                      -- 错误信息
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_export_task_no ON data_export_task(task_no);
CREATE INDEX IF NOT EXISTS idx_export_type ON data_export_task(export_type);
CREATE INDEX IF NOT EXISTS idx_export_status ON data_export_task(status);
CREATE INDEX IF NOT EXISTS idx_export_user ON data_export_task(exported_by);

-- 导入模板表
CREATE TABLE IF NOT EXISTS import_template (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_code VARCHAR(50) NOT NULL UNIQUE,               -- 模板编码
    template_name VARCHAR(100) NOT NULL,                     -- 模板名称
    import_type VARCHAR(50) NOT NULL,                        -- 导入类型
    template_file_path VARCHAR(500),                         -- 模板文件路径
    field_mappings TEXT NOT NULL,                            -- 字段映射(JSON)
    validation_rules TEXT,                                   -- 校验规则(JSON)
    description TEXT,                                        -- 说明
    instructions TEXT,                                       -- 填写说明
    is_active INTEGER DEFAULT 1,                             -- 是否启用
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_import_tpl_code ON import_template(template_code);
CREATE INDEX IF NOT EXISTS idx_import_tpl_type ON import_template(import_type);


-- ==================== 初始数据 ====================

-- 绩效指标配置
INSERT OR IGNORE INTO performance_indicator (indicator_code, indicator_name, indicator_type, weight, max_score, is_active, sort_order) VALUES
('WORKLOAD_HOURS', '工时饱和度', 'WORKLOAD', 20.00, 100, 1, 1),
('WORKLOAD_OVERTIME', '加班贡献', 'WORKLOAD', 5.00, 100, 1, 2),
('TASK_COMPLETION', '任务完成率', 'TASK', 25.00, 100, 1, 3),
('TASK_ONTIME', '按时完成率', 'TASK', 15.00, 100, 1, 4),
('QUALITY_DEFECT', '缺陷率', 'QUALITY', 15.00, 100, 1, 5),
('QUALITY_REWORK', '返工率', 'QUALITY', 10.00, 100, 1, 6),
('COLLAB_ASSIST', '协作支持', 'COLLABORATION', 5.00, 100, 1, 7),
('COLLAB_RESPONSE', '响应及时性', 'COLLABORATION', 5.00, 100, 1, 8);

-- 工时填报规则
INSERT OR IGNORE INTO timesheet_rule (rule_code, rule_name, standard_daily_hours, max_daily_hours, min_entry_hours, submit_deadline_day, allow_backfill_days, require_approval, is_active) VALUES
('DEFAULT_RULE', '默认填报规则', 8.00, 12.00, 0.50, 1, 7, 1, 1);

-- 报表模板
INSERT OR IGNORE INTO report_template (template_code, template_name, report_type, description, is_system, is_active) VALUES
('TPL_PROJECT_WEEKLY_STD', '标准项目周报', 'PROJECT_WEEKLY', '包含进度、任务、风险、下周计划', 1, 1),
('TPL_PROJECT_WEEKLY_EXEC', '项目周报-管理层版', 'PROJECT_WEEKLY', '精简版，聚焦关键指标和风险', 1, 1),
('TPL_DEPT_MONTHLY', '部门月报', 'DEPT_MONTHLY', '部门月度工作汇总', 1, 1),
('TPL_COST_ANALYSIS', '成本分析报表', 'COST_ANALYSIS', '项目成本明细分析', 1, 1),
('TPL_WORKLOAD', '负荷分析报表', 'WORKLOAD_ANALYSIS', '人员工作负荷分析', 1, 1);

