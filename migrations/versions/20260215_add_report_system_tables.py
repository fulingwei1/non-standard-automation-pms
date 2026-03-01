"""工时报表自动生成系统 - 报表模板、归档、收件人表

Revision ID: 20260215_add_report_system_tables
Revises: 
Create Date: 2026-02-15

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260215_add_report_system_tables'
down_revision = None  # 更新为实际的上一个迁移ID
branch_labels = None
depends_on = None


def upgrade():
    """升级数据库：创建报表系统相关表"""
    
    # ==================== 报表模板表 ====================
    op.create_table(
        'report_template',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
        sa.Column('name', sa.String(100), nullable=False, comment='模板名称'),
        sa.Column('report_type', sa.String(50), nullable=False, comment='报表类型'),
        sa.Column('description', sa.Text(), comment='描述'),
        sa.Column('config', sa.JSON(), comment='模板配置（字段、筛选条件等）'),
        sa.Column('output_format', sa.String(20), nullable=False, server_default='EXCEL', comment='输出格式'),
        sa.Column('frequency', sa.String(20), nullable=False, server_default='MONTHLY', comment='生成频率'),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default=sa.text('1'), comment='是否启用'),
        sa.Column('created_by', sa.Integer(), comment='创建人ID'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        comment='报表模板表'
    )
    
    # 创建索引
    op.create_index('idx_report_type', 'report_template', ['report_type'])
    op.create_index('idx_enabled', 'report_template', ['enabled'])
    op.create_index('idx_created_at', 'report_template', ['created_at'])
    
    # ==================== 报表归档表 ====================
    op.create_table(
        'report_archive',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
        sa.Column('template_id', sa.Integer(), nullable=False, comment='模板ID'),
        sa.Column('report_type', sa.String(50), nullable=False, comment='报表类型'),
        sa.Column('period', sa.String(20), nullable=False, comment='报表周期（如：2026-01）'),
        sa.Column('file_path', sa.String(500), nullable=False, comment='文件路径'),
        sa.Column('file_size', sa.Integer(), comment='文件大小（字节）'),
        sa.Column('row_count', sa.Integer(), comment='数据行数'),
        sa.Column('generated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='生成时间'),
        sa.Column('generated_by', sa.String(50), nullable=False, comment='生成方式（SYSTEM/用户ID）'),
        sa.Column('status', sa.String(20), nullable=False, server_default='SUCCESS', comment='状态'),
        sa.Column('error_message', sa.Text(), comment='失败原因'),
        sa.Column('download_count', sa.Integer(), nullable=False, server_default='0', comment='下载次数'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.ForeignKeyConstraint(['template_id'], ['report_template.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='报表归档表'
    )
    
    # 创建索引
    op.create_index('idx_template_period', 'report_archive', ['template_id', 'period'])
    op.create_index('idx_report_type_archive', 'report_archive', ['report_type'])
    op.create_index('idx_period', 'report_archive', ['period'])
    op.create_index('idx_status_archive', 'report_archive', ['status'])
    op.create_index('idx_generated_at', 'report_archive', ['generated_at'])
    
    # ==================== 报表收件人表 ====================
    op.create_table(
        'report_recipient',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
        sa.Column('template_id', sa.Integer(), nullable=False, comment='模板ID'),
        sa.Column('recipient_type', sa.String(20), nullable=False, comment='收件人类型'),
        sa.Column('recipient_id', sa.Integer(), comment='用户/角色/部门ID'),
        sa.Column('recipient_email', sa.String(200), comment='外部邮箱'),
        sa.Column('delivery_method', sa.String(20), nullable=False, server_default='EMAIL', comment='分发方式'),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default=sa.text('1'), comment='是否启用'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.ForeignKeyConstraint(['template_id'], ['report_template.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='报表收件人表'
    )
    
    # 创建索引
    op.create_index('idx_template_id_recipient', 'report_recipient', ['template_id'])
    op.create_index('idx_recipient_type', 'report_recipient', ['recipient_type'])
    op.create_index('idx_recipient_enabled', 'report_recipient', ['enabled'])
    
    print("✅ 报表系统数据表创建完成")


def downgrade():
    """降级数据库：删除报表系统相关表"""
    
    # 删除索引
    op.drop_index('idx_recipient_enabled', 'report_recipient')
    op.drop_index('idx_recipient_type', 'report_recipient')
    op.drop_index('idx_template_id_recipient', 'report_recipient')
    
    op.drop_index('idx_generated_at', 'report_archive')
    op.drop_index('idx_status_archive', 'report_archive')
    op.drop_index('idx_period', 'report_archive')
    op.drop_index('idx_report_type_archive', 'report_archive')
    op.drop_index('idx_template_period', 'report_archive')
    
    op.drop_index('idx_created_at', 'report_template')
    op.drop_index('idx_enabled', 'report_template')
    op.drop_index('idx_report_type', 'report_template')
    
    # 删除表（注意顺序：先子表后父表）
    op.drop_table('report_recipient')
    op.drop_table('report_archive')
    op.drop_table('report_template')
    
    print("✅ 报表系统数据表删除完成")
