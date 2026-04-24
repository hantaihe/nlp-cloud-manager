import uuid
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.sql import func
from database import Base


class AWSCredential(Base):
    __tablename__ = "aws_credentials"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), unique=True, index=True, nullable=False)
    access_key_id = Column(String(255), nullable=False)
    secret_access_key = Column(String(255), nullable=False)
    session_token = Column(String(255), nullable=True)
    region = Column(String(255), nullable=False, default="ap-northeast-2")
    account_id = Column(String(255), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())


class AzureCredential(Base):
    __tablename__ = "azure_credentials"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), unique=True, index=True, nullable=False)
    tenant_id = Column(String(255), nullable=False)
    client_id = Column(String(255), nullable=False)
    client_secret = Column(String(255), nullable=False)
    subscription_id = Column(String(255), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())


class GCPCredential(Base):
    __tablename__ = "gcp_credentials"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), unique=True, index=True, nullable=False)
    project_id = Column(String(255), nullable=False)
    billing_account_id = Column(String(255), nullable=True)
    service_account_json = Column(Text, nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
