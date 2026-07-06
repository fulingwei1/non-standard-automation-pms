"""add company certifications table

Revision ID: 20260705_001
Revises: 
Create Date: 2026-07-05

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260705_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建公司资质证书表
    op.create_table(
        'company_certifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cert_name', sa.String(200), nullable=False, comment='证书名称'),
        sa.Column('cert_type', sa.String(100), nullable=False, comment='证书类型'),
        sa.Column('cert_number', sa.String(100), comment='证书编号'),
        sa.Column('issuing_authority', sa.String(200), comment='发证机构'),
        sa.Column('issue_date', sa.Date(), comment='发证日期'),
        sa.Column('expiry_date', sa.Date(), comment='到期日期'),
        sa.Column('status', sa.String(50), default='有效', comment='证书状态：有效/即将到期/已过期'),
        sa.Column('description', sa.Text(), comment='证书描述'),
        sa.Column('scope', sa.Text(), comment='认证范围'),
        sa.Column('attachment_path', sa.String(500), comment='附件路径'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_company_certifications_id'), 'company_certifications', ['id'], unique=False)
    op.create_index(op.f('ix_company_certifications_cert_name'), 'company_certifications', ['cert_name'], unique=False)
    op.create_index(op.f('ix_company_certifications_cert_type'), 'company_certifications', ['cert_type'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_company_certifications_cert_type'), table_name='company_certifications')
    op.drop_index(op.f('ix_company_certifications_cert_name'), table_name='company_certifications')
    op.drop_index(op.f('ix_company_certifications_id'), table_name='company_certifications')
    op.drop_table('company_certifications')
