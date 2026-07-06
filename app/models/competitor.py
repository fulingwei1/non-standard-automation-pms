# -*- coding: utf-8 -*-
"""竞争对手库（competitors）。

供售前 AI（sales_coach / competitive_analyzer）以原生 SQL 读取，
存放竞对优劣势、报价水平、应对策略等。
注意：presale 服务当前以原生 SQL 访问本表，修改列名需同步
app/services/presale/sales_coach.py 与 competitive_analyzer.py。
"""

from sqlalchemy import Column, DateTime, Integer, String, Text, func

from app.models.base import Base


class Competitor(Base):
    __tablename__ = "competitors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, comment="竞争对手名称")
    short_name = Column(String(50), comment="简称")
    competitor_type = Column(String(50), comment="类型")
    strengths = Column(Text, comment="优势")
    weaknesses = Column(Text, comment="劣势")
    good_at = Column(Text, comment="擅长领域")
    typical_projects = Column(Text, comment="典型项目")
    price_level = Column(String(20), comment="报价水平")
    delivery_time = Column(String(50), comment="交期水平")
    service_area = Column(String(100), comment="服务区域")
    counter_strategy = Column(Text, comment="应对策略")
    encounter_count = Column(Integer, default=0, comment="遭遇次数")
    win_count = Column(Integer, default=0, comment="赢单次数")
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
