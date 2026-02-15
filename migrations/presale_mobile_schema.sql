-- ==========================================
-- 移动端AI销售助手 - 数据库迁移脚本
-- Team 9: AI实时销售助手（移动端）
-- ==========================================

-- 移动助手对话记录表
CREATE TABLE IF NOT EXISTS presale_mobile_assistant_chat (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    user_id INT NOT NULL COMMENT '用户ID',
    presale_ticket_id INT COMMENT '售前工单ID',
    question TEXT COMMENT '提问内容',
    answer TEXT COMMENT 'AI回答',
    question_type ENUM('technical', 'competitor', 'case', 'pricing', 'other') DEFAULT 'other' COMMENT '问题类型：技术/竞品/案例/报价/其他',
    context JSON COMMENT '对话上下文',
    response_time INT COMMENT '响应时间（毫秒）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_user_id (user_id),
    INDEX idx_presale_ticket_id (presale_ticket_id),
    INDEX idx_question_type (question_type),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='移动助手对话记录表';

-- 拜访记录表
CREATE TABLE IF NOT EXISTS presale_visit_record (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    presale_ticket_id INT NOT NULL COMMENT '售前工单ID',
    customer_id INT NOT NULL COMMENT '客户ID',
    visit_date DATE NOT NULL COMMENT '拜访日期',
    visit_type ENUM('first_contact', 'follow_up', 'demo', 'negotiation', 'closing') NOT NULL COMMENT '拜访类型：初次接触/跟进/演示/谈判/签约',
    attendees JSON COMMENT '参会人员',
    discussion_points TEXT COMMENT '讨论要点',
    customer_feedback TEXT COMMENT '客户反馈',
    next_steps TEXT COMMENT '下一步行动',
    audio_recording_url VARCHAR(255) COMMENT '录音文件URL',
    ai_generated_summary TEXT COMMENT 'AI生成的摘要',
    created_by INT NOT NULL COMMENT '创建人ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_presale_ticket_id (presale_ticket_id),
    INDEX idx_customer_id (customer_id),
    INDEX idx_visit_date (visit_date),
    INDEX idx_visit_type (visit_type),
    INDEX idx_created_by (created_by),
    FOREIGN KEY (presale_ticket_id) REFERENCES presale_tickets(id) ON DELETE CASCADE,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='拜访记录表';

-- 移动端快速估价记录表
CREATE TABLE IF NOT EXISTS presale_mobile_quick_estimate (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    presale_ticket_id INT COMMENT '售前工单ID',
    customer_id INT COMMENT '客户ID',
    equipment_photo_url VARCHAR(255) COMMENT '设备照片URL',
    recognized_equipment VARCHAR(200) COMMENT '识别的设备名称',
    equipment_description TEXT COMMENT '设备描述',
    estimated_cost INT COMMENT '预估成本（元）',
    price_range_min INT COMMENT '报价范围最小值（元）',
    price_range_max INT COMMENT '报价范围最大值（元）',
    bom_items JSON COMMENT 'BOM物料清单',
    confidence_score INT COMMENT '识别置信度（0-100）',
    created_by INT NOT NULL COMMENT '创建人ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_presale_ticket_id (presale_ticket_id),
    INDEX idx_customer_id (customer_id),
    INDEX idx_created_by (created_by),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='移动端快速估价记录表';

-- 移动端离线数据同步表
CREATE TABLE IF NOT EXISTS presale_mobile_offline_data (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    user_id INT NOT NULL COMMENT '用户ID',
    data_type VARCHAR(50) NOT NULL COMMENT '数据类型：chat/visit/estimate',
    local_id VARCHAR(100) COMMENT '本地临时ID',
    data_payload JSON COMMENT '数据内容',
    sync_status VARCHAR(20) DEFAULT 'pending' COMMENT '同步状态：pending/synced/failed',
    synced_at TIMESTAMP NULL COMMENT '同步时间',
    error_message TEXT COMMENT '错误信息',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_user_id (user_id),
    INDEX idx_data_type (data_type),
    INDEX idx_sync_status (sync_status),
    INDEX idx_local_id (local_id),
    UNIQUE KEY uk_user_local (user_id, local_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='移动端离线数据同步表';

-- ==========================================
-- 索引优化说明：
-- 1. user_id: 用于查询用户相关数据
-- 2. presale_ticket_id: 关联售前工单
-- 3. customer_id: 关联客户
-- 4. created_at: 时间范围查询
-- 5. sync_status: 同步状态查询
-- ==========================================
