# -*- coding: utf-8 -*-
"""公司资料知识库（company_profile）。

供售前 AI 工具（presale_tool_registry / audit_pack_generator）以原生 SQL 读取，
按 category/key 存放公司简介、资质、案例等文案条目。
注意：presale 服务当前以原生 SQL 访问本表，修改列名需同步
app/services/presale/presale_tool_registry.py 与 audit_pack_generator.py。
"""

from sqlalchemy import Column, DateTime, Integer, String, Text, func

from app.models.base import Base


class CompanyProfile(Base):
    __tablename__ = "company_profile"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(50), nullable=False, comment="类别，如 简介/资质/案例")
    key = Column(String(100), nullable=False, comment="条目键")
    content = Column(Text, nullable=False, comment="条目内容")
    sort_order = Column(Integer, default=0)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
