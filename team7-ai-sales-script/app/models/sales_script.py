from sqlalchemy import Column, Integer, String, Text, Enum, JSON, TIMESTAMP, ForeignKey, DECIMAL
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()


class ScenarioType(str, enum.Enum):
    FIRST_CONTACT = "first_contact"
    NEEDS_DISCOVERY = "needs_discovery"
    SOLUTION_PRESENTATION = "solution_presentation"
    PRICE_NEGOTIATION = "price_negotiation"
    OBJECTION_HANDLING = "objection_handling"
    CLOSING = "closing"


class PresaleAISalesScript(Base):
    __tablename__ = "presale_ai_sales_script"

    id = Column(Integer, primary_key=True, autoincrement=True)
    presale_ticket_id = Column(Integer, nullable=False, index=True)
    scenario = Column(Enum(ScenarioType), nullable=False)
    customer_profile_id = Column(Integer, nullable=True)
    recommended_scripts = Column(JSON, nullable=True)  # 推荐的话术列表
    objection_type = Column(String(100), nullable=True)
    response_strategy = Column(Text, nullable=True)
    success_case_references = Column(JSON, nullable=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "presale_ticket_id": self.presale_ticket_id,
            "scenario": self.scenario.value if self.scenario else None,
            "customer_profile_id": self.customer_profile_id,
            "recommended_scripts": self.recommended_scripts,
            "objection_type": self.objection_type,
            "response_strategy": self.response_strategy,
            "success_case_references": self.success_case_references,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SalesScriptTemplate(Base):
    __tablename__ = "sales_script_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scenario = Column(Enum(ScenarioType), nullable=False, index=True)
    customer_type = Column(String(50), nullable=True, index=True)
    script_content = Column(Text, nullable=False)
    tags = Column(JSON, nullable=True)
    success_rate = Column(DECIMAL(5, 2), nullable=True)  # 成功率
    created_at = Column(TIMESTAMP, server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "scenario": self.scenario.value if self.scenario else None,
            "customer_type": self.customer_type,
            "script_content": self.script_content,
            "tags": self.tags,
            "success_rate": float(self.success_rate) if self.success_rate else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
