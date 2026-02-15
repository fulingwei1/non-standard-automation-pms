-- 异常处理流程增强 - 数据库迁移脚本
-- 创建日期: 2024-02-16
-- 团队: Team 6

-- ================================================
-- 1. 异常处理流程表
-- ================================================
CREATE TABLE IF NOT EXISTS exception_handling_flow (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    exception_id INT NOT NULL COMMENT '异常ID',
    status ENUM('PENDING', 'PROCESSING', 'RESOLVED', 'VERIFIED', 'CLOSED') NOT NULL DEFAULT 'PENDING' COMMENT '流程状态',
    escalation_level ENUM('NONE', 'LEVEL_1', 'LEVEL_2', 'LEVEL_3') NOT NULL DEFAULT 'NONE' COMMENT '升级级别',
    escalation_reason TEXT COMMENT '升级原因',
    escalated_at DATETIME COMMENT '升级时间',
    escalated_to_id INT COMMENT '升级至处理人ID',
    
    pending_duration_minutes INT COMMENT '待处理时长(分钟)',
    processing_duration_minutes INT COMMENT '处理中时长(分钟)',
    total_duration_minutes INT COMMENT '总处理时长(分钟)',
    
    pending_at DATETIME COMMENT '进入待处理时间',
    processing_at DATETIME COMMENT '进入处理中时间',
    resolved_at DATETIME COMMENT '进入已解决时间',
    verified_at DATETIME COMMENT '进入已验证时间',
    closed_at DATETIME COMMENT '进入已关闭时间',
    
    verifier_id INT COMMENT '验证人ID',
    verify_result VARCHAR(20) COMMENT '验证结果：PASS/FAIL',
    verify_comment TEXT COMMENT '验证意见',
    
    remark TEXT COMMENT '备注',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    FOREIGN KEY (exception_id) REFERENCES production_exception(id) ON DELETE CASCADE,
    FOREIGN KEY (escalated_to_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (verifier_id) REFERENCES users(id) ON DELETE SET NULL,
    
    INDEX idx_ehf_exception_id (exception_id),
    INDEX idx_ehf_status (status),
    INDEX idx_ehf_escalation_level (escalation_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='异常处理流程表';

-- ================================================
-- 2. 异常知识库表
-- ================================================
CREATE TABLE IF NOT EXISTS exception_knowledge (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    title VARCHAR(200) NOT NULL COMMENT '知识标题',
    exception_type VARCHAR(20) NOT NULL COMMENT '异常类型',
    exception_level VARCHAR(20) NOT NULL COMMENT '异常级别',
    
    symptom_description TEXT NOT NULL COMMENT '异常症状描述',
    solution TEXT NOT NULL COMMENT '解决方案',
    solution_steps TEXT COMMENT '处理步骤（JSON格式）',
    prevention_measures TEXT COMMENT '预防措施',
    keywords VARCHAR(500) COMMENT '关键词（逗号分隔）',
    
    source_exception_id INT COMMENT '来源异常ID',
    
    reference_count INT NOT NULL DEFAULT 0 COMMENT '引用次数',
    success_count INT NOT NULL DEFAULT 0 COMMENT '成功解决次数',
    last_referenced_at DATETIME COMMENT '最后引用时间',
    
    is_approved BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否已审核',
    approver_id INT COMMENT '审核人ID',
    approved_at DATETIME COMMENT '审核时间',
    
    creator_id INT NOT NULL COMMENT '创建人ID',
    attachments TEXT COMMENT '附件URL（JSON格式）',
    remark TEXT COMMENT '备注',
    
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    FOREIGN KEY (source_exception_id) REFERENCES production_exception(id) ON DELETE SET NULL,
    FOREIGN KEY (creator_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (approver_id) REFERENCES users(id) ON DELETE SET NULL,
    
    INDEX idx_ek_exception_type (exception_type),
    INDEX idx_ek_exception_level (exception_level),
    INDEX idx_ek_keywords (keywords(100)),
    INDEX idx_ek_is_approved (is_approved),
    FULLTEXT INDEX ft_idx_knowledge (title, symptom_description, solution, keywords)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='异常知识库表';

-- ================================================
-- 3. PDCA闭环记录表
-- ================================================
CREATE TABLE IF NOT EXISTS exception_pdca (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    exception_id INT NOT NULL COMMENT '异常ID',
    pdca_no VARCHAR(50) UNIQUE NOT NULL COMMENT 'PDCA编号',
    current_stage ENUM('PLAN', 'DO', 'CHECK', 'ACT', 'COMPLETED') NOT NULL DEFAULT 'PLAN' COMMENT '当前阶段',
    
    -- Plan阶段
    plan_description TEXT COMMENT '问题描述',
    plan_root_cause TEXT COMMENT '根本原因分析',
    plan_target TEXT COMMENT '改善目标',
    plan_measures TEXT COMMENT '改善措施（JSON格式）',
    plan_owner_id INT COMMENT '计划负责人ID',
    plan_deadline DATETIME COMMENT '计划完成期限',
    plan_completed_at DATETIME COMMENT 'Plan阶段完成时间',
    
    -- Do阶段
    do_action_taken TEXT COMMENT '实施内容',
    do_resources_used TEXT COMMENT '使用资源',
    do_difficulties TEXT COMMENT '遇到的困难',
    do_owner_id INT COMMENT '执行负责人ID',
    do_completed_at DATETIME COMMENT 'Do阶段完成时间',
    
    -- Check阶段
    check_result TEXT COMMENT '检查结果',
    check_effectiveness VARCHAR(20) COMMENT '有效性：EFFECTIVE/PARTIAL/INEFFECTIVE',
    check_data TEXT COMMENT '数据分析（JSON格式）',
    check_gap TEXT COMMENT '差距分析',
    check_owner_id INT COMMENT '检查负责人ID',
    check_completed_at DATETIME COMMENT 'Check阶段完成时间',
    
    -- Act阶段
    act_standardization TEXT COMMENT '标准化措施',
    act_horizontal_deployment TEXT COMMENT '横向展开计划',
    act_remaining_issues TEXT COMMENT '遗留问题',
    act_next_cycle TEXT COMMENT '下一轮PDCA计划',
    act_owner_id INT COMMENT '改进负责人ID',
    act_completed_at DATETIME COMMENT 'Act阶段完成时间',
    
    -- 完成状态
    is_completed BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否完成',
    completed_at DATETIME COMMENT '完成时间',
    summary TEXT COMMENT '总结',
    lessons_learned TEXT COMMENT '经验教训',
    
    remark TEXT COMMENT '备注',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    FOREIGN KEY (exception_id) REFERENCES production_exception(id) ON DELETE CASCADE,
    FOREIGN KEY (plan_owner_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (do_owner_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (check_owner_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (act_owner_id) REFERENCES users(id) ON DELETE SET NULL,
    
    INDEX idx_pdca_exception_id (exception_id),
    INDEX idx_pdca_stage (current_stage),
    INDEX idx_pdca_is_completed (is_completed)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='PDCA闭环记录表';

-- ================================================
-- 4. 初始化配置数据
-- ================================================

-- 插入示例知识库数据（可选）
INSERT INTO exception_knowledge (
    title, exception_type, exception_level,
    symptom_description, solution, solution_steps,
    prevention_measures, keywords,
    creator_id, is_approved
) VALUES (
    '设备主轴异响处理指南',
    'EQUIPMENT', 'MAJOR',
    '设备运行时主轴发出尖锐异响，频率约500Hz，伴随明显震动，温度从正常45°C上升至65°C',
    '停机检查主轴轴承，清理旧润滑脂并更换新润滑脂后恢复正常',
    '["1. 立即停机并挂警示牌", "2. 拆卸主轴防护罩", "3. 清理旧润滑脂", "4. 涂抹新润滑脂（型号XXX，用量50g）", "5. 重新装配，低速试运行", "6. 确认正常后恢复生产"]',
    '每月检查主轴润滑情况，每季度更换润滑脂，建立定期保养计划',
    '设备,主轴,异响,润滑,轴承,温度,震动',
    1, TRUE
);

-- ================================================
-- 5. 权限配置（根据实际权限系统调整）
-- ================================================
-- 后续可添加角色权限配置

COMMIT;
