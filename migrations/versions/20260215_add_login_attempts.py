"""添加登录尝试记录表

Revision ID: 20260215_login_attempts
Revises: 
Create Date: 2026-02-15 11:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260215_login_attempts'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """升级数据库：创建login_attempts表"""
    op.create_table(
        'login_attempts',
        sa.Column('id', sa.Integer(), nullable=False, comment='主键ID'),
        sa.Column('username', sa.String(length=50), nullable=False, comment='用户名'),
        sa.Column('ip_address', sa.String(length=45), nullable=False, comment='IP地址（支持IPv6）'),
        sa.Column('user_agent', sa.Text(), nullable=True, comment='用户代理（浏览器信息）'),
        sa.Column('success', sa.Boolean(), nullable=False, server_default='0', comment='是否成功'),
        sa.Column('failure_reason', sa.String(length=50), nullable=True, comment='失败原因：wrong_password, user_not_found, account_locked等'),
        sa.Column('locked', sa.Boolean(), nullable=False, server_default='0', comment='此次尝试后是否导致账户锁定'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='尝试时间'),
        sa.PrimaryKeyConstraint('id'),
        comment='登录尝试记录表'
    )
    
    # 创建索引以提高查询性能
    op.create_index('idx_login_attempts_username', 'login_attempts', ['username'])
    op.create_index('idx_login_attempts_ip_address', 'login_attempts', ['ip_address'])
    op.create_index('idx_login_attempts_success', 'login_attempts', ['success'])
    op.create_index('idx_login_attempts_created_at', 'login_attempts', ['created_at'])
    
    # 创建复合索引用于常见查询
    op.create_index(
        'idx_login_attempts_username_created_at',
        'login_attempts',
        ['username', 'created_at']
    )


def downgrade() -> None:
    """降级数据库：删除login_attempts表"""
    op.drop_index('idx_login_attempts_username_created_at', table_name='login_attempts')
    op.drop_index('idx_login_attempts_created_at', table_name='login_attempts')
    op.drop_index('idx_login_attempts_success', table_name='login_attempts')
    op.drop_index('idx_login_attempts_ip_address', table_name='login_attempts')
    op.drop_index('idx_login_attempts_username', table_name='login_attempts')
    op.drop_table('login_attempts')
