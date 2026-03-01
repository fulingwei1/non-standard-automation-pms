"""
添加售前AI赢率预测表
Date: 2026-02-15
Team: Team 4 - AI智能赢率预测模型
"""

from sqlalchemy import text
from alembic import op


# revision identifiers, used by Alembic.
revision = '20260215_presale_ai_win_rate'
down_revision = None  # 设置为最新的迁移版本
branch_labels = None
depends_on = None


def upgrade():
    """创建售前AI赢率预测相关表"""
    
    # 1. 创建 presale_ai_win_rate 表
    op.execute(text("""
    CREATE TABLE IF NOT EXISTS presale_ai_win_rate (
        id INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
        presale_ticket_id INT NOT NULL COMMENT '售前工单ID',
        win_rate_score DECIMAL(5,2) COMMENT '赢率分数 (0-100)',
        confidence_interval VARCHAR(20) COMMENT '置信区间，如：60-80%',
        influencing_factors JSON COMMENT '影响因素列表: [{factor, impact, type: positive/negative}]',
        competitor_analysis JSON COMMENT '竞品分析: {competitors: [], our_advantages: [], competitor_advantages: [], strategy: []}',
        improvement_suggestions JSON COMMENT '改进建议: {short_term: [], mid_term: [], milestones: []}',
        ai_analysis_report TEXT COMMENT 'AI生成的完整分析报告',
        model_version VARCHAR(50) COMMENT '使用的模型版本',
        predicted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '预测时间',
        created_by INT COMMENT '创建人ID',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_presale_ai_win_rate_ticket (presale_ticket_id),
        INDEX idx_presale_ai_win_rate_score (win_rate_score),
        INDEX idx_presale_ai_win_rate_predicted_at (predicted_at),
        FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI赢率预测记录表';
    """))
    
    # 2. 创建 presale_win_rate_history 表
    op.execute(text("""
    CREATE TABLE IF NOT EXISTS presale_win_rate_history (
        id INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
        presale_ticket_id INT NOT NULL COMMENT '售前工单ID',
        predicted_win_rate DECIMAL(5,2) COMMENT '预测赢率 (0-100)',
        prediction_id INT COMMENT '关联的预测记录ID',
        actual_result ENUM('won', 'lost', 'pending') DEFAULT 'pending' COMMENT '实际结果',
        actual_win_date DATETIME COMMENT '实际赢单日期',
        actual_lost_date DATETIME COMMENT '实际失单日期',
        features JSON COMMENT '所有输入特征的快照',
        prediction_error DECIMAL(5,2) COMMENT '预测误差',
        is_correct_prediction INT COMMENT '预测是否正确 (1=正确, 0=错误, NULL=待定)',
        result_updated_at DATETIME COMMENT '结果更新时间',
        updated_by INT COMMENT '结果更新人ID',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_presale_win_rate_history_ticket (presale_ticket_id),
        INDEX idx_presale_win_rate_history_result (actual_result),
        INDEX idx_presale_win_rate_history_prediction (prediction_id),
        INDEX idx_presale_win_rate_history_created (created_at),
        FOREIGN KEY (prediction_id) REFERENCES presale_ai_win_rate(id) ON DELETE SET NULL,
        FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='赢率历史记录表（用于模型训练）';
    """))
    
    print("✅ 售前AI赢率预测表创建成功")


def downgrade():
    """删除售前AI赢率预测相关表"""
    
    op.execute(text("DROP TABLE IF EXISTS presale_win_rate_history"))
    op.execute(text("DROP TABLE IF EXISTS presale_ai_win_rate"))
    
    print("✅ 售前AI赢率预测表删除成功")
