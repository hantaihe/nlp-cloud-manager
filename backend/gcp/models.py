import uuid
from sqlalchemy import Column, String, Text, DateTime, Numeric, JSON, UniqueConstraint, ForeignKey, Integer
from sqlalchemy.sql import func
from database import Base

class GCPCredential(Base):
    __tablename__ = "gcp_credentials"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), unique=True, index=True, nullable=False)
    project_id = Column(String(255), nullable=False)
    billing_account_id = Column(String(255), nullable=True)
    service_account_json = Column(Text, nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())


class GCPDailyCost(Base):
    __tablename__ = "gcp_daily_costs"
    __table_args__ = (UniqueConstraint("credential_id", "date", name="uq_gcp_daily_cost"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    credential_id = Column(String(36), ForeignKey("gcp_credentials.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(String(10), nullable=False)
    amount = Column(Numeric(18, 6), nullable=False, default=0.0)
    unit = Column(String(10), default="USD")
    grouped_data = Column(JSON, nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
