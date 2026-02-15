"""质量风险识别系统 - 风险检测和测试推荐表

Revision ID: 20260215_quality_risk_detection
Revises: 20260215_add_report_system_tables
Create Date: 2026-02-15

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '20260215_quality_risk_detection'
down_revision = '20260215_add_report_system_tables'
branch_labels = None
depends_on = None


def upgrade():
    """升级数据库：创建质量风险识别系统相关表"""
    
    # ==================== 质量风险检测表 ====================
    op.create_table(
        'quality_risk_detection',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
        
        # 关联信息
        sa.Column('project_id', sa.Integer(), nullable=False, comment='项目ID'),
        sa.Column('module_name', sa.String(200), comment='模块名称'),
        sa.Column('task_id', sa.Integer(), comment='任务ID'),
        sa.Column('detection_date', sa.Date(), nullable=False, comment='检测日期'),
        
        # 数据来源
        sa.Column('source_type', sa.String(50), nullable=False, comment='数据来源类型：WORK_LOG/PROGRESS/MANUAL'),
        sa.Column('source_id', sa.Integer(), comment='来源记录ID'),
        
        # 风险信号
        sa.Column('risk_signals', sa.JSON(), comment='检测到的风险信号列表'),
        sa.Column('risk_keywords', sa.JSON(), comment='触发的关键词列表'),
        sa.Column('abnormal_patterns', sa.JSON(), comment='异常模式描述'),
        
        # 质量风险评估
        sa.Column('risk_level', sa.String(20), nullable=False, comment='风险等级：LOW/MEDIUM/HIGH/CRITICAL'),
        sa.Column('risk_score', sa.Numeric(5, 2), nullable=False, comment='风险评分 (0-100)'),
        sa.Column('risk_category', sa.String(50), comment='风险类别：BUG/PERFORMANCE/STABILITY/COMPATIBILITY'),
        
        # 问题预测
        sa.Column('predicted_issues', sa.JSON(), comment='预测可能出现的问题'),
        sa.Column('rework_probability', sa.Numeric(5, 2), comment='返工概率 (0-100)'),
        sa.Column('estimated_impact_days', sa.Integer(), comment='预估影响天数'),
        
        # AI分析结果
        sa.Column('ai_analysis', sa.JSON(), comment='AI详细分析结果'),
        sa.Column('ai_confidence', sa.Numeric(5, 2), comment='AI置信度 (0-100)'),
        sa.Column('analysis_model', sa.String(50), comment='使用的AI模型'),
        
        # 状态管理
        sa.Column('status', sa.String(20), nullable=False, server_default='DETECTED', comment='状态：DETECTED/CONFIRMED/FALSE_POSITIVE/RESOLVED'),
        sa.Column('confirmed_by', sa.Integer(), comment='确认人ID'),
        sa.Column('confirmed_at', sa.DateTime(), comment='确认时间'),
        sa.Column('resolution_note', sa.Text(), comment='处理说明'),
        
        # 审计字段
        sa.Column('created_by', sa.Integer(), comment='创建人ID'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), comment='更新时间'),
        
        # 外键
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['confirmed_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        
        sa.PrimaryKeyConstraint('id'),
        comment='质量风险检测表'
    )
    
    # 创建索引
    op.create_index('idx_qrd_project', 'quality_risk_detection', ['project_id'])
    op.create_index('idx_qrd_detection_date', 'quality_risk_detection', ['detection_date'])
    op.create_index('idx_qrd_risk_level', 'quality_risk_detection', ['risk_level'])
    op.create_index('idx_qrd_status', 'quality_risk_detection', ['status'])
    op.create_index('idx_qrd_source', 'quality_risk_detection', ['source_type', 'source_id'])
    op.create_index('idx_qrd_module', 'quality_risk_detection', ['project_id', 'module_name'])
    
    # ==================== 质量测试推荐表 ====================
    op.create_table(
        'quality_test_recommendations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
        
        # 关联信息
        sa.Column('project_id', sa.Integer(), nullable=False, comment='项目ID'),
        sa.Column('detection_id', sa.Integer(), comment='关联的风险检测ID'),
        sa.Column('recommendation_date', sa.Date(), nullable=False, comment='推荐日期'),
        
        # 测试重点区域
        sa.Column('focus_areas', sa.JSON(), nullable=False, comment='测试重点区域列表'),
        sa.Column('priority_modules', sa.JSON(), comment='优先测试模块'),
        sa.Column('risk_modules', sa.JSON(), comment='高风险模块列表'),
        
        # 测试建议
        sa.Column('test_types', sa.JSON(), comment='推荐的测试类型'),
        sa.Column('test_scenarios', sa.JSON(), comment='测试场景建议'),
        sa.Column('test_coverage_target', sa.Numeric(5, 2), comment='目标测试覆盖率 (0-100)'),
        
        # 资源分配建议
        sa.Column('recommended_testers', sa.Integer(), comment='推荐测试人员数'),
        sa.Column('recommended_days', sa.Integer(), comment='推荐测试天数'),
        sa.Column('priority_level', sa.String(20), nullable=False, comment='优先级：LOW/MEDIUM/HIGH/URGENT'),
        
        # AI推荐理由
        sa.Column('ai_reasoning', sa.Text(), comment='AI推荐理由'),
        sa.Column('risk_summary', sa.Text(), comment='风险汇总说明'),
        sa.Column('historical_data', sa.JSON(), comment='参考的历史数据'),
        
        # 测试计划生成
        sa.Column('test_plan_generated', sa.Boolean(), nullable=False, server_default=sa.text('0'), comment='是否已生成测试计划'),
        sa.Column('test_plan_id', sa.Integer(), comment='关联的测试计划ID'),
        
        # 执行状态
        sa.Column('status', sa.String(20), nullable=False, server_default='PENDING', comment='状态：PENDING/ACCEPTED/IN_PROGRESS/COMPLETED/REJECTED'),
        sa.Column('acceptance_note', sa.Text(), comment='接受/拒绝说明'),
        sa.Column('actual_test_days', sa.Integer(), comment='实际测试天数'),
        sa.Column('actual_coverage', sa.Numeric(5, 2), comment='实际测试覆盖率'),
        
        # 效果评估
        sa.Column('bugs_found', sa.Integer(), comment='发现的BUG数量'),
        sa.Column('critical_bugs_found', sa.Integer(), comment='发现的严重BUG数量'),
        sa.Column('recommendation_accuracy', sa.Numeric(5, 2), comment='推荐准确度评分 (0-100)'),
        
        # 审计字段
        sa.Column('created_by', sa.Integer(), comment='创建人ID'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), comment='更新时间'),
        
        # 外键
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['detection_id'], ['quality_risk_detection.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        
        sa.PrimaryKeyConstraint('id'),
        comment='质量测试推荐表'
    )
    
    # 创建索引
    op.create_index('idx_qtr_project', 'quality_test_recommendations', ['project_id'])
    op.create_index('idx_qtr_recommendation_date', 'quality_test_recommendations', ['recommendation_date'])
    op.create_index('idx_qtr_priority', 'quality_test_recommendations', ['priority_level'])
    op.create_index('idx_qtr_status', 'quality_test_recommendations', ['status'])
    op.create_index('idx_qtr_detection', 'quality_test_recommendations', ['detection_id'])


def downgrade():
    """降级数据库：删除质量风险识别系统相关表"""
    
    # 删除索引和表（逆序）
    op.drop_index('idx_qtr_detection', table_name='quality_test_recommendations')
    op.drop_index('idx_qtr_status', table_name='quality_test_recommendations')
    op.drop_index('idx_qtr_priority', table_name='quality_test_recommendations')
    op.drop_index('idx_qtr_recommendation_date', table_name='quality_test_recommendations')
    op.drop_index('idx_qtr_project', table_name='quality_test_recommendations')
    op.drop_table('quality_test_recommendations')
    
    op.drop_index('idx_qrd_module', table_name='quality_risk_detection')
    op.drop_index('idx_qrd_source', table_name='quality_risk_detection')
    op.drop_index('idx_qrd_status', table_name='quality_risk_detection')
    op.drop_index('idx_qrd_risk_level', table_name='quality_risk_detection')
    op.drop_index('idx_qrd_detection_date', table_name='quality_risk_detection')
    op.drop_index('idx_qrd_project', table_name='quality_risk_detection')
    op.drop_table('quality_risk_detection')
