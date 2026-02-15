from sqlalchemy import Column, Integer, String, Text, Enum, JSON, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()


class CustomerType(str, enum.Enum):
    TECHNICAL = "technical"
    COMMERCIAL = "commercial"
    DECISION_MAKER = "decision_maker"
    MIXED = "mixed"


class DecisionStyle(str, enum.Enum):
    RATIONAL = "rational"
    EMOTIONAL = "emotional"
    AUTHORITATIVE = "authoritative"


class PresaleCustomerProfile(Base):
    __tablename__ = "presale_customer_profile"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, nullable=False, index=True)
    presale_ticket_id = Column(Integer, nullable=True, index=True)
    customer_type = Column(Enum(CustomerType), nullable=False)
    focus_points = Column(JSON, nullable=True)  # ['price', 'quality', 'delivery', 'service']
    decision_style = Column(Enum(DecisionStyle), nullable=False)
    communication_notes = Column(Text, nullable=True)
    ai_analysis = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "presale_ticket_id": self.presale_ticket_id,
            "customer_type": self.customer_type.value if self.customer_type else None,
            "focus_points": self.focus_points,
            "decision_style": self.decision_style.value if self.decision_style else None,
            "communication_notes": self.communication_notes,
            "ai_analysis": self.ai_analysis,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
