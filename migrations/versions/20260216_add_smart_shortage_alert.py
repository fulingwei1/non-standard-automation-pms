# -*- coding: utf-8 -*-
"""
添加智能缺料预警系统表

Team 3: 智能缺料预警系统
创建3个新表: shortage_alerts_enhanced, shortage_handling_plans, material_demand_forecasts

Revision ID: team3_smart_shortage_alert
Revises: 
Create Date: 2026-02-16 08:30:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision = 'team3_smart_shortage_alert'
down_revision = None  # 实际应该指向上一个版本
branch_labels = None
depends_on = None


def upgrade():
    """升级数据库"""
    
    # 1. 创建智能缺料预警表
    op.create_table(
        'shortage_alerts_enhanced',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
        sa.Column('alert_no', sa.String(50), nullable=False, unique=True, comment='预警单号'),
        
        # 关联信息
        sa.Column('project_id', sa.Integer(), nullable=False, comment='项目ID'),
        sa.Column('material_id', sa.Integer(), nullable=False, comment='物料ID'),
        sa.Column('work_order_id', sa.Integer(), nullable=True, comment='工单ID'),
        
        # 物料信息快照
        sa.Column('material_code', sa.String(50), nullable=False, comment='物料编码'),
        sa.Column('material_name', sa.String(200), nullable=False, comment='物料名称'),
        sa.Column('material_spec', sa.String(200), comment='物料规格'),
        
        # 需求与库存
        sa.Column('required_qty', sa.Numeric(14, 4), nullable=False, comment='需求数量'),
        sa.Column('available_qty', sa.Numeric(14, 4), default=0, comment='可用数量'),
        sa.Column('shortage_qty', sa.Numeric(14, 4), nullable=False, comment='缺料数量'),
        sa.Column('in_transit_qty', sa.Numeric(14, 4), default=0, comment='在途数量'),
        
        # 预警级别与时间
        sa.Column('alert_level', sa.String(20), nullable=False, comment='预警级别'),
        sa.Column('alert_date', sa.Date(), nullable=False, comment='预警日期'),
        sa.Column('required_date', sa.Date(), comment='需求日期'),
        sa.Column('expected_arrival_date', sa.Date(), comment='预计到货日期'),
        sa.Column('days_to_shortage', sa.Integer(), default=0, comment='距离缺料天数'),
        
        # 影响分析
        sa.Column('impact_projects', mysql.JSON(), comment='受影响项目列表'),
        sa.Column('estimated_delay_days', sa.Integer(), default=0, comment='预计延期天数'),
        sa.Column('estimated_cost_impact', sa.Numeric(14, 2), default=0, comment='预计成本影响'),
        sa.Column('is_critical_path', sa.Boolean(), default=False, comment='是否关键路径'),
        sa.Column('risk_score', sa.Numeric(5, 2), default=0, comment='风险评分 0-100'),
        
        # 预测信息
        sa.Column('demand_forecast_id', sa.Integer(), comment='需求预测ID'),
        sa.Column('confidence_level', sa.Numeric(5, 2), comment='预测置信度 0-100'),
        sa.Column('forecast_accuracy', sa.Numeric(5, 2), comment='历史预测准确率'),
        
        # 状态与处理
        sa.Column('status', sa.String(20), default='PENDING', comment='状态'),
        sa.Column('auto_handled', sa.Boolean(), default=False, comment='是否自动处理'),
        sa.Column('handling_plan_id', sa.Integer(), comment='处理方案ID'),
        
        # 处理时间
        sa.Column('detected_at', sa.DateTime(), default=sa.func.now(), comment='检测时间'),
        sa.Column('notified_at', sa.DateTime(), comment='通知时间'),
        sa.Column('handled_at', sa.DateTime(), comment='处理开始时间'),
        sa.Column('resolved_at', sa.DateTime(), comment='解决时间'),
        
        # 处理结果
        sa.Column('resolution_type', sa.String(50), comment='解决方式'),
        sa.Column('resolution_note', sa.Text(), comment='解决说明'),
        sa.Column('actual_delay_days', sa.Integer(), comment='实际延期天数'),
        sa.Column('actual_cost_impact', sa.Numeric(14, 2), comment='实际成本影响'),
        
        # 扩展信息
        sa.Column('alert_source', sa.String(50), default='AUTO', comment='预警来源'),
        sa.Column('priority_boost', sa.Integer(), default=0, comment='优先级加成'),
        sa.Column('metadata', mysql.JSON(), comment='扩展数据'),
        sa.Column('remark', sa.Text(), comment='备注'),
        
        # 创建人
        sa.Column('created_by', sa.Integer(), comment='创建人ID'),
        sa.Column('handler_id', sa.Integer(), comment='处理人ID'),
        
        # 时间戳
        sa.Column('created_at', sa.DateTime(), default=sa.func.now(), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now(), comment='更新时间'),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.ForeignKeyConstraint(['material_id'], ['materials.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['handler_id'], ['users.id']),
        
        comment='缺料预警表（增强版）- 智能预警系统'
    )
    
    # 创建索引
    op.create_index('idx_shortage_alert_no', 'shortage_alerts_enhanced', ['alert_no'])
    op.create_index('idx_shortage_alert_project', 'shortage_alerts_enhanced', ['project_id'])
    op.create_index('idx_shortage_alert_material', 'shortage_alerts_enhanced', ['material_id'])
    op.create_index('idx_shortage_alert_level', 'shortage_alerts_enhanced', ['alert_level'])
    op.create_index('idx_shortage_alert_status', 'shortage_alerts_enhanced', ['status'])
    op.create_index('idx_shortage_alert_date', 'shortage_alerts_enhanced', ['alert_date'])
    op.create_index('idx_shortage_alert_required_date', 'shortage_alerts_enhanced', ['required_date'])
    op.create_index('idx_shortage_alert_auto_handled', 'shortage_alerts_enhanced', ['auto_handled'])
    
    # 2. 创建缺料处理方案表
    op.create_table(
        'shortage_handling_plans',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
        sa.Column('plan_no', sa.String(50), nullable=False, unique=True, comment='方案编号'),
        
        # 关联预警
        sa.Column('alert_id', sa.Integer(), nullable=False, comment='预警ID'),
        
        # 方案类型
        sa.Column('solution_type', sa.String(50), nullable=False, comment='方案类型'),
        sa.Column('solution_name', sa.String(200), nullable=False, comment='方案名称'),
        sa.Column('solution_description', sa.Text(), comment='方案描述'),
        
        # 方案详情
        sa.Column('target_material_id', sa.Integer(), comment='目标物料ID'),
        sa.Column('target_supplier_id', sa.Integer(), comment='目标供应商ID'),
        sa.Column('target_project_id', sa.Integer(), comment='目标项目ID'),
        
        # 方案参数
        sa.Column('proposed_qty', sa.Numeric(14, 4), comment='建议数量'),
        sa.Column('proposed_date', sa.Date(), comment='建议日期'),
        sa.Column('estimated_lead_time', sa.Integer(), comment='预计交期（天）'),
        sa.Column('estimated_cost', sa.Numeric(14, 2), comment='预计成本'),
        
        # AI评分
        sa.Column('ai_score', sa.Numeric(5, 2), default=0, comment='AI评分 0-100'),
        sa.Column('feasibility_score', sa.Numeric(5, 2), default=0, comment='可行性评分'),
        sa.Column('cost_score', sa.Numeric(5, 2), default=0, comment='成本评分'),
        sa.Column('time_score', sa.Numeric(5, 2), default=0, comment='时间评分'),
        sa.Column('risk_score', sa.Numeric(5, 2), default=0, comment='风险评分'),
        
        # 评分权重说明
        sa.Column('score_weights', mysql.JSON(), comment='评分权重'),
        sa.Column('score_explanation', sa.Text(), comment='评分说明'),
        
        # 优缺点分析
        sa.Column('advantages', mysql.JSON(), comment='优点列表'),
        sa.Column('disadvantages', mysql.JSON(), comment='缺点列表'),
        sa.Column('risks', mysql.JSON(), comment='风险点列表'),
        
        # 推荐优先级
        sa.Column('is_recommended', sa.Boolean(), default=False, comment='是否推荐'),
        sa.Column('recommendation_rank', sa.Integer(), default=999, comment='推荐排名'),
        
        # 执行状态
        sa.Column('status', sa.String(20), default='PENDING', comment='状态'),
        sa.Column('approved_by', sa.Integer(), comment='审批人ID'),
        sa.Column('approved_at', sa.DateTime(), comment='审批时间'),
        sa.Column('executed_at', sa.DateTime(), comment='执行时间'),
        sa.Column('completed_at', sa.DateTime(), comment='完成时间'),
        
        # 执行结果
        sa.Column('execution_result', mysql.JSON(), comment='执行结果'),
        sa.Column('actual_cost', sa.Numeric(14, 2), comment='实际成本'),
        sa.Column('actual_lead_time', sa.Integer(), comment='实际交期'),
        sa.Column('effectiveness_rating', sa.Integer(), comment='方案有效性评分 1-5'),
        
        # 扩展信息
        sa.Column('metadata', mysql.JSON(), comment='扩展数据'),
        sa.Column('remark', sa.Text(), comment='备注'),
        sa.Column('created_by', sa.Integer(), comment='创建人ID'),
        
        # 时间戳
        sa.Column('created_at', sa.DateTime(), default=sa.func.now(), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now(), comment='更新时间'),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['alert_id'], ['shortage_alerts_enhanced.id']),
        sa.ForeignKeyConstraint(['target_material_id'], ['materials.id']),
        sa.ForeignKeyConstraint(['target_project_id'], ['projects.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id']),
        
        comment='缺料处理方案表 - AI智能推荐'
    )
    
    # 创建索引
    op.create_index('idx_handling_plan_no', 'shortage_handling_plans', ['plan_no'])
    op.create_index('idx_handling_plan_alert', 'shortage_handling_plans', ['alert_id'])
    op.create_index('idx_handling_plan_type', 'shortage_handling_plans', ['solution_type'])
    op.create_index('idx_handling_plan_status', 'shortage_handling_plans', ['status'])
    op.create_index('idx_handling_plan_recommended', 'shortage_handling_plans', ['is_recommended'])
    op.create_index('idx_handling_plan_score', 'shortage_handling_plans', ['ai_score'])
    
    # 3. 创建物料需求预测表
    op.create_table(
        'material_demand_forecasts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
        sa.Column('forecast_no', sa.String(50), nullable=False, unique=True, comment='预测编号'),
        
        # 预测目标
        sa.Column('material_id', sa.Integer(), nullable=False, comment='物料ID'),
        sa.Column('project_id', sa.Integer(), comment='项目ID'),
        
        # 预测周期
        sa.Column('forecast_start_date', sa.Date(), nullable=False, comment='预测起始日期'),
        sa.Column('forecast_end_date', sa.Date(), nullable=False, comment='预测结束日期'),
        sa.Column('forecast_horizon_days', sa.Integer(), default=30, comment='预测周期（天）'),
        
        # 预测算法
        sa.Column('algorithm', sa.String(50), nullable=False, comment='预测算法'),
        sa.Column('algorithm_params', mysql.JSON(), comment='算法参数'),
        
        # 预测结果
        sa.Column('forecasted_demand', sa.Numeric(14, 4), nullable=False, comment='预测需求量'),
        sa.Column('lower_bound', sa.Numeric(14, 4), comment='预测下限'),
        sa.Column('upper_bound', sa.Numeric(14, 4), comment='预测上限'),
        sa.Column('confidence_interval', sa.Numeric(5, 2), default=95, comment='置信区间 %'),
        
        # 历史基准
        sa.Column('historical_avg', sa.Numeric(14, 4), comment='历史平均需求'),
        sa.Column('historical_std', sa.Numeric(14, 4), comment='历史标准差'),
        sa.Column('historical_period_days', sa.Integer(), default=90, comment='历史数据周期（天）'),
        
        # 季节性因素
        sa.Column('seasonal_factor', sa.Numeric(5, 2), default=1.0, comment='季节性系数'),
        sa.Column('seasonal_pattern', mysql.JSON(), comment='季节性模式数据'),
        
        # 预测准确率
        sa.Column('accuracy_score', sa.Numeric(5, 2), comment='预测准确率 %'),
        sa.Column('mae', sa.Numeric(14, 4), comment='平均绝对误差 MAE'),
        sa.Column('rmse', sa.Numeric(14, 4), comment='均方根误差 RMSE'),
        sa.Column('mape', sa.Numeric(5, 2), comment='平均绝对百分比误差 MAPE %'),
        
        # 实际对比
        sa.Column('actual_demand', sa.Numeric(14, 4), comment='实际需求量'),
        sa.Column('forecast_error', sa.Numeric(14, 4), comment='预测误差'),
        sa.Column('error_percentage', sa.Numeric(5, 2), comment='误差百分比 %'),
        
        # 预测状态
        sa.Column('status', sa.String(20), default='ACTIVE', comment='状态'),
        sa.Column('forecast_date', sa.Date(), default=sa.func.current_date(), comment='预测生成日期'),
        sa.Column('validated_at', sa.DateTime(), comment='验证时间'),
        
        # 影响因素
        sa.Column('influencing_factors', mysql.JSON(), comment='影响因素'),
        
        # 扩展信息
        sa.Column('metadata', mysql.JSON(), comment='扩展数据'),
        sa.Column('remark', sa.Text(), comment='备注'),
        sa.Column('created_by', sa.Integer(), comment='创建人ID'),
        
        # 时间戳
        sa.Column('created_at', sa.DateTime(), default=sa.func.now(), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now(), comment='更新时间'),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['material_id'], ['materials.id']),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        
        comment='物料需求预测表 - 智能预测引擎'
    )
    
    # 创建索引
    op.create_index('idx_forecast_no', 'material_demand_forecasts', ['forecast_no'])
    op.create_index('idx_forecast_material', 'material_demand_forecasts', ['material_id'])
    op.create_index('idx_forecast_project', 'material_demand_forecasts', ['project_id'])
    op.create_index('idx_forecast_status', 'material_demand_forecasts', ['status'])
    op.create_index('idx_forecast_date', 'material_demand_forecasts', ['forecast_date'])
    op.create_index('idx_forecast_period', 'material_demand_forecasts', ['forecast_start_date', 'forecast_end_date'])


def downgrade():
    """降级数据库"""
    
    # 删除表（逆序）
    op.drop_table('material_demand_forecasts')
    op.drop_table('shortage_handling_plans')
    op.drop_table('shortage_alerts_enhanced')
