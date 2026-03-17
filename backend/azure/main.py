from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
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
from fastapi.middleware.cors import CORSMiddleware
import os
import json
import time
from azure.core.pipeline.policies import HttpLoggingPolicy
import logging

from database import engine, Base, get_db
from models import AzureCredential

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HTTP")

class CustomAzureLoggingPolicy(HttpLoggingPolicy):
    def on_request(self, request):
        logger.info(f"SDK Request: Azure {request.http_request.method} {request.http_request.url}")
        super().on_request(request)

    def on_response(self, request, response):
        logger.info(f"SDK Response: Azure {request.http_request.method} {request.http_request.url} - {response.http_response.status_code}")
        super().on_response(request, response)

azure_logging_policy = CustomAzureLoggingPolicy()
app = FastAPI(title="Azure Cost & Billing API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    body = await request.body()
    try:
        body_json = json.loads(body) if body else {}
    except:
        body_json = body.decode() if body else {}

    logger.info(
        f"Request: {request.method} {request.url.path}\n"
        f" Query: {dict(request.query_params)}\n"
        f" Body: {json.dumps(body_json)}"
    )

    async def receive():
        return {"type": "http.request", "body": body}
    request._receive = receive

    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000
    
    response_body = b""
    async for chunk in response.body_iterator:
        response_body += chunk
    
    try:
        resp_json = json.loads(response_body) if response_body else {}
    except:
        resp_json = response_body.decode() if response_body else {}

    logger.info(
        f"Response: {request.method} {request.url.path} - {response.status_code} ({process_time:.2f}ms)\n"
        f" Message: {json.dumps(resp_json)}"
    )

    return JSONResponse(
        content=resp_json,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

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
    
    return client_class(azure_creds, credential.subscription_id, logging_policy=azure_logging_policy), credential

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
        client = BillingBenefitsRP(azure_creds, logging_policy=azure_logging_policy)
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
        client = CostManagementClient(azure_creds, logging_policy=azure_logging_policy)
        
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
        client = AzureReservationAPI(azure_creds, logging_policy=azure_logging_policy)
        return {"status": "success", "service": "reservations"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dashboard/stats")
async def get_dashboard_stats(
    name: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    granularity: str = "Monthly",
    group_by: Optional[List[str]] = None,
    db: AsyncSession = Depends(get_db)
):
    try:
        import traceback
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
        cost_client = CostManagementClient(azure_creds)
        scope = f"/subscriptions/{credential.subscription_id}"

        from azure.mgmt.costmanagement.models import (
            QueryDefinition, QueryTimePeriod, QueryDataset,
            QueryAggregation, QueryGrouping, QueryColumnType
        )
        from datetime import timedelta
        import calendar

        azure_granularity = "Monthly"
        if granularity and granularity.upper() == "DAILY":
            azure_granularity = "Daily"

        now = datetime.now()
        
        try:
            if start:
                dt_from = datetime.strptime(start, "%Y-%m-%d")
            else:
                dt_from = now.replace(day=1)
                
            if end:
                dt_to = datetime.strptime(end, "%Y-%m-%d")
            else:
                dt_to = now
        except ValueError:
            dt_from = now.replace(day=1)
            dt_to = now

        current_month_start = dt_from.strftime("%Y-%m-%dT00:00:00Z")
        current_month_end = dt_to.strftime("%Y-%m-%dT23:59:59Z")

        last_month_end = (dt_from - timedelta(days=1))
        last_month_start = last_month_end.replace(day=1).strftime("%Y-%m-%dT00:00:00Z")
        last_month_end_str = last_month_end.strftime("%Y-%m-%dT23:59:59Z")

        seven_months_ago = dt_from.replace(day=1)
        for _ in range(6):
            seven_months_ago = (seven_months_ago - timedelta(days=1)).replace(day=1)

        total_cost = 0
        top_services = []
        cost_trend = 0
        monthly_data = []
        budget_used = 0
        alertsCount = 0
        recent_alerts = []

        azure_grouping = []
        if group_by:
            for g in group_by:
                azure_grouping.append(QueryGrouping(type="Dimension", name=g))
        else:
            azure_grouping = [QueryGrouping(type="Dimension", name="ServiceName")]

        try:
            current_query = QueryDefinition(
                type="ActualCost",
                timeframe="Custom",
                time_period=QueryTimePeriod(
                    from_property=dt_from,
                    to=dt_to
                ),
                dataset=QueryDataset(
                    granularity=None,
                    aggregation={"totalCost": QueryAggregation(name="Cost", function="Sum")},
                    grouping=azure_grouping
                )
            )
            current_result = cost_client.query.usage(scope=scope, parameters=current_query)
            if current_result.rows:
                service_costs = []
                for row in current_result.rows:
                    cost_val = float(row[0]) if row[0] else 0
                    service_name = str(row[1]) if len(row) > 1 else "Unknown"
                    total_cost += cost_val
                    service_costs.append({"name": service_name, "cost": round(cost_val)})
                service_costs.sort(key=lambda x: x["cost"], reverse=True)
                top_services = service_costs[:5]
        except Exception as e:
            print(f"Current cost query error: {e}")

        try:
            last_query = QueryDefinition(
                type="ActualCost",
                timeframe="Custom",
                time_period=QueryTimePeriod(
                    from_property=datetime.strptime(last_month_start, "%Y-%m-%dT00:00:00Z"),
                    to=datetime.strptime(last_month_end_str, "%Y-%m-%dT23:59:59Z")
                ),
                dataset=QueryDataset(
                    granularity=None,
                    aggregation={"totalCost": QueryAggregation(name="Cost", function="Sum")}
                )
            )
            last_result = cost_client.query.usage(scope=scope, parameters=last_query)
            if last_result.rows:
                last_total = float(last_result.rows[0][0]) if last_result.rows[0][0] else 0
                if last_total > 0:
                    cost_trend = round(((total_cost - last_total) / last_total) * 100, 1)
        except Exception as e:
            print(f"Last month cost query error: {e}")

        try:
            monthly_query = QueryDefinition(
                type="ActualCost",
                timeframe="Custom",
                time_period=QueryTimePeriod(
                    from_property=seven_months_ago,
                    to=dt_to
                ),
                dataset=QueryDataset(
                    granularity=azure_granularity,
                    aggregation={"totalCost": QueryAggregation(name="Cost", function="Sum")}
                )
            )
            monthly_result = cost_client.query.usage(scope=scope, parameters=monthly_query)
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            if monthly_result.rows:
                for row in monthly_result.rows:
                    cost_val = float(row[0]) if row[0] else 0
                    date_val = row[1] if len(row) > 1 else None
                    month_label = "Unknown"
                    if date_val:
                        try:
                            dt_row = datetime.strptime(str(date_val)[:10], "%Y-%m-%d") if isinstance(date_val, str) else date_val
                            if azure_granularity == "Monthly":
                                month_label = month_names[dt_row.month - 1]
                            else:
                                month_label = dt_row.strftime("%m/%d")
                        except Exception as inner_e:
                            print(f"Error parsing date in monthly_data: {inner_e}")
                            month_label = str(date_val)[:10]
                    monthly_data.append({"month": month_label, "cost": round(cost_val)})
        except Exception as e:
            print(f"Monthly cost query error: {e}")

        try:
            consumption_client = ConsumptionManagementClient(azure_creds, credential.subscription_id, logging_policy=azure_logging_policy)
            budget_list = list(consumption_client.budgets.list(scope=scope))
            if budget_list:
                budget = budget_list[0]
                budget_amount = float(budget.amount) if budget.amount else 0
                if budget_amount > 0:
                    budget_used = round((total_cost / budget_amount) * 100)
                for b in budget_list:
                    b_amount = float(b.amount) if b.amount else 0
                    if b_amount > 0 and total_cost > b_amount * 0.8:
                        alertsCount += 1
                        recent_alerts.append({
                            "message": f"Azure Budget Alert: {b.name} is at {round((total_cost/b_amount)*100)}% usage.",
                            "severity": "error" if total_cost > b_amount else "warning",
                            "date": datetime.now().strftime("%Y-%m-%d")
                        })
        except Exception as e:
            print(f"Budget query error: {e}")

        return {
            "totalCost": round(total_cost),
            "costTrend": cost_trend,
            "topServices": top_services,
            "monthlyData": monthly_data,
            "activeResources": len(top_services),
            "budgetUsed": budget_used,
            "alerts": alertsCount,
            "recentAlerts": recent_alerts,
            "recommendations": [],
            "resourcesSummary": [],
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"CRITICAL ERROR in get_dashboard_stats: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
