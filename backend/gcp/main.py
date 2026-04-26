from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import json
import time
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from google.api_core.exceptions import PermissionDenied, Forbidden
from google.oauth2 import service_account
import google.auth.transport.requests
from google.cloud import billing_v1
from google.cloud.billing import budgets_v1
from google.cloud import bigquery
from google.cloud.bigquery_reservation_v1 import ReservationServiceClient
from google.cloud import bigquery_datatransfer_v1

from google.cloud import monitoring_v3
from google.cloud import logging_v2 as gcp_logging_v2
from google.cloud import asset_v1
from google.cloud import cloudquotas_v1
from google.cloud import orgpolicy_v2
from google.cloud import service_usage_v1
from google.cloud import recommender_v1
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from database import engine, Base, get_db
from models import GCPCredential, GCPDailyCost

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HTTP")

def log_gcp_call(service_name, method_name, func, *args, **kwargs):
    now = time.time()
    logger.info(f"SDK Request: GCP {service_name}.{method_name}")
    try:
        result = func(*args, **kwargs)
        duration = (time.time() - now) * 1000
        logger.info(f"SDK Response: GCP {service_name}.{method_name} - Success ({duration:.2f}ms)")
        return result
    except Exception as e:
        duration = (time.time() - now) * 1000
        logger.error(f"SDK Response: GCP {service_name}.{method_name} - Error ({duration:.2f}ms): {str(e)}")
        raise e

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="GCP Cost & Billing API", lifespan=lifespan)

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
        f"Request {request.method} {request.url.path}\n"
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
        f"Response {request.method} {request.url.path} - {response.status_code} ({process_time:.2f}ms)\n"
        f" Message: {json.dumps(resp_json)}"
    )

    return JSONResponse(
        content=resp_json,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

class CredentialCreate(BaseModel):
    name: str
    project_id: str
    billing_account_id: Optional[str] = None
    service_account_json: str

class CredentialResponse(BaseModel):
    id: str
    name: str
    project_id: str
    billing_account_id: Optional[str] = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

from models import GCPCredential

async def _get_credential(db: AsyncSession, name: Optional[str] = None) -> GCPCredential:
    query = select(GCPCredential)
    if name:
        query = query.where(GCPCredential.name == name)

    result = await db.execute(query)
    credential = result.scalars().first()

    if not credential:
        raise HTTPException(
            status_code=401, 
            detail="Credentials not found."
        )
    return credential


def _get_credentials_obj(credential: GCPCredential, scopes: Optional[List[str]] = None):
    try:
        if not credential.service_account_json:
            raise ValueError("Service account empty")
        
        info = json.loads(credential.service_account_json)
        creds = service_account.Credentials.from_service_account_info(info)
        
        if scopes:
            creds = creds.with_scopes(scopes)
        return creds
    except json.JSONDecodeError:
        raise HTTPException(status_code=401, detail="Invalid format")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")


def _get_monitoring_total_cost(creds, project_id: str):
    try:
        from google.cloud import monitoring_v3
        from datetime import datetime, timedelta
        import time

        client = monitoring_v3.MetricServiceClient(credentials=creds)
        now = time.time()

        start_time = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        interval = monitoring_v3.TimeInterval(
            end_time={"seconds": int(now)},
            start_time={"seconds": int(start_time.timestamp())},
        )
        
        filter_str = 'metric.type = "billing.googleapis.com/billing/total_cost"'
        
        results = client.list_time_series(
            request={
                "name": f"projects/{project_id}",
                "filter": filter_str,
                "interval": interval,
                "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
            }
        )
        
        total_cost = 0.0
        currency = "USD"
        
        for result in results:
            if result.points:
                latest_point = result.points[0]
                total_cost += latest_point.value.double_value
        
        return total_cost, currency
    except Exception as e:
        logger.warning(f"Monitoring fallback failed: {e}")
        return 0.0, "USD"


def _resolve_billing_info(client: bigquery.Client, project_id: str, dataset: str, table: str, billing_account_id: Optional[str] = None):
    try:
        client.get_table(f"{project_id}.{dataset}.{table}")
        return dataset, table
    except Exception:
        pass

    if billing_account_id:
        suffix = billing_account_id.replace("-", "_")
        alt_table = f"gcp_billing_export_v1_{suffix}"
        try:
            client.get_table(f"{project_id}.{dataset}.{alt_table}")
            return dataset, alt_table
        except Exception:
            pass

    try:
        datasets = client.list_datasets(project=project_id)
        for ds in datasets:
            ds_id = ds.dataset_id
            try:
                tables = client.list_tables(f"{project_id}.{ds_id}")
                for t in tables:
                    if t.table_id.startswith("gcp_billing_export_v1"):
                        logger.info(f"Discovered billing table: {ds_id}.{t.table_id}")
                        return ds_id, t.table_id
            except Exception:
                continue
    except Exception:
        pass

    return dataset, table

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"message": "GCP Cost & Billing API is running"}


@app.post("/credentials", response_model=CredentialResponse)
async def create_credential(cred: CredentialCreate, db: AsyncSession = Depends(get_db)):
    db_cred = GCPCredential(**cred.dict())
    db.add(db_cred)
    await db.commit()
    await db.refresh(db_cred)
    return db_cred


@app.get("/credentials", response_model=List[CredentialResponse])
async def list_credentials(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(GCPCredential))
    return result.scalars().all()


@app.patch("/credentials/{name}", response_model=CredentialResponse)
async def update_credential(name: str, data: dict, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(GCPCredential).where(GCPCredential.name == name))
    db_cred = result.scalars().first()
    if not db_cred:
        raise HTTPException(status_code=404, detail="Credential not found")
    allowed = {"billing_account_id", "project_id", "service_account_json"}
    for key, value in data.items():
        if key in allowed:
            setattr(db_cred, key, value)
    await db.commit()
    await db.refresh(db_cred)
    return db_cred


@app.delete("/credentials/{name}")
async def delete_credential(name: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(GCPCredential).where(GCPCredential.name == name))
    db_cred = result.scalars().first()
    if not db_cred:
        raise HTTPException(status_code=404, detail="Credential not found")
    await db.delete(db_cred)
    await db.commit()
    return {"message": "Credential deleted"}


@app.get("/billing/accounts")
async def list_billing_accounts(name: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    try:
        credential = await _get_credential(db, name)
        creds = _get_credentials_obj(credential)
        client = billing_v1.CloudBillingClient(credentials=creds)

        accounts = []
        try:
            for account in log_gcp_call("CloudBilling", "list_billing_accounts", client.list_billing_accounts):
                accounts.append({
                    "name": account.name,
                    "display_name": account.display_name,
                    "open": account.open_,
                    "master_billing_account": account.master_billing_account,
                })
        except (PermissionDenied, Forbidden):
            logger.warning("list_billing_accounts 권한 없음")
            return {
                "status": "permission_denied",
                "billing_accounts": [],
                "warning": "계정에 billing.accounts.list 권한이 없습니다. 저장된 Billing Account ID를 사용합니다.",
                "saved_billing_account_id": credential.billing_account_id,
            }

        return {"status": "success", "billing_accounts": accounts}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/billing/accounts/{billing_account_id}/projects")
async def list_billing_projects(
    billing_account_id: str,
    name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    try:
        credential = await _get_credential(db, name)
        creds = _get_credentials_obj(credential)
        client = billing_v1.CloudBillingClient(credentials=creds)

        projects = []
        request = billing_v1.ListProjectBillingInfoRequest(
            name=f"billingAccounts/{billing_account_id}"
        )
        for proj in log_gcp_call("CloudBilling", "list_project_billing_info", client.list_project_billing_info, request=request):
            projects.append({
                "project_id": proj.project_id,
                "billing_account_name": proj.billing_account_name,
                "billing_enabled": proj.billing_enabled,
            })
        return {"status": "success", "projects": projects}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/billing/summary")
async def get_billing_summary(
    billing_account_id: Optional[str] = None,
    name: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    try:
        credential = await _get_credential(db, name)
        creds = _get_credentials_obj(credential)

        now = datetime.now()
        try:
            dt_start = datetime.strptime(start, "%Y-%m-%d") if start else now.replace(day=1)
            dt_end = datetime.strptime(end, "%Y-%m-%d") if end else now
        except ValueError:
            dt_start = now.replace(day=1)
            dt_end = now
        period_start = dt_start.strftime("%Y-%m-%d")
        period_end = dt_end.strftime("%Y-%m-%d")

        billing_client = billing_v1.CloudBillingClient(credentials=creds)
        accounts = list(log_gcp_call("CloudBilling", "list_billing_accounts", billing_client.list_billing_accounts))
        
        total_budget = 0
        currency_code = "USD"
        
        if billing_account_id:
            budget_client = budgets_v1.BudgetServiceClient(credentials=creds)
            request = budgets_v1.ListBudgetsRequest(parent=f"billingAccounts/{billing_account_id}")
            for budget in log_gcp_call("BudgetService", "list_budgets", budget_client.list_budgets, request=request):
                if budget.amount.specified_amount:
                    amount = budget.amount.specified_amount.units + (budget.amount.specified_amount.nanos / 1e9)
                    total_budget += amount
                    currency_code = budget.amount.specified_amount.currency_code
        elif accounts:
             active_acc = next((a for a in accounts if a.open_), None)
             if active_acc:
                 billing_account_id = active_acc.name.split("/")[-1]
                 budget_client = budgets_v1.BudgetServiceClient(credentials=creds)
                 request = budgets_v1.ListBudgetsRequest(parent=active_acc.name)
                 for budget in log_gcp_call("BudgetService", "list_budgets", budget_client.list_budgets, request=request):
                     if budget.amount.specified_amount:
                         amount = budget.amount.specified_amount.units + (budget.amount.specified_amount.nanos / 1e9)
                         total_budget += amount
                         currency_code = budget.amount.specified_amount.currency_code
        
        total_cost = 0.0
        bq_error = None
        try:
            bq_client = bigquery.Client(credentials=creds, project=credential.project_id)
            dataset_name = "all_billing_data"
            base_table = "gcp_billing_export_v1"
            dataset_name, resolved_table = _resolve_billing_info(bq_client, credential.project_id, dataset_name, base_table, billing_account_id)
            
            query = f"""
                SELECT
                    IFNULL(SUM(cost), 0) + IFNULL(SUM((SELECT SUM(c.amount) FROM UNNEST(credits) AS c)), 0) AS total_cost,
                    ANY_VALUE(currency) as currency
                FROM `{credential.project_id}.{dataset_name}.{resolved_table}`
                WHERE usage_start_time >= TIMESTAMP('{period_start}')
                  AND usage_start_time <= TIMESTAMP('{period_end} 23:59:59')
            """
            query_job = bq_client.query(query)
            for row in query_job:
                total_cost = float(row["total_cost"])
                if row["currency"]:
                    currency_code = row["currency"]
        except Exception as e:
            bq_error = str(e)
            logger.warning(f"BigQuery not available: {e}")
            try:
                scoped_creds = creds.with_scopes([
                    "https://www.googleapis.com/auth/cloud-billing.readonly",
                    "https://www.googleapis.com/auth/cloud-platform.read-only",
                ])
                scoped_creds.refresh(google.auth.transport.requests.Request())
                token = scoped_creds.token

                if billing_account_id:
                    import urllib.request as _urllib_req
                    year = dt_start.year
                    month = dt_start.month
                    url = (
                        f"https://cloudbilling.googleapis.com/v1/billingAccounts/"
                        f"{billing_account_id}/invoices"
                        f"?filter=invoice_month%3D{year:04d}{month:02d}"
                    )
                    req = _urllib_req.Request(url, headers={"Authorization": f"Bearer {token}"})
                    try:
                        with _urllib_req.urlopen(req) as resp:
                            data = json.loads(resp.read())
                            invoices = data.get("invoices", [])
                            for invoice in invoices:
                                for subtotal in invoice.get("subtotals", []):
                                    total_cost += float(subtotal.get("units", 0) or 0) + (int(subtotal.get("nanos", 0) or 0) / 1e9)
                                    if subtotal.get("currencyCode"):
                                        currency_code = subtotal["currencyCode"]
                            logger.info(f"Cloud Billing invoices API: fetched total_cost={total_cost} {currency_code}")
                    except Exception as http_e:
                        logger.warning(f"Invoices API 권한 없음: {http_e}")
            except Exception as rest_e:
                logger.warning(f"Cloud Billing REST API fallback failed: {rest_e}")
                logger.error(
                    "BigQuery billing export is not configured."
                )

        return {
            "status": "success",
            "summary": {
                "account_count": len(accounts),
                "active_accounts": len([a for a in accounts if a.open_]),
                "total_budget": total_budget,
                "total_cost": round(total_cost, 2),
                "currency_code": currency_code,
                "start_date": period_start,
                "end_date": period_end,
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/billing/budgets")
async def list_budgets(
    billing_account_id: str,
    name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    try:
        credential = await _get_credential(db, name)
        creds = _get_credentials_obj(credential)
        client = budgets_v1.BudgetServiceClient(credentials=creds)

        budgets = []
        request = budgets_v1.ListBudgetsRequest(
            parent=f"billingAccounts/{billing_account_id}"
        )
        for budget in log_gcp_call("BudgetService", "list_budgets", client.list_budgets, request=request):
            budgets.append({
                "name": budget.name,
                "display_name": budget.display_name,
                "amount": {
                    "specified_amount": {
                        "currency_code": budget.amount.specified_amount.currency_code,
                        "units": budget.amount.specified_amount.units,
                        "nanos": budget.amount.specified_amount.nanos,
                        "total": budget.amount.specified_amount.units + (budget.amount.specified_amount.nanos / 1e9),
                    } if budget.amount.specified_amount else None,
                    "last_period_amount": bool(budget.amount.last_period_amount),
                },
                "threshold_rules": [
                    {
                        "threshold_percent": rule.threshold_percent,
                        "spend_basis": rule.spend_basis.name,
                    }
                    for rule in budget.threshold_rules
                ],
            })
        return {"status": "success", "budgets": budgets}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/billing/budgets")
async def create_budget(
    billing_account_id: str,
    display_name: str,
    amount_currency_code: str = "USD",
    amount_units: int = 1000,
    threshold_percents: List[float] = [0.5, 0.8, 1.0],
    name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    try:
        credential = await _get_credential(db, name)
        creds = _get_credentials_obj(credential)
        client = budgets_v1.BudgetServiceClient(credentials=creds)

        budget = budgets_v1.Budget(
            display_name=display_name,
            amount=budgets_v1.BudgetAmount(
                specified_amount={
                    "currency_code": amount_currency_code,
                    "units": amount_units,
                }
            ),
            threshold_rules=[
                budgets_v1.ThresholdRule(threshold_percent=p)
                for p in threshold_percents
            ],
        )
        request = budgets_v1.CreateBudgetRequest(
            parent=f"billingAccounts/{billing_account_id}",
            budget=budget,
        )
        result = log_gcp_call("BudgetService", "create_budget", client.create_budget, request=request)
        return {"status": "success", "budget_name": result.name}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/billing/budgets/{budget_id}")
async def delete_budget(
    billing_account_id: str,
    budget_id: str,
    name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    try:
        credential = await _get_credential(db, name)
        creds = _get_credentials_obj(credential)
        client = budgets_v1.BudgetServiceClient(credentials=creds)

        request = budgets_v1.DeleteBudgetRequest(
            name=f"billingAccounts/{billing_account_id}/budgets/{budget_id}"
        )
        log_gcp_call("BudgetService", "delete_budget", client.delete_budget, request=request)
        return {"status": "success", "message": "Budget deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/bigquery/billing-export")
async def query_billing_export(
    dataset: str = "all_billing_data",
    table: str = "gcp_billing_export_v1",
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: int = 100,
    name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    try:
        credential = await _get_credential(db, name)
        creds = _get_credentials_obj(credential)
        client = bigquery.Client(
            credentials=creds, project=credential.project_id
        )

        where_clauses = []
        if start:
            where_clauses.append(f"usage_start_time >= '{start}'")
        if end:
            where_clauses.append(f"usage_end_time <= '{end}'")

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        query = f"""
            SELECT
                billing_account_id,
                service.description AS service,
                sku.description AS sku,
                usage_start_time,
                usage_end_time,
                cost,
                currency
            FROM `{credential.project_id}.{dataset}.{table}`
            {where_sql}
            ORDER BY usage_start_time DESC
            LIMIT {limit}
        """
        query_job = log_gcp_call("BigQuery", "query", client.query, query)
        rows = [dict(row) for row in query_job]
        return {"status": "success", "rows": rows, "total": len(rows)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/bigquery/datasets")
async def list_datasets(name: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    try:
        credential = await _get_credential(db, name)
        creds = _get_credentials_obj(credential)
        client = bigquery.Client(
            credentials=creds, project=credential.project_id
        )

        datasets = []
        for ds in log_gcp_call("BigQuery", "list_datasets", client.list_datasets):
            datasets.append({
                "dataset_id": ds.dataset_id,
                "full_dataset_id": ds.full_dataset_id,
                "friendly_name": ds.friendly_name,
            })
        return {"status": "success", "datasets": datasets}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/bigquery/reservations")
async def list_reservations(
    location: str = "US",
    name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    try:
        credential = await _get_credential(db, name)
        creds = _get_credentials_obj(credential)
        client = ReservationServiceClient(credentials=creds)

        parent = f"projects/{credential.project_id}/locations/{location}"
        reservations = []
        for res in log_gcp_call("BigQueryReservation", "list_reservations", client.list_reservations, parent=parent):
            reservations.append({
                "name": res.name,
                "slot_capacity": res.slot_capacity,
                "ignore_idle_slots": res.ignore_idle_slots,
                "edition": res.edition.name if res.edition else None,
            })
        return {"status": "success", "reservations": reservations}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/bigquery/transfer-configs")
async def list_transfer_configs(
    name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    try:
        credential = await _get_credential(db, name)
        creds = _get_credentials_obj(credential)
        client = bigquery_datatransfer_v1.DataTransferServiceClient(credentials=creds)

        parent = f"projects/{credential.project_id}"
        configs = []
        for config in log_gcp_call("BigQueryDataTransfer", "list_transfer_configs", client.list_transfer_configs, parent=parent):
            configs.append({
                "name": config.name,
                "display_name": config.display_name,
                "data_source_id": config.data_source_id,
                "state": config.state.name,
                "schedule": config.schedule,
            })
        return {"status": "success", "transfer_configs": configs}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




@app.get("/monitoring/metrics")
async def query_metrics(
    metric_type: str = "compute.googleapis.com/instance/cpu/utilization",
    hours: int = 24,
    name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    try:
        credential = await _get_credential(db, name)
        creds = _get_credentials_obj(credential)
        client = monitoring_v3.MetricServiceClient(credentials=creds)

        from google.protobuf import timestamp_pb2
        import time

        now = time.time()
        interval = monitoring_v3.TimeInterval(
            end_time=timestamp_pb2.Timestamp(seconds=int(now)),
            start_time=timestamp_pb2.Timestamp(seconds=int(now - hours * 3600)),
        )
        results = log_gcp_call("Monitoring", "list_time_series", client.list_time_series,
            request={
                "name": f"projects/{credential.project_id}",
                "filter": f'metric.type = "{metric_type}"',
                "interval": interval,
                "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
            }
        )
        series_list = []
        for ts in results:
            points = []
            for point in ts.points:
                points.append({
                    "interval_start": str(point.interval.start_time),
                    "interval_end": str(point.interval.end_time),
                    "value": point.value.double_value or point.value.int64_value,
                })
            series_list.append({
                "metric_kind": ts.metric_kind.name,
                "resource_type": ts.resource.type_,
                "resource_labels": dict(ts.resource.labels),
                "points": points[:20],  # 최대 20개 포인트
            })
        return {"status": "success", "time_series": series_list}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/logging/entries")
async def list_log_entries(
    filter_str: str = 'resource.type="gce_instance"',
    hours: int = 24,
    limit: int = 50,
    name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    try:
        credential = await _get_credential(db, name)
        creds = _get_credentials_obj(credential)
        client = gcp_logging_v2.Client(credentials=creds, project=credential.project_id)

        from datetime import datetime, timedelta, timezone

        start_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        time_filter = f'timestamp >= "{start_time.isoformat()}"'
        full_filter = f"{filter_str} AND {time_filter}" if filter_str else time_filter

        entries = []
        for entry in log_gcp_call("Logging", "list_entries", client.list_entries,
            filter_=full_filter,
            order_by=gcp_logging_v2.DESCENDING,
            max_results=limit,
        ):
            entries.append({
                "log_name": entry.log_name,
                "severity": entry.severity,
                "timestamp": str(entry.timestamp),
                "resource_type": entry.resource.type if entry.resource else None,
                "payload": str(entry.payload),
            })
        return {"status": "success", "entries": entries, "total": len(entries)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/assets")
async def list_assets(
    asset_types: Optional[List[str]] = None,
    content_type: str = "RESOURCE",
    name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    try:
        credential = await _get_credential(db, name)
        creds = _get_credentials_obj(credential)
        client = asset_v1.AssetServiceClient(credentials=creds)

        content_type_enum = asset_v1.ContentType[content_type]
        request = asset_v1.ListAssetsRequest(
            parent=f"projects/{credential.project_id}",
            content_type=content_type_enum,
            asset_types=asset_types or [],
        )
        assets = []
        for asset in log_gcp_call("Asset", "list_assets", client.list_assets, request=request):
            assets.append({
                "name": asset.name,
                "asset_type": asset.asset_type,
                "update_time": str(asset.update_time),
            })
            if len(assets) >= 200:
                break
        return {"status": "success", "assets": assets, "total": len(assets)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/assets/search")
async def search_assets(
    query: str = "",
    asset_types: Optional[List[str]] = None,
    name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    try:
        credential = await _get_credential(db, name)
        creds = _get_credentials_obj(credential)
        client = asset_v1.AssetServiceClient(credentials=creds)

        request = asset_v1.SearchAllResourcesRequest(
            scope=f"projects/{credential.project_id}",
            query=query,
            asset_types=asset_types or [],
        )
        resources = []
        for resource in log_gcp_call("Asset", "search_all_resources", client.search_all_resources, request=request):
            resources.append({
                "name": resource.name,
                "asset_type": resource.asset_type,
                "project": resource.project,
                "display_name": resource.display_name,
                "location": resource.location,
                "state": resource.state,
            })
            if len(resources) >= 200:
                break
        return {"status": "success", "resources": resources, "total": len(resources)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/recommendations")
async def get_gcp_recommendations(name: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    try:
        credential = await _get_credential(db, name)
        creds = _get_credentials_obj(credential)
        client = recommender_v1.RecommenderClient(credentials=creds)

        recommenders = [
            ("Compute Engine", "google.compute.instance.IdleResourceRecommender", "global"),
            ("Compute Engine", "google.compute.instance.MachineTypeRecommender", "us-central1-a"),
            ("Cloud Storage", "google.compute.disk.IdleResourceRecommender", "us-central1-a"),
            ("Billing", "google.cloudbilling.billingaccount.CostInsightsRecommender", "global"),
        ]
        
        recommendations = []
        for service, rec_type, location in recommenders:
            try:
                parent = f"projects/{credential.project_id}/locations/{location}/recommenders/{rec_type}"
                for rec in client.list_recommendations(parent=parent):
                    impact_amount = 0
                    if rec.primary_impact and rec.primary_impact.cost_projection:
                        cost = rec.primary_impact.cost_projection.cost
                        impact_amount = cost.units + (cost.nanos / 1e9)
                    
                    recommendations.append({
                        "name": rec.name,
                        "service": service,
                        "description": rec.description,
                        "impact": impact_amount,
                        "category": rec.recommender_subtype,
                        "last_refresh_time": str(rec.last_refresh_time)
                    })
            except Exception as e:
                logger.warning(f"recommendations failed {rec_type} / {location}: {e}")

        return {"status": "success", "recommendations": recommendations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/quotas")
async def list_quotas(
    service: str = "compute.googleapis.com",
    name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    try:
        credential = await _get_credential(db, name)
        creds = _get_credentials_obj(credential)
        client = cloudquotas_v1.CloudQuotasClient(credentials=creds)

        parent = f"projects/{credential.project_id}/locations/global/services/{service}"
        quota_infos = []
        for qi in log_gcp_call("CloudQuotas", "list_quota_infos", client.list_quota_infos, parent=parent):
            quota_infos.append({
                "name": qi.name,
                "quota_id": qi.quota_id,
                "metric": qi.metric,
                "is_precise": qi.is_precise,
                "container_type": qi.container_type.name if qi.container_type else None,
            })
        return {"status": "success", "quota_infos": quota_infos}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/quotas/preferences")
async def list_quota_preferences(
    name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    try:
        credential = await _get_credential(db, name)
        creds = _get_credentials_obj(credential)
        client = cloudquotas_v1.CloudQuotasClient(credentials=creds)

        parent = f"projects/{credential.project_id}/locations/global"
        preferences = []
        for pref in log_gcp_call("CloudQuotas", "list_quota_preferences", client.list_quota_preferences, parent=parent):
            preferences.append({
                "name": pref.name,
                "quota_id": pref.quota_id,
                "service": pref.service,
                "reconciling": pref.reconciling,
            })
        return {"status": "success", "quota_preferences": preferences}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/org-policy/constraints")
async def list_org_constraints(
    name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    try:
        credential = await _get_credential(db, name)
        creds = _get_credentials_obj(credential)
        client = orgpolicy_v2.OrgPolicyClient(credentials=creds)

        parent = f"projects/{credential.project_id}"
        constraints = []
        for constraint in log_gcp_call("OrgPolicy", "list_constraints", client.list_constraints, parent=parent):
            constraints.append({
                "name": constraint.name,
                "display_name": constraint.display_name,
                "description": constraint.description,
                "constraint_default": constraint.constraint_default.name
                if constraint.constraint_default
                else None,
            })
        return {"status": "success", "constraints": constraints}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/org-policy/policies")
async def list_org_policies(
    name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    try:
        credential = await _get_credential(db, name)
        creds = _get_credentials_obj(credential)
        client = orgpolicy_v2.OrgPolicyClient(credentials=creds)

        parent = f"projects/{credential.project_id}"
        policies = []
        for policy in client.list_policies(parent=parent):
            rules = []
            if policy.spec and policy.spec.rules:
                for rule in policy.spec.rules:
                    rules.append({
                        "allow_all": rule.allow_all if hasattr(rule, "allow_all") else None,
                        "deny_all": rule.deny_all if hasattr(rule, "deny_all") else None,
                        "enforce": rule.enforce if hasattr(rule, "enforce") else None,
                    })
            policies.append({
                "name": policy.name,
                "rules": rules,
            })
        return {"status": "success", "policies": policies}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/service-usage/services")
async def list_services(
    filter_str: str = "state:ENABLED",
    name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    try:
        credential = await _get_credential(db, name)
        creds = _get_credentials_obj(credential)
        client = service_usage_v1.ServiceUsageClient(credentials=creds)

        request = service_usage_v1.ListServicesRequest(
            parent=f"projects/{credential.project_id}",
            filter=filter_str,
        )
        services = []
        for svc in log_gcp_call("ServiceUsage", "list_services", client.list_services, request=request):
            services.append({
                "name": svc.name,
                "config": {
                    "title": svc.config.title if svc.config else None,
                    "name": svc.config.name if svc.config else None,
                },
                "state": svc.state.name,
            })
        return {"status": "success", "services": services}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/service-usage/services/{service_name}/enable")
async def enable_service(
    service_name: str,
    name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    try:
        credential = await _get_credential(db, name)
        creds = _get_credentials_obj(credential)
        client = service_usage_v1.ServiceUsageClient(credentials=creds)

        request = service_usage_v1.EnableServiceRequest(
            name=f"projects/{credential.project_id}/services/{service_name}"
        )
        operation = log_gcp_call("ServiceUsage", "enable_service", client.enable_service, request=request)
        result = log_gcp_call("Operation", "result", operation.result)
        return {"status": "success", "service": result.service.name if result.service else service_name}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/service-usage/services/{service_name}/disable")
async def disable_service(
    service_name: str,
    name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    try:
        credential = await _get_credential(db, name)
        creds = _get_credentials_obj(credential)
        client = service_usage_v1.ServiceUsageClient(credentials=creds)

        request = service_usage_v1.DisableServiceRequest(
            name=f"projects/{credential.project_id}/services/{service_name}"
        )
        operation = client.disable_service(request=request)
        result = operation.result()
        return {"status": "success", "message": f"Service {service_name} disabled"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dashboard/stats")
async def get_dashboard_stats(
    billing_account_id: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    granularity: str = "MONTHLY",
    dataset: str = "all_billing_data",
    table: str = "gcp_billing_export_v1",
    name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    try:
        credential = await _get_credential(db, name)
        creds_obj = _get_credentials_obj(credential)
        if not billing_account_id:
            billing_account_id = credential.billing_account_id

        from datetime import timedelta
        now = datetime.now()
        
        try:
            if start:
                dt_start = datetime.strptime(start, "%Y-%m-%d")
            else:
                dt_start = now.replace(day=1)
                
            if end:
                dt_end = datetime.strptime(end, "%Y-%m-%d")
            else:
                dt_end = now
        except ValueError:
            dt_start = now.replace(day=1)
            dt_end = now

        current_month_start = dt_start.strftime("%Y-%m-%d")
        current_month_end = dt_end.strftime("%Y-%m-%d")

        last_month_end = (dt_start - timedelta(days=1))
        last_month_start = last_month_end.replace(day=1).strftime("%Y-%m-%d")
        last_month_end_str = last_month_end.strftime("%Y-%m-%d")

        seven_months_ago = dt_start.replace(day=1)
        for _ in range(6):
            seven_months_ago = (seven_months_ago - timedelta(days=1)).replace(day=1)
        
        if granularity.upper() == "DAILY":
            seven_months_ago = dt_start - timedelta(days=30)
            
        seven_months_start = seven_months_ago.strftime("%Y-%m-%d")

        total_cost = 0
        currency_code = "USD"
        top_services = []
        cost_trend = 0
        monthly_data = []
        daily_data = []
        budget_used = 0
        alerts = 0
        active_resources = 0

        GCP_GROUP_BY_KEY = "service.description"
        cost_cache_hit = False

        try:
            bq_client = bigquery.Client(
                credentials=creds_obj, project=credential.project_id
            )

            if granularity.upper() == "DAILY":
                cached_result = await db.execute(
                    select(GCPDailyCost)
                    .where(GCPDailyCost.credential_id == credential.id)
                    .where(GCPDailyCost.date >= seven_months_start)
                    .where(GCPDailyCost.date <= current_month_end)
                    .order_by(GCPDailyCost.date)
                )
                cached_rows = cached_result.scalars().all()

                expected_days = (dt_end.date() - seven_months_ago.date()).days
                hasAllData = len(cached_rows) >= expected_days
                hasGroupingData = bool(cached_rows) and all(
                    r.grouped_data and GCP_GROUP_BY_KEY in r.grouped_data
                    for r in cached_rows
                )

                if hasAllData and hasGroupingData:
                    logger.info(f"Cache HIT: GCP daily {credential.name}")
                    cost_cache_hit = True
                    svc_agg = {}
                    for r in cached_rows:
                        dt_row = datetime.strptime(r.date, "%Y-%m-%d")
                        daily_data.append({"day": dt_row.strftime("%m/%d"), "cost": round(r.amount)})
                        if r.date >= current_month_start:
                            total_cost += r.amount
                            for svc in (r.grouped_data.get(GCP_GROUP_BY_KEY) or []):
                                sname = svc.get("name", "Unknown")
                                svc_agg[sname] = svc_agg.get(sname, 0) + svc.get("cost", 0)
                    top_services = sorted(
                        [{"name": k, "cost": round(v)} for k, v in svc_agg.items() if v > 0],
                        key=lambda x: -x["cost"]
                    )[:5]
                else:
                    logger.info(f"Cache MISS: GCP daily {credential.name} — calling BigQuery")
                    
                    dataset, resolved_table = _resolve_billing_info(bq_client, credential.project_id, dataset, table, billing_account_id)
                    
                    combined_query = f"""
                        SELECT
                            FORMAT_TIMESTAMP('%Y-%m-%d', usage_start_time) AS day_key,
                            service.description AS service_name,
                            SUM(cost) + SUM((SELECT IFNULL(SUM(c.amount), 0) FROM UNNEST(credits) AS c)) AS daily_cost,
                            ANY_VALUE(currency) as currency
                        FROM `{credential.project_id}.{dataset}.{resolved_table}`
                        WHERE usage_start_time >= TIMESTAMP('{seven_months_start}')
                          AND usage_start_time <= TIMESTAMP('{current_month_end} 23:59:59')
                        GROUP BY day_key, service_name
                        ORDER BY day_key ASC
                    """
                    combined_result = log_gcp_call("BigQuery", "query", bq_client.query, combined_query)

                    day_totals = {}
                    day_services = {}
                    currency_code = "USD"
                    for row in combined_result:
                        day_key = row["day_key"]
                        svc_name = row["service_name"] or "Unknown"
                        cost_val = float(row["daily_cost"] or 0)
                        if row["currency"]:
                            currency_code = row["currency"]
                        day_totals[day_key] = day_totals.get(day_key, 0) + cost_val
                        if day_key not in day_services:
                            day_services[day_key] = {}
                        day_services[day_key][svc_name] = day_services[day_key].get(svc_name, 0) + cost_val

                    svc_agg_all = {}
                    for day_key in sorted(day_totals.keys()):
                        dt_row = datetime.strptime(day_key, "%Y-%m-%d")
                        daily_data.append({"day": dt_row.strftime("%m/%d"), "cost": round(day_totals[day_key])})
                        if day_key >= current_month_start:
                            total_cost += day_totals[day_key]
                            for svc, cost_v in day_services.get(day_key, {}).items():
                                svc_agg_all[svc] = svc_agg_all.get(svc, 0) + cost_v

                    top_services = sorted(
                        [{"name": k, "cost": round(v)} for k, v in svc_agg_all.items() if v > 0],
                        key=lambda x: -x["cost"]
                    )[:5]

                    for day_key, day_amount in day_totals.items():
                        existing = await db.execute(
                            select(GCPDailyCost).where(
                                GCPDailyCost.credential_id == credential.id,
                                GCPDailyCost.date == day_key
                            )
                        )
                        dc = existing.scalars().first()
                        if not dc:
                            dc = GCPDailyCost(credential_id=credential.id, date=day_key)
                        dc.amount = day_amount
                        dc.unit = currency_code
                        svc_list = [{"name": k, "cost": v} for k, v in day_services.get(day_key, {}).items()]
                        dc.grouped_data = {GCP_GROUP_BY_KEY: svc_list}
                        db.add(dc)
                    await db.commit()
                    cost_cache_hit = True

            if not cost_cache_hit:
                MONTHLY_KEY = "monthly_svc"
                month_names = ['1월', '2월', '3월', '4월', '5월', '6월', '7월', '8월', '9월', '10월', '11월', '12월']

                # ── Build first-of-month date keys ───────────────────────────────
                first_of_months: list[str] = []
                _m = seven_months_ago.replace(day=1)
                while _m.strftime("%Y-%m") <= dt_end.strftime("%Y-%m"):
                    first_of_months.append(_m.strftime("%Y-%m-01"))
                    _m = (_m + timedelta(days=32)).replace(day=1)
                current_month_date = datetime.now().strftime("%Y-%m-01")

                # ── DB cache check ───────────────────────────────────────────────
                db_result = await db.execute(
                    select(GCPDailyCost)
                    .where(GCPDailyCost.credential_id == credential.id)
                    .where(GCPDailyCost.date.in_(first_of_months))
                    .order_by(GCPDailyCost.date)
                )
                db_rows = {r.date: r for r in db_result.scalars().all()}

                def _is_fresh_gcp(row) -> bool:
                    if row is None or row.updated_at is None:
                        return False
                    updated = row.updated_at.replace(tzinfo=None) if row.updated_at.tzinfo else row.updated_at
                    return (datetime.utcnow() - updated).total_seconds() < 3600

                db_cache_hit = (
                    all(d in db_rows and db_rows[d].grouped_data and MONTHLY_KEY in db_rows[d].grouped_data
                        for d in first_of_months)
                    and _is_fresh_gcp(db_rows.get(current_month_date))
                )

                if db_cache_hit:
                    logger.info(f"Cache HIT (DB): GCP monthly cost {credential.name}")
                    last_total = 0.0
                    last_month_date = (datetime.now().replace(day=1) - timedelta(days=1)).strftime("%Y-%m-01")
                    for d in sorted(db_rows.keys()):
                        r = db_rows[d]
                        dt_r = datetime.strptime(d, "%Y-%m-01")
                        m_idx = dt_r.month - 1
                        monthly_data.append({
                            "month": month_names[m_idx],
                            "cost": round(r.amount)
                        })
                        if d == current_month_date:
                            total_cost = r.amount
                            currency_code = r.unit or "USD"
                            top_services = r.grouped_data.get(MONTHLY_KEY, [])
                        if d == last_month_date:
                            last_total = r.amount
                    if last_total > 0 and total_cost > 0:
                        cost_trend = round(((total_cost - last_total) / last_total) * 100, 1)
                    cost_cache_hit = True
                else:
                    logger.info(f"Cache MISS (DB): GCP monthly cost {credential.name} — calling BigQuery")
                    dataset, resolved_table = _resolve_billing_info(bq_client, credential.project_id, dataset, table, billing_account_id)

                    current_cost_query = f"""
                        SELECT
                            IFNULL(SUM(cost + (SELECT IFNULL(SUM(c.amount), 0) FROM UNNEST(credits) AS c)), 0) AS total_cost,
                            ANY_VALUE(currency) as currency
                        FROM `{credential.project_id}.{dataset}.{resolved_table}`
                        WHERE usage_start_time >= '{current_month_start}'
                          AND usage_start_time <= '{current_month_end}T23:59:59'
                    """
                    current_result = log_gcp_call("BigQuery", "query", bq_client.query, current_cost_query)
                    for row in current_result:
                        total_cost = float(row["total_cost"])
                        if row["currency"]:
                            currency_code = row["currency"]

                    service_query = f"""
                        SELECT
                            service.description AS service_name,
                            SUM(cost + (SELECT IFNULL(SUM(c.amount), 0) FROM UNNEST(credits) AS c)) AS service_cost
                        FROM `{credential.project_id}.{dataset}.{resolved_table}`
                        WHERE usage_start_time >= '{current_month_start}'
                          AND usage_start_time <= '{current_month_end}T23:59:59'
                        GROUP BY service.description
                        HAVING service_cost > 0
                        ORDER BY service_cost DESC
                        LIMIT 5
                    """
                    service_result = log_gcp_call("BigQuery", "query", bq_client.query, service_query)
                    for row in service_result:
                        top_services.append({
                            "name": row["service_name"],
                            "cost": round(float(row["service_cost"]))
                        })

                    monthly_query = f"""
                        SELECT
                            FORMAT_TIMESTAMP('%Y-%m', usage_start_time) AS month_key,
                            EXTRACT(MONTH FROM usage_start_time) AS month_num,
                            SUM(cost + (SELECT IFNULL(SUM(c.amount), 0) FROM UNNEST(credits) AS c)) AS monthly_cost
                        FROM `{credential.project_id}.{dataset}.{resolved_table}`
                        WHERE usage_start_time >= '{seven_months_start}'
                        GROUP BY month_key, month_num
                        ORDER BY month_key ASC
                    """
                    monthly_result = bq_client.query(monthly_query)
                    monthly_by_date: dict = {}
                    last_total = 0.0
                    last_month_str_gcp = (datetime.now().replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
                    for row in monthly_result:
                        m_idx = int(row["month_num"]) - 1
                        cost_val = round(float(row["monthly_cost"]))
                        month_key = str(row["month_key"])
                        monthly_data.append({
                            "month": month_names[m_idx] if 0 <= m_idx < 12 else month_key,
                            "cost": cost_val
                        })
                        d_key = f"{month_key}-01"
                        monthly_by_date[d_key] = cost_val
                        if month_key == last_month_str_gcp:
                            last_total = cost_val
                    if last_total > 0 and total_cost > 0:
                        cost_trend = round(((total_cost - last_total) / last_total) * 100, 1)

                    last_cost_query = f"""
                        SELECT
                            IFNULL(SUM(cost + (SELECT IFNULL(SUM(c.amount), 0) FROM UNNEST(credits) AS c)), 0) AS total_cost
                        FROM `{credential.project_id}.{dataset}.{resolved_table}`
                        WHERE usage_start_time >= '{last_month_start}'
                          AND usage_start_time < '{last_month_end_str}T23:59:59'
                    """
                    last_result = log_gcp_call("BigQuery", "query", bq_client.query, last_cost_query)
                    for row in last_result:
                        last_total = float(row["total_cost"])
                        if last_total > 0:
                            cost_trend = round(((total_cost - last_total) / last_total) * 100, 1)

                    # ── Write monthly aggregates to DB ───────────────────────────
                    monthly_by_date[current_month_date] = total_cost
                    for d_key, month_amount in monthly_by_date.items():
                        ex = await db.execute(
                            select(GCPDailyCost).where(
                                GCPDailyCost.credential_id == credential.id,
                                GCPDailyCost.date == d_key,
                            )
                        )
                        dc = ex.scalars().first()
                        if not dc:
                            dc = GCPDailyCost(credential_id=credential.id, date=d_key)
                        dc.amount = month_amount
                        dc.unit = currency_code
                        dc.grouped_data = {
                            MONTHLY_KEY: top_services if d_key == current_month_date else []
                        }
                        db.add(dc)
                    if monthly_by_date:
                        await db.commit()

        except Exception as e:
            logger.error(f"BigQuery Failed: {e}")
            total_cost, currency_code = _get_monitoring_total_cost(creds_obj, credential.project_id)

        budget_used = 0
        alertsCount = 0
        recent_alerts = []

        if billing_account_id:
            try:
                budget_client = budgets_v1.BudgetServiceClient(credentials=creds_obj)
                request = budgets_v1.ListBudgetsRequest(
                    parent=f"billingAccounts/{billing_account_id}"
                )
                budget_list = list(log_gcp_call("BudgetService", "list_budgets", budget_client.list_budgets, request=request))
                if budget_list:
                    budget = budget_list[0]
                    if budget.amount.specified_amount:
                        budget_amount = float(budget.amount.specified_amount.units) + (budget.amount.specified_amount.nanos / 1e9)
                        if budget_amount > 0:
                            budget_used = round((total_cost / budget_amount) * 100)
                    
                    for b in budget_list:
                        if b.amount.specified_amount:
                            b_amount = float(b.amount.specified_amount.units) + (b.amount.specified_amount.nanos / 1e9)
                            if b_amount > 0 and total_cost > b_amount * 0.8:
                                alertsCount += 1
                                recent_alerts.append({
                                    "message": f"예산 초과 관측: {b.display_name} 예산의 {round((total_cost/b_amount)*100)}% 사용됨",
                                    "severity": "error" if total_cost > b_amount else "warning",
                                    "date": datetime.now().strftime("%Y-%m-%d")
                                })
            except Exception as e:
                print(f"error: {e}")

        try:
            asset_client = asset_v1.AssetServiceClient(credentials=creds_obj)
            request = asset_v1.ListAssetsRequest(
                parent=f"projects/{credential.project_id}",
                content_type=asset_v1.ContentType.RESOURCE,
                asset_types=[
                    "compute.googleapis.com/Instance",
                    "storage.googleapis.com/Bucket",
                    "sqladmin.googleapis.com/Instance",
                    "container.googleapis.com/Cluster",
                ],
            )
            count = 0
            res_summary = []
            for asset in asset_client.list_assets(request=request):
                count += 1
                if len(res_summary) < 5:
                    res_summary.append({
                        "name": asset.name.split('/')[-1],
                        "type": asset.asset_type.split('/')[-1],
                        "status": "Active"
                    })
                if count >= 500:
                    break
            active_resources = count
            resources_summary = res_summary
        except Exception as e:
            print(f"Asset count error: {e}")
            resources_summary = []

        recommendations = []
        try:
            recommender_client = recommender_v1.RecommenderClient(credentials=creds_obj)
            parent = f"projects/{credential.project_id}/locations/global/recommenders/google.compute.instance.IdleResourceRecommender"
            for rec in recommender_client.list_recommendations(parent=parent):
                recommendations.append({
                    "service": "Compute Engine",
                    "title": "Idle VM detected",
                    "impact": f"${rec.primary_impact.cost_projection.cost.units}/month" if rec.primary_impact and rec.primary_impact.cost_projection else "Unknown",
                    "description": rec.description
                })
        except Exception as e:
            print(f"Recommender query error: {e}")

        return {
            "totalCost": round(total_cost, 2),
            "currencyCode": currency_code,
            "costTrend": cost_trend,
            "topServices": top_services,
            "monthlyData": monthly_data,
            "dailyData": daily_data,
            "activeResources": active_resources,
            "budgetUsed": budget_used,
            "alerts": alertsCount,
            "recentAlerts": recent_alerts,
            "recommendations": recommendations,
            "resourcesSummary": resources_summary,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)

