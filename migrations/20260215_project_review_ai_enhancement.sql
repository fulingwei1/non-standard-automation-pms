-- 项目复盘AI增强迁移脚本
-- 添加AI生成相关字段

-- 1. 为project_reviews表添加AI字段
ALTER TABLE project_reviews
ADD COLUMN ai_generated BOOLEAN DEFAULT FALSE COMMENT 'AI是否生成',
ADD COLUMN ai_generated_at DATETIME NULL COMMENT 'AI生成时间',
ADD COLUMN ai_summary TEXT NULL COMMENT 'AI生成的摘要',
ADD COLUMN ai_insights JSON NULL COMMENT 'AI洞察（JSON格式）',
ADD COLUMN embedding BLOB NULL COMMENT '向量嵌入（用于相似度搜索）',
ADD COLUMN quality_score DECIMAL(3,2) DEFAULT 0.50 COMMENT '报告质量评分0-1';

-- 2. 为project_lessons表添加AI字段
ALTER TABLE project_lessons
ADD COLUMN ai_extracted BOOLEAN DEFAULT FALSE COMMENT 'AI是否提取',
ADD COLUMN ai_confidence DECIMAL(3,2) DEFAULT 0.00 COMMENT 'AI置信度0-1',
ADD COLUMN similar_cases JSON NULL COMMENT '相似案例ID列表',
ADD COLUMN embedding BLOB NULL COMMENT '向量嵌入';

-- 3. 为project_best_practices表添加AI字段
ALTER TABLE project_best_practices
ADD COLUMN ai_identified BOOLEAN DEFAULT FALSE COMMENT 'AI是否识别',
ADD COLUMN ai_confidence DECIMAL(3,2) DEFAULT 0.00 COMMENT 'AI置信度0-1',
ADD COLUMN effectiveness_score DECIMAL(3,2) DEFAULT 0.00 COMMENT '有效性评分0-1',
ADD COLUMN embedding BLOB NULL COMMENT '向量嵌入';

-- 4. 创建项目复盘-知识库关联表
CREATE TABLE IF NOT EXISTS project_review_knowledge_sync (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    review_id INT NOT NULL COMMENT '复盘报告ID',
    knowledge_case_id INT NOT NULL COMMENT '知识库案例ID',
    sync_type VARCHAR(20) NOT NULL DEFAULT 'AUTO' COMMENT '同步类型: AUTO/MANUAL',
    sync_status VARCHAR(20) NOT NULL DEFAULT 'PENDING' COMMENT '同步状态: PENDING/SUCCESS/FAILED',
    sync_time DATETIME NULL COMMENT '同步时间',
    error_message TEXT NULL COMMENT '错误信息',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    FOREIGN KEY (review_id) REFERENCES project_reviews(id) ON DELETE CASCADE,
    FOREIGN KEY (knowledge_case_id) REFERENCES presale_knowledge_case(id) ON DELETE CASCADE,
    INDEX idx_review (review_id),
    INDEX idx_knowledge (knowledge_case_id),
    INDEX idx_sync_status (sync_status),
    INDEX idx_sync_time (sync_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目复盘-知识库同步表';

-- 5. 创建项目复盘AI处理日志表
CREATE TABLE IF NOT EXISTS project_review_ai_logs (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    review_id INT NOT NULL COMMENT '复盘报告ID',
    ai_function VARCHAR(50) NOT NULL COMMENT 'AI功能: GENERATE/EXTRACT/COMPARE/SYNC',
    input_data JSON NULL COMMENT '输入数据',
    output_data JSON NULL COMMENT '输出数据',
    processing_time INT NULL COMMENT '处理时间(毫秒)',
    token_usage INT NULL COMMENT 'Token使用量',
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING' COMMENT '状态: PENDING/SUCCESS/FAILED',
    error_message TEXT NULL COMMENT '错误信息',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    FOREIGN KEY (review_id) REFERENCES project_reviews(id) ON DELETE CASCADE,
    INDEX idx_review (review_id),
    INDEX idx_function (ai_function),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目复盘AI处理日志表';

-- 6. 为现有表添加索引优化
CREATE INDEX idx_project_reviews_ai_generated ON project_reviews(ai_generated);
CREATE INDEX idx_project_reviews_quality_score ON project_reviews(quality_score);
CREATE INDEX idx_project_lessons_ai_extracted ON project_lessons(ai_extracted);
CREATE INDEX idx_project_lessons_confidence ON project_lessons(ai_confidence);

-- 7. 添加全文索引以支持搜索
ALTER TABLE project_reviews ADD FULLTEXT INDEX ft_idx_content (success_factors, problems, improvements);
ALTER TABLE project_lessons ADD FULLTEXT INDEX ft_idx_description (title, description, root_cause);
