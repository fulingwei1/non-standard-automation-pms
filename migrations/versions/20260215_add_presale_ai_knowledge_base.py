"""
添加售前AI知识库和问答表

迁移ID: 20260215_add_presale_ai_knowledge_base
创建时间: 2026-02-15
"""

def upgrade(cursor):
    """升级数据库"""
    
    # 创建AI知识库案例表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS presale_knowledge_case (
            id INT PRIMARY KEY AUTO_INCREMENT COMMENT '案例ID',
            case_name VARCHAR(200) NOT NULL COMMENT '案例名称',
            industry VARCHAR(100) COMMENT '行业分类',
            equipment_type VARCHAR(100) COMMENT '设备类型',
            customer_name VARCHAR(200) COMMENT '客户名称',
            project_amount DECIMAL(12,2) COMMENT '项目金额',
            project_summary TEXT COMMENT '项目摘要',
            technical_highlights TEXT COMMENT '技术亮点',
            success_factors TEXT COMMENT '成功要素',
            lessons_learned TEXT COMMENT '失败教训',
            tags JSON COMMENT '标签数组',
            embedding BLOB COMMENT '向量嵌入',
            quality_score DECIMAL(3,2) DEFAULT 0.50 COMMENT '案例质量评分 0-1',
            is_public BOOLEAN DEFAULT TRUE COMMENT '是否公开',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
            INDEX idx_industry (industry),
            INDEX idx_equipment_type (equipment_type),
            INDEX idx_quality_score (quality_score),
            INDEX idx_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='售前AI知识库案例表';
    """)
    
    # 创建智能问答记录表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS presale_ai_qa (
            id INT PRIMARY KEY AUTO_INCREMENT COMMENT '问答ID',
            question TEXT NOT NULL COMMENT '问题',
            answer TEXT COMMENT '答案',
            matched_cases JSON COMMENT '关联的案例IDs',
            confidence_score DECIMAL(3,2) COMMENT '置信度评分 0-1',
            feedback_score INT COMMENT '用户反馈1-5星',
            created_by INT COMMENT '创建人ID',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            INDEX idx_created_by (created_by),
            INDEX idx_created_at (created_at),
            INDEX idx_feedback_score (feedback_score)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='售前AI智能问答记录表';
    """)
    
    print("✅ AI知识库表创建成功")


def downgrade(cursor):
    """降级数据库"""
    cursor.execute("DROP TABLE IF EXISTS presale_ai_qa")
    cursor.execute("DROP TABLE IF EXISTS presale_knowledge_case")
    print("✅ AI知识库表删除成功")
