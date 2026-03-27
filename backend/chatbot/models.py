from sqlalchemy import Column, Integer, String, Text
from database import Base

class GCPCredential(Base):
    __tablename__ = "gcp_credentials"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True)
    project_id = Column(String(255))
    service_account_json = Column(Text)

class AzureCredential(Base):
    __tablename__ = "azure_credentials"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True)
    tenant_id = Column(String(255))
    client_id = Column(String(255))
    client_secret = Column(String(255))
    subscription_id = Column(String(255))

class AWSCredential(Base):
    __tablename__ = "aws_credentials"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True)
    accessKeyId = Column(String(255))
    secretAccessKey = Column(String(255))
    region = Column(String(255))
