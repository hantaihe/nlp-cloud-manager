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
from azure.mgmt.advisor import AdvisorManagementClient
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
from models import AzureCredential, AzureDailyCost

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

    try:
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
            headers={k: v for k, v in response.headers.items() if k.lower() != "content-length"},
        )
    except Exception as e:
        process_time = (time.time() - start_time) * 1000
        logger.error(f"Middleware error: {request.method} {request.url.path} ({process_time:.2f}ms) - {e}")
        return JSONResponse(content={"detail": "Internal Server Error"}, status_code=500)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    id: str
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

@app.get("/advisor")
async def get_advisor_recommendations(name: Optional[str] = None, db: AsyncSession = Depends(get_db)):
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
        client = AdvisorManagementClient(azure_creds, credential.subscription_id, logging_policy=azure_logging_policy)
        
        recs = []
        for rec in client.recommendations.list():
            recs.append({
                "id": rec.id,
                "name": rec.name,
                "category": rec.category,
                "impact": rec.impact,
                "risk": rec.risk,
                "short_description": {
                    "problem": rec.short_description.problem if rec.short_description else None,
                    "solution": rec.short_description.solution if rec.short_description else None,
                },
                "resource_metadata": rec.extended_properties if hasattr(rec, 'extended_properties') else None
            })
        return {"status": "success", "recommendations": recs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/forecast")
async def get_forecast(
    name: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    try:
        import calendar
        import traceback
        from datetime import timedelta
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

        now = datetime.now()
        if start:
            dt_from = datetime.strptime(start, "%Y-%m-%d")
        else:
            dt_from = now.replace(day=1)
        if end:
            dt_to = datetime.strptime(end, "%Y-%m-%d")
        else:
            last_day = calendar.monthrange(now.year, now.month)[1]
            dt_to = now.replace(day=last_day)

        forecast_result = _forecast_query(
            cost_client, scope,
            {
                "type": "Usage",
                "timeframe": "Custom",
                "timePeriod": {
                    "from": dt_from.strftime("%Y-%m-%dT00:00:00Z"),
                    "to": dt_to.strftime("%Y-%m-%dT23:59:59Z"),
                },
                "dataset": {
                    "granularity": "Daily",
                    "aggregation": {"totalCost": {"function": "Sum", "name": "Cost"}},
                },
                "includeActualCost": True,
                "includeFreshPartialCost": True,
            },
        )

        cols = [c.name for c in forecast_result.columns] if forecast_result.columns else []
        cost_idx = next((i for i, c in enumerate(cols) if c in ("Cost", "PreTaxCost")), 0)
        date_idx = next((i for i, c in enumerate(cols) if c in ("UsageDate", "BillingMonth", "Date")), 1)
        type_idx = next((i for i, c in enumerate(cols) if c in ("CostStatus", "ChargeType")), 2)

        daily_forecast = []
        total_forecasted = 0
        total_actual = 0
        if forecast_result.rows:
            for row in forecast_result.rows:
                cost_val = float(row[cost_idx]) if row[cost_idx] else 0
                date_val = row[date_idx] if len(row) > date_idx else None
                cost_type = str(row[type_idx]) if len(row) > type_idx else "Forecast"
                label = "Unknown"
                if date_val is not None:
                    try:
                        if isinstance(date_val, int):
                            dt_row = datetime.strptime(str(date_val), "%Y%m%d")
                        elif isinstance(date_val, str):
                            dt_row = datetime.strptime(date_val[:10], "%Y-%m-%d")
                        else:
                            dt_row = date_val
                        label = dt_row.strftime("%m/%d")
                    except Exception:
                        pass
                daily_forecast.append({
                    "day": label,
                    "cost": round(cost_val, 2),
                    "type": cost_type,
                })
                if "Forecast" in str(cost_type):
                    total_forecasted += cost_val
                else:
                    total_actual += cost_val

        return {
            "forecastedCost": round(total_forecasted + total_actual, 2),
            "actualCost": round(total_actual, 2),
            "dailyForecast": [{"day": d["day"], "cost": round(d["cost"], 2), "type": d["type"]} for d in daily_forecast],
            "period": {
                "start": dt_from.strftime("%Y-%m-%d"),
                "end": dt_to.strftime("%Y-%m-%d"),
            },
            "currency": "USD",
            "timestamp": datetime.now().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


def _parse_date_val(date_val) -> Optional[datetime]:
    """Azure API returns dates as int (YYYYMMDD), ISO string, or datetime."""
    if date_val is None:
        return None
    try:
        if isinstance(date_val, int):
            return datetime.strptime(str(date_val), "%Y%m%d")
        if isinstance(date_val, str):
            return datetime.strptime(date_val[:10], "%Y-%m-%d")
        if hasattr(date_val, "year"):
            return date_val
    except Exception:
        pass
    return None


def _col_idx(columns, *names) -> int:
    """Return index of first matching column name, default 0."""
    col_names = [c.name for c in columns] if columns else []
    logger.info(f"Available columns: {col_names}, looking for: {list(names)}")
    for n in names:
        if n in col_names:
            return col_names.index(n)
    logger.warning(f"Column(s) {list(names)} not found in {col_names}, defaulting to index 0")
    return 0


def _cost_query(cost_client, scope: str, parameters: dict, max_retries: int = 3):
    """Cost Management query with automatic retry on 429 (rate limit)."""
    import time
    from azure.core.exceptions import HttpResponseError

    for attempt in range(max_retries):
        try:
            return cost_client.query.usage(scope=scope, parameters=parameters)
        except HttpResponseError as e:
            if e.status_code == 429:
                retry_after = int(
                    e.response.headers.get(
                        "x-ms-ratelimit-microsoft.costmanagement-entity-retry-after", 10
                    )
                )
                logger.warning(f"429 rate limit — retrying in {retry_after}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(retry_after)
            else:
                raise
    return cost_client.query.usage(scope=scope, parameters=parameters)


def _forecast_query(cost_client, scope: str, parameters: dict, max_retries: int = 3):
    """Cost Management forecast with automatic retry on 429."""
    import time
    from azure.core.exceptions import HttpResponseError

    for attempt in range(max_retries):
        try:
            return cost_client.forecast.usage(scope=scope, parameters=parameters)
        except HttpResponseError as e:
            if e.status_code == 429:
                retry_after = int(
                    e.response.headers.get(
                        "x-ms-ratelimit-microsoft.costmanagement-entity-retry-after", 10
                    )
                )
                logger.warning(f"429 rate limit (forecast) — retrying in {retry_after}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(retry_after)
            else:
                raise
    return cost_client.forecast.usage(scope=scope, parameters=parameters)


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
        import calendar
        from datetime import timedelta

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
            client_secret=credential.client_secret,
        )
        cost_client = CostManagementClient(azure_creds)
        scope = f"/subscriptions/{credential.subscription_id}"

        is_daily = granularity.upper() == "DAILY"
        azure_granularity = "Daily" if is_daily else "Monthly"
        now = datetime.now()

        try:
            dt_from = datetime.strptime(start, "%Y-%m-%d") if start else now.replace(day=1)
            dt_to = datetime.strptime(end, "%Y-%m-%d") if end else now
        except ValueError:
            dt_from, dt_to = now.replace(day=1), now

        last_month_end = dt_from - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)

        if is_daily:
            history_start = dt_from - timedelta(days=30)
        else:
            history_start = dt_from.replace(day=1)
            for _ in range(6):
                history_start = (history_start - timedelta(days=1)).replace(day=1)

        total_cost = 0.0
        top_services: list = []
        cost_trend = 0.0
        monthly_data: list = []
        daily_data: list = []
        budget_used = 0
        alerts_count = 0
        recent_alerts: list = []
        cost_cache_hit = False

        grouping_dims = group_by if group_by else ["ServiceName"]
        group_by_key = ",".join(sorted(grouping_dims))
        grouping_param = [{"type": "Dimension", "name": g} for g in grouping_dims]

        if is_daily:
            trend_start_str = history_start.strftime("%Y-%m-%d")
            trend_end_str = dt_to.strftime("%Y-%m-%d")
            current_start_str = dt_from.strftime("%Y-%m-%d")

            cached_result = await db.execute(
                select(AzureDailyCost)
                .where(AzureDailyCost.credential_id == credential.id)
                .where(AzureDailyCost.date >= trend_start_str)
                .where(AzureDailyCost.date <= trend_end_str)
                .order_by(AzureDailyCost.date)
            )
            cached_rows = cached_result.scalars().all()

            expected_days = (dt_to.date() - history_start.date()).days
            has_all = len(cached_rows) >= expected_days
            has_grouping = bool(cached_rows) and all(
                r.grouped_data and group_by_key in r.grouped_data for r in cached_rows
            )

            if has_all and has_grouping:
                logger.info(f"Cache HIT: Azure daily {credential.name}")
                cost_cache_hit = True
                svc_agg: dict = {}
                for r in cached_rows:
                    dt_r = datetime.strptime(r.date, "%Y-%m-%d")
                    daily_data.append({"day": dt_r.strftime("%m/%d"), "cost": round(r.amount)})
                    if r.date >= current_start_str:
                        total_cost += r.amount
                        for svc in (r.grouped_data.get(group_by_key) or []):
                            svc_agg[svc["name"]] = svc_agg.get(svc["name"], 0) + svc.get("cost", 0)
                top_services = sorted(
                    [{"name": k, "cost": round(v)} for k, v in svc_agg.items() if v > 0],
                    key=lambda x: -x["cost"],
                )[:5]
            else:
                logger.info(f"Cache MISS: Azure daily {credential.name} — calling API")
                try:
                    combined_result = _cost_query(
                        cost_client, scope,
                        {
                            "type": "Usage",
                            "timeframe": "Custom",
                            "timePeriod": {
                                "from": history_start.strftime("%Y-%m-%dT00:00:00Z"),
                                "to": dt_to.strftime("%Y-%m-%dT23:59:59Z"),
                            },
                            "dataset": {
                                "granularity": "Daily",
                                "aggregation": {"totalCost": {"function": "Sum", "name": "PreTaxCost"}},
                                "grouping": grouping_param,
                            },
                        },
                    )

                    cost_i = _col_idx(combined_result.columns, "PreTaxCost", "Cost")
                    date_i = _col_idx(combined_result.columns, "UsageDate", "BillingMonth", "Date")
                    svc_i = _col_idx(combined_result.columns, *grouping_dims, "ServiceName")

                    day_totals: dict = {}
                    day_services: dict = {}
                    if combined_result.rows:
                        for row in combined_result.rows:
                            cost_val = float(row[cost_i]) if row[cost_i] else 0
                            dt_row = _parse_date_val(row[date_i] if len(row) > date_i else None)
                            svc_name = str(row[svc_i]) if len(row) > svc_i else "Unknown"
                            if dt_row is None:
                                continue
                            date_str = dt_row.strftime("%Y-%m-%d")
                            day_totals[date_str] = day_totals.get(date_str, 0) + cost_val
                            day_services.setdefault(date_str, {})
                            day_services[date_str][svc_name] = day_services[date_str].get(svc_name, 0) + cost_val

                    svc_agg_all: dict = {}
                    for date_str in sorted(day_totals):
                        dt_r = datetime.strptime(date_str, "%Y-%m-%d")
                        daily_data.append({"day": dt_r.strftime("%m/%d"), "cost": round(day_totals[date_str])})
                        if date_str >= current_start_str:
                            total_cost += day_totals[date_str]
                            for svc, cv in day_services.get(date_str, {}).items():
                                svc_agg_all[svc] = svc_agg_all.get(svc, 0) + cv

                    top_services = sorted(
                        [{"name": k, "cost": round(v)} for k, v in svc_agg_all.items() if v > 0],
                        key=lambda x: -x["cost"],
                    )[:5]

                    for date_str, day_amount in day_totals.items():
                        ex = await db.execute(
                            select(AzureDailyCost).where(
                                AzureDailyCost.credential_id == credential.id,
                                AzureDailyCost.date == date_str,
                            )
                        )
                        dc = ex.scalars().first()
                        if not dc:
                            dc = AzureDailyCost(credential_id=credential.id, date=date_str)
                        dc.amount = day_amount
                        dc.unit = "USD"
                        dc.grouped_data = {
                            group_by_key: [{"name": k, "cost": v} for k, v in day_services.get(date_str, {}).items()]
                        }
                        db.add(dc)
                    await db.commit()
                    cost_cache_hit = True
                except Exception as e:
                    logger.error(f"Daily cost query error: {e}")
                    traceback.print_exc()

        if not cost_cache_hit:
            month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            last_month_str = last_month_start.strftime("%Y-%m")

            try:
                current_result = _cost_query(
                    cost_client, scope,
                    {
                        "type": "Usage",
                        "timeframe": "Custom",
                        "timePeriod": {
                            "from": dt_from.strftime("%Y-%m-%dT00:00:00Z"),
                            "to": dt_to.strftime("%Y-%m-%dT23:59:59Z"),
                        },
                        "dataset": {
                            "granularity": "None",
                            "aggregation": {"totalCost": {"function": "Sum", "name": "PreTaxCost"}},
                            "grouping": grouping_param,
                        },
                    },
                )
                cost_i = _col_idx(current_result.columns, "PreTaxCost", "Cost")
                svc_i = _col_idx(current_result.columns, *grouping_dims, "ServiceName")
                if current_result.rows:
                    service_costs = []
                    for row in current_result.rows:
                        cost_val = float(row[cost_i]) if row[cost_i] else 0
                        svc_name = str(row[svc_i]) if len(row) > svc_i else "Unknown"
                        total_cost += cost_val
                        service_costs.append({"name": svc_name, "cost": round(cost_val)})
                    top_services = sorted(service_costs, key=lambda x: -x["cost"])[:5]
            except Exception as e:
                logger.error(f"Current cost query error: {e}")
                traceback.print_exc()

            try:
                monthly_result = _cost_query(
                    cost_client, scope,
                    {
                        "type": "Usage",
                        "timeframe": "Custom",
                        "timePeriod": {
                            "from": history_start.strftime("%Y-%m-%dT00:00:00Z"),
                            "to": dt_to.strftime("%Y-%m-%dT23:59:59Z"),
                        },
                        "dataset": {
                            "granularity": azure_granularity,
                            "aggregation": {"totalCost": {"function": "Sum", "name": "PreTaxCost"}},
                        },
                    },
                )
                cost_i = _col_idx(monthly_result.columns, "PreTaxCost", "Cost")
                date_i = _col_idx(monthly_result.columns, "BillingMonth", "UsageDate", "Date")
                last_total = 0.0
                if monthly_result.rows:
                    for row in monthly_result.rows:
                        cost_val = float(row[cost_i]) if row[cost_i] else 0
                        dt_row = _parse_date_val(row[date_i] if len(row) > date_i else None)
                        if dt_row:
                            monthly_data.append({
                                "month": month_names[dt_row.month - 1],
                                "cost": round(cost_val),
                            })
                            if dt_row.strftime("%Y-%m") == last_month_str:
                                last_total = cost_val
                if last_total > 0 and total_cost > 0:
                    cost_trend = round(((total_cost - last_total) / last_total) * 100, 1)
            except Exception as e:
                logger.error(f"Monthly trend query error: {e}")
                traceback.print_exc()

        try:
            consumption_client = ConsumptionManagementClient(
                azure_creds, credential.subscription_id, logging_policy=azure_logging_policy
            )
            budget_list = list(consumption_client.budgets.list(scope=scope))
            if budget_list:
                budget_amount = float(budget_list[0].amount) if budget_list[0].amount else 0
                if budget_amount > 0:
                    budget_used = round((total_cost / budget_amount) * 100)
                for b in budget_list:
                    b_amount = float(b.amount) if b.amount else 0
                    if b_amount > 0 and total_cost > b_amount * 0.8:
                        alerts_count += 1
                        recent_alerts.append({
                            "message": f"Azure Budget Alert: {b.name} is at {round((total_cost / b_amount) * 100)}% usage.",
                            "severity": "error" if total_cost > b_amount else "warning",
                            "date": now.strftime("%Y-%m-%d"),
                        })
        except Exception as e:
            logger.error(f"Budget query error: {e}")

        try:
            alert_result = cost_client.alerts.list(scope=scope)
            for alert in (alert_result.value or []):
                alerts_count += 1
                recent_alerts.append({
                    "message": alert.properties.description if alert.properties else str(alert.name),
                    "severity": str(alert.properties.severity).lower() if alert.properties else "info",
                    "date": now.strftime("%Y-%m-%d"),
                })
        except Exception as e:
            logger.error(f"Alerts query error: {e}")

        forecasted_cost = 0.0
        try:
            last_day = calendar.monthrange(now.year, now.month)[1]
            forecast_end = now.replace(day=last_day)
            forecast_result = _forecast_query(
                cost_client, scope,
                {
                    "type": "Usage",
                    "timeframe": "Custom",
                    "timePeriod": {
                        "from": dt_from.strftime("%Y-%m-%dT00:00:00Z"),
                        "to": forecast_end.strftime("%Y-%m-%dT23:59:59Z"),
                    },
                    "dataset": {
                        "granularity": "Monthly",
                        "aggregation": {"totalCost": {"function": "Sum", "name": "Cost"}},
                    },
                    "includeActualCost": True,
                    "includeFreshPartialCost": True,
                },
            )
            cost_i = _col_idx(forecast_result.columns, "Cost", "PreTaxCost")
            if forecast_result.rows:
                for row in forecast_result.rows:
                    forecasted_cost += float(row[cost_i]) if row[cost_i] else 0
        except Exception as e:
            logger.error(f"Forecast query error: {e}")

        recommendations: list = []
        try:
            advisor_client = AdvisorManagementClient(azure_creds, credential.subscription_id)
            for rec in advisor_client.recommendations.list():
                if rec.category == "Cost":
                    recommendations.append({
                        "service": "Azure Advisor",
                        "title": rec.short_description.problem if rec.short_description else rec.name,
                        "impact": (
                            f"${rec.extended_properties.get('savingsAmount', '0')}/month"
                            if rec.extended_properties
                            else "High"
                        ),
                        "description": rec.short_description.solution if rec.short_description else "",
                    })
        except Exception as e:
            logger.error(f"Advisor query error: {e}")

        return {
            "totalCost": round(total_cost, 2),
            "costTrend": cost_trend,
            "forecastedCost": round(forecasted_cost, 2),
            "topServices": [{"name": s["name"], "cost": round(s["cost"], 2)} for s in top_services],
            "monthlyData": [{"month": m["month"], "cost": round(m["cost"], 2)} for m in monthly_data],
            "dailyData": [{"day": d["day"], "cost": round(d["cost"], 2)} for d in daily_data],
            "activeResources": len(top_services),
            "budgetUsed": budget_used,
            "alerts": alerts_count,
            "recentAlerts": recent_alerts,
            "recommendations": recommendations,
            "resourcesSummary": [],
            "currency": "USD",
            "timestamp": datetime.now().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/debug/cost")
async def debug_cost(name: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """임시 디버그 엔드포인트 — 실제 API 에러를 그대로 반환"""
    import traceback
    from datetime import timedelta
    errors = {}

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
        client_secret=credential.client_secret,
    )
    cost_client = CostManagementClient(azure_creds)
    scope = f"/subscriptions/{credential.subscription_id}"

    from datetime import datetime as dt
    now = dt.now()
    dt_from = now.replace(day=1)

    raw_query_result = None
    raw_grouped_result = None
    try:
        raw = cost_client.query.usage(
            scope=scope,
            parameters={
                "type": "Usage",
                "timeframe": "MonthToDate",
                "dataset": {
                    "granularity": "None",
                    "aggregation": {"totalCost": {"function": "Sum", "name": "PreTaxCost"}},
                },
            },
        )
        raw_query_result = {
            "columns": [{"name": c.name, "type": str(c.type)} for c in (raw.columns or [])],
            "rows": raw.rows,
            "total": sum(float(r[0]) for r in (raw.rows or []) if r),
        }
    except Exception as e:
        errors["query_MonthToDate"] = traceback.format_exc()

    try:
        raw_grouped = cost_client.query.usage(
            scope=scope,
            parameters={
                "type": "Usage",
                "timeframe": "MonthToDate",
                "dataset": {
                    "granularity": "None",
                    "aggregation": {"totalCost": {"function": "Sum", "name": "PreTaxCost"}},
                    "grouping": [{"type": "Dimension", "name": "ServiceName"}],
                },
            },
        )
        raw_grouped_result = {
            "columns": [{"name": c.name, "type": str(c.type)} for c in (raw_grouped.columns or [])],
            "rows": raw_grouped.rows,
        }
    except Exception as e:
        errors["query_grouped"] = traceback.format_exc()

    return {
        "scope": scope,
        "credential_name": credential.name,
        "raw_query_result": raw_query_result,
        "errors": errors,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)