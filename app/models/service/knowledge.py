# -*- coding: utf-8 -*-
"""
服务模型 - 知识库
"""
from sqlalchemy import Boolean, Column, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from ..base import Base, TimestampMixin


class KnowledgeBase(Base, TimestampMixin):
    """知识库文章表"""
    __tablename__ = 'knowledge_base'

    id = Column(Integer, primary_key=True, autoincrement=True)
    article_no = Column(String(50), unique=True, nullable=False, comment='文章编号')

    # 基本信息
    title = Column(String(200), nullable=False, comment='文章标题')
    category = Column(String(50), nullable=False, comment='分类')
    content = Column(Text, nullable=True, comment='文章内容')

    # 文件信息
    file_path = Column(String(500), nullable=True, comment='文件路径')
    file_name = Column(String(200), nullable=True, comment='原始文件名')
    file_size = Column(Integer, nullable=True, comment='文件大小（字节）')
    file_type = Column(String(100), nullable=True, comment='文件MIME类型')

    # 标签和标记
    tags = Column(JSON, comment='标签列表')
    is_faq = Column(Boolean, default=False, comment='是否FAQ')
    is_featured = Column(Boolean, default=False, comment='是否精选')

    # 状态
    status = Column(String(20), default='DRAFT', comment='状态：草稿/已发布/已归档')

    # 统计信息
    view_count = Column(Integer, default=0, comment='浏览量')
    like_count = Column(Integer, default=0, comment='点赞数')
    helpful_count = Column(Integer, default=0, comment='有用数')
    download_count = Column(Integer, default=0, comment='下载次数')
    adopt_count = Column(Integer, default=0, comment='采用次数')

    # 权限设置
    allow_download = Column(Boolean, default=True, comment='是否允许他人下载')

    # 作者
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='作者ID')
    author_name = Column(String(50), comment='作者姓名')

    # 关系
    author = relationship('User', foreign_keys=[author_id])

    __table_args__ = (
        Index('idx_kb_category', 'category'),
        Index('idx_kb_status', 'status'),
        Index('idx_kb_faq', 'is_faq'),
        {'comment': '知识库文章表'},
    )

    def __repr__(self):
        return f'<KnowledgeBase {self.article_no}>'
