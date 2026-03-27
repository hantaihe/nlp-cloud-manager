from fastapi import FastAPI, HTTPException, Body, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import logging
import json
import time
from langchain.agents import create_agent
from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from typing import Dict, Any

from sqlalchemy import select
from database import AsyncSessionLocal
from models import GCPCredential, AzureCredential, AWSCredential

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HTTP")

CHATBOT_PROVIDER = os.getenv("CHATBOT_PROVIDER", "gemini")   # "ollama" | "gemini"
OLLAMA_MODEL    = os.getenv("CHATBOT_MODEL", "qwen3:0.6b")
GEMINI_MODEL    = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GOOGLE_API_KEY  = os.getenv("GOOGLE_API_KEY", "[GCP_API_KEY]")

def build_model():
    if CHATBOT_PROVIDER == "gemini":
        if not GOOGLE_API_KEY:
            raise RuntimeError("GOOGLE_API_KEY env var is required when CHATBOT_PROVIDER=gemini")
        logger.info(f"Using Gemini model: {GEMINI_MODEL}")
        return ChatGoogleGenerativeAI(model=GEMINI_MODEL, google_api_key=GOOGLE_API_KEY)
    logger.info(f"Using Ollama model: {OLLAMA_MODEL}")
    return ChatOllama(model=OLLAMA_MODEL)

app = FastAPI(title="MCP Chatbot Server")

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
    
    from fastapi.responses import StreamingResponse
    if isinstance(response, StreamingResponse):
        return response

    headers = dict(response.headers)
    if "content-length" in headers:
        del headers["content-length"]

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
        headers=headers
    )

agents: Dict[str, Any] = {}

class Config(BaseModel):
    aws_credential_name: str = ""
    azure_credential_name: str = ""
    gcp_credential_name: str = ""


import json
from google.oauth2 import service_account
import google.auth.transport.requests

def get_gcp_token_and_project(sa_json_str: str):
    try:
        sa_info = json.loads(sa_json_str)
        creds = service_account.Credentials.from_service_account_info(
            sa_info,
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        auth_request = google.auth.transport.requests.Request()
        creds.refresh(auth_request)
        return creds.token, sa_info.get("project_id"), sa_info.get("region", "us-central1")
    except Exception as e:
        print(f"Error generating GCP token: {e}")
        return None, None, None

async def get_mcp_servers(config: Config):
    mcp_servers = {}
    
    async with AsyncSessionLocal() as session:
        if config.aws_credential_name:
            stmt = select(AWSCredential).where(AWSCredential.name == config.aws_credential_name)
            res = await session.execute(stmt)
            aws = res.scalar_one_or_none()
            if aws:
                mcp_servers["awslabs-core-mcp-server"] = {
                    "command": "uvx",
                    "args": ["--python", "3.13", "awslabs.core-mcp-server@latest"],
                    "env": {
                        "FASTMCP_LOG_LEVEL": "ERROR",
                        "AWS_ACCESS_KEY_ID": aws.accessKeyId,
                        "AWS_SECRET_ACCESS_KEY": aws.secretAccessKey,
                        "AWS_REGION": aws.region,
                        "aws-foundation": "true",
                        "dev-tools": "true",
                        "ci-cd-devops": "true",
                        "container-orchestration": "true",
                        "serverless-architecture": "true",
                        "analytics-warehouse": "true",
                        "data-platform-eng": "true",
                        "frontend-dev": "true",
                        "solutions-architect": "true",
                        "finops": "true",
                        "monitoring-observability": "true",
                        "caching-performance": "true",
                        "security-identity": "true",
                        "sql-db-specialist": "true",
                        "timeseries-db-specialist": "true",
                        "messaging-events": "true",
                    },
                    "transport": "stdio"
                }

        if config.azure_credential_name:
            stmt = select(AzureCredential).where(AzureCredential.name == config.azure_credential_name)
            res = await session.execute(stmt)
            azure = res.scalar_one_or_none()
            if azure:
                mcp_servers["Azure MCP Server"] = {
                    "command": "uvx",
                    "args": ["--from", "msmcp-azure", "azmcp", "server", "start"],
                    "env": {
                        "AZURE_TENANT_ID": azure.tenant_id,
                        "AZURE_CLIENT_ID": azure.client_id,
                        "AZURE_CLIENT_SECRET": azure.client_secret
                    },
                    "transport": "stdio"
                }

        if config.gcp_credential_name:
            stmt = select(GCPCredential).where(GCPCredential.name == config.gcp_credential_name)
            res = await session.execute(stmt)
            gcp = res.scalar_one_or_none()
            if gcp:
                token, project_id, region = get_gcp_token_and_project(gcp.service_account_json)
                if token and project_id:
                    mcp_servers.update({
                        "gcp-resource-manager": {
                            "url": "https://cloudresourcemanager.googleapis.com/mcp",
                            "headers": {
                                "Authorization": f"Bearer {token}",
                                "x-goog-user-project": project_id
                            },
                            "transport": "http"
                        },
                        "gcp-compute": {
                            "url": "https://compute.googleapis.com/mcp",
                            "headers": {
                                "Authorization": f"Bearer {token}",
                                "x-goog-user-project": project_id
                            },
                            "transport": "http"
                        },
                        "gcp-sql": {
                            "url": "https://sqladmin.googleapis.com/mcp",
                            "headers": {
                                "Authorization": f"Bearer {token}",
                                "x-goog-user-project": project_id
                            },
                            "transport": "http"
                        },
                        "gcp-bigquery": {
                            "url": "https://bigquery.googleapis.com/mcp",
                            "headers": {
                                "Authorization": f"Bearer {token}",
                                "x-goog-user-project": project_id
                            },
                            "transport": "http"
                        },
                        "gcp-bigtable": {
                            "url": "https://bigtableadmin.googleapis.com/mcp",
                            "headers": {
                                "Authorization": f"Bearer {token}",
                                "x-goog-user-project": project_id
                            },
                            "transport": "http"
                        },
                        "gcp-alloydb": {
                            "url": f"https://alloydb.{region}.rep.googleapis.com/mcp",
                            "headers": {
                                "Authorization": f"Bearer {token}",
                                "x-goog-user-project": project_id
                            },
                            "transport": "http"
                        },
                        "google-developer-knowledge": {
                            "url": "https://developerknowledge.googleapis.com/mcp",
                            "headers": {
                                "Authorization": f"Bearer {token}",
                                "x-goog-user-project": project_id
                            },
                            "transport": "http"
                        },
                        "gcp-gke": {
                            "url": "https://container.googleapis.com/mcp",
                            "headers": {
                                "Authorization": f"Bearer {token}",
                                "x-goog-user-project": project_id
                            },
                            "transport": "http"
                        },
                        "gcp-spanner": {
                            "url": "https://spanner.googleapis.com/mcp",
                            "headers": {
                                "Authorization": f"Bearer {token}",
                                "x-goog-user-project": project_id
                            },
                            "transport": "http"
                        },
                    })

    return mcp_servers

async def get_or_create_agent(session_id: str, config: Config):
    if session_id not in agents:
        mcp_servers = await get_mcp_servers(config)
        mcp_client = MultiServerMCPClient(mcp_servers)

        logger.info(f"Creating new agent for session: {session_id}")
        model = build_model()
        tools = await mcp_client.get_tools()

        prompt = """
        당신은 전 세계 최고의 "멀티 클라우드 플랫폼 전문가(Multi-Cloud Platform Expert)"입니다.
        사용자의 인프라(AWS, Azure, GCP)를 분석, 설계 및 운영하는 임무를 맡고 있습니다.

        1. 핵심
        - 분석적 사고: 단순히 리소스를 생성하는 것이 아니라, 왜 해당 서비스를 선택해야 하는지 아키텍처 관점에서 설명합니다.
        - 클라우드 중립성: 특정 벤더에 편향되지 않고, 비용 효율성과 성능(Latency, Throughput)에 기반하여 최적의 클라우드를 추천합니다.
        - Security First: 모든 제안에는 IAM 권한 최소화, 데이터 암호화, 네트워크 격리 등 보안 모범 사례가 포함되어야 합니다.

        2. 클라우드별 전문 지식 활용 가이드
        - AWS (awslabs-core-mcp-server): EC2, S3, RDS 등 핵심 서비스와 Well-Architected Framework를 기준으로 답변하십시오.
        - Azure (msmcp-azure): Enterprise 구조, Entra ID(Active Directory) 통합, Azure Native 서비스와의 연동을 중점적으로 다룹니다.
        - GCP (Google Cloud APIs):
            - 인프라 관리 시 Resource Manager와 Compute Engine을 적극 활용하십시오.
            - 기술적 궁금증은 반드시 'google-developer-knowledge' 도구의 `search_documents`를 먼저 호출하여 최신 문서를 기반으로 답변하십시오.
            - 상세 구현 코드가 필요하면 `get_document`를 통해 컨텍스트를 확보하십시오.

        3. 작업 수행 순서
        - Step 1. 상황 파악: 사용자의 요구사항이 특정 클라우드에 종속적인지, 멀티 클라우드 구성인지 먼저 파악하십시오.
        - Step 2. 도구 활용: 가능한 경우 도구를 사용하여 현재 리소스 상태나 공식 문서를 실시간으로 확인하십시오.
        - Step 3. 비교 분석: 클라우드 간 서비스 비교 요청 시(예: AWS Lambda vs GCP Functions), 실행 환경, 트리거 방식, Cold Start 특성, 가격 정책을 표 형식으로 비교하여 제시하십시오.
        - Step 4. 실행 및 검증: 리소스 생성이나 변경 요청 시, 예상되는 영향(Impact)을 먼저 설명한 뒤 실행하십시오.

        4. 제약 사항
        - 자격 증명(Access Key, Secret 등)은 절대 노출하지 마십시오.
        - 복잡한 인프라 구성 시 가급적 Terraform이나 CloudFormation 같은 IaC 코드를 함께 제안하십시오.
        - 답변은 전문적이면서도 명확한 한국어로 작성하되, 기술 용어는 원문을 병기하십시오.
        """

        agents[session_id] = create_agent(
            system_prompt=prompt,
            model=model,
            tools=tools
        )
    return agents[session_id]

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    config: Config

@app.post("/chat")
async def chat(request: ChatRequest):
    agent = await get_or_create_agent(request.session_id, request.config)
    try:
        result = await agent.ainvoke({"messages": [{"role": "user", "content": request.message}]})
        return {"reply": result["messages"][-1].content, "session_id": request.session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi.responses import StreamingResponse
import json
import asyncio
import re

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    agent = await get_or_create_agent(request.session_id, request.config)

    async def event_generator():
        try:
            result = await agent.ainvoke({"messages": [{"role": "user", "content": request.message}]})
            full_text = result["messages"][-1].content

            think_match = re.search(r'<think>(.*?)</think>', full_text, re.DOTALL)
            if think_match:
                thinking_content = think_match.group(1).strip()
                response_content = re.sub(r'<think>.*?</think>', '', full_text, flags=re.DOTALL).strip()
            else:
                thinking_content = ""
                response_content = full_text.strip()

            if thinking_content:
                for i in range(0, len(thinking_content), 8):
                    yield json.dumps({"type": "thinking", "token": thinking_content[i:i+8]}) + "\n"
                    await asyncio.sleep(0.01)
                yield json.dumps({"type": "thinking_done"}) + "\n"
                await asyncio.sleep(0.15)

            for i in range(0, len(response_content), 12):
                yield json.dumps({"type": "token", "token": response_content[i:i+12]}) + "\n"
                await asyncio.sleep(0.025)

            yield json.dumps({"type": "done"}) + "\n"

        except Exception as e:
            yield json.dumps({"type": "error", "error": str(e)}) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")

@app.post("/clear")
async def clear_session(request: Dict[str, str] = Body(...)):
    session_id = request.get("session_id", "default")
    if session_id in agents:
        del agents[session_id]
        logger.info(f"Cleared session: {session_id}")
    return {"status": "cleared", "session_id": session_id}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)
