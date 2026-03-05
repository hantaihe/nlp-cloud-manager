from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from azure.identity import ClientSecretCredential
from azure.mgmt.billing import BillingManagementClient
from azure.mgmt.billingbenefits import BillingBenefitsRP
from azure.mgmt.commerce import UsageManagementClient
from azure.mgmt.consumption import ConsumptionManagementClient
from azure.mgmt.costmanagement import CostManagementClient
from azure.mgmt.reservations import AzureReservationAPI
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os

from database import engine, Base, get_db
from models import AzureCredential

app = FastAPI(title="Azure Cost & Billing API")

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

class CredentialCreate(BaseModel):
    name: str
    tenant_id: str
    client_id: str
    client_secret: str
    subscription_id: str

class CredentialResponse(BaseModel):
    id: int
    name: str
    tenant_id: str
    client_id: str
    subscription_id: str
    updated_at: datetime

    class Config:
        from_attributes = True

async def get_azure_client(client_class, db: AsyncSession, name: Optional[str] = None):
    query = select(AzureCredential)
    if name:
        query = query.where(AzureCredential.name == name)
    
    result = await db.execute(query)
    credential = result.scalars().first()
    
    if not credential:
        raise HTTPException(status_code=404, detail="Credentials not found")
        
    azure_creds = ClientSecretCredential(
        tenant_id=credential.tenant_id,
        client_id=credential.client_id,
        client_secret=credential.client_secret
    )
    
    return client_class(azure_creds, credential.subscription_id), credential

@app.get("/")
async def root():
    return {"message": "Azure Cost & Billing API is running"}

@app.post("/credentials", response_model=CredentialResponse)
async def create_credential(cred: CredentialCreate, db: AsyncSession = Depends(get_db)):
    db_cred = AzureCredential(**cred.dict())
    db.add(db_cred)
    await db.commit()
    await db.refresh(db_cred)
    return db_cred

@app.get("/credentials", response_model=List[CredentialResponse])
async def list_credentials(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AzureCredential))
    return result.scalars().all()

@app.delete("/credentials/{name}")
async def delete_credential(name: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AzureCredential).where(AzureCredential.name == name))
    db_cred = result.scalars().first()
    if not db_cred:
        raise HTTPException(status_code=404, detail="Credential not found")
    await db.delete(db_cred)
    await db.commit()
    return {"message": "Credential deleted"}

@app.get("/billing")
async def get_billing_info(name: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    try:
        client, _ = await get_azure_client(BillingManagementClient, db, name)
        return {"status": "success", "service": "billing"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/billingbenefits")
async def get_billing_benefits(name: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    try:
        query = select(AzureCredential)
        if name:
            query = query.where(AzureCredential.name == name)
        result = await db.execute(query)
        credential = result.scalars().first()
        if not credential:
            raise HTTPException(status_code=404, detail="Credential not found")
            
        azure_creds = ClientSecretCredential(
            tenant_id=credential.tenant_id,
            client_id=credential.client_id,
            client_secret=credential.client_secret
        )
        client = BillingBenefitsRP(azure_creds)
        return {"status": "success", "service": "billingbenefits"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/commerce")
async def get_commerce_info(name: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    try:
        client, _ = await get_azure_client(UsageManagementClient, db, name)
        return {"status": "success", "service": "commerce"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/consumption")
async def get_consumption_info(
    name: Optional[str] = None, 
    start: Optional[str] = None,
    end: Optional[str] = None,
    granularity: Optional[str] = "Monthly",
    db: AsyncSession = Depends(get_db)
):
    try:
        client, credential = await get_azure_client(ConsumptionManagementClient, db, name)
        return {
            "status": "success", 
            "service": "consumption",
            "filters": {"start": start, "end": end, "granularity": granularity}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/costmanagement")
async def get_cost_management(
    name: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    granularity: str = "Monthly",
    group_by: Optional[List[str]] = None,
    db: AsyncSession = Depends(get_db)
):
    try:
        query = select(AzureCredential)
        if name:
            query = query.where(AzureCredential.name == name)
        result = await db.execute(query)
        credential = result.scalars().first()
        if not credential:
            raise HTTPException(status_code=404, detail="Credentials not found")
            
        azure_creds = ClientSecretCredential(
            tenant_id=credential.tenant_id,
            client_id=credential.client_id,
            client_secret=credential.client_secret
        )
        client = CostManagementClient(azure_creds)
        
        return {
            "status": "success", 
            "service": "costmanagement",
            "subscription_id": credential.subscription_id,
            "query_info": {
                "granularity": granularity,
                "timeframe": "Custom" if start and end else "MonthToDate",
                "group_by": group_by
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reservations")
async def get_reservations(name: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    try:
        query = select(AzureCredential)
        if name:
            query = query.where(AzureCredential.name == name)
        result = await db.execute(query)
        credential = result.scalars().first()
        if not credential:
            raise HTTPException(status_code=404, detail="Credential not found")
            
        azure_creds = ClientSecretCredential(
            tenant_id=credential.tenant_id,
            client_id=credential.client_id,
            client_secret=credential.client_secret
        )
        client = AzureReservationAPI(azure_creds)
        return {"status": "success", "service": "reservations"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
