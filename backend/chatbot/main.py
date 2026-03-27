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
OLLAMA_MODEL    = os.getenv("CHATBOT_MODEL", "qwen3:1.7b")
GEMINI_MODEL    = os.getenv("GEMINI_MODEL", "gemini-3-pro-preview")
GOOGLE_API_KEY  = os.getenv("GOOGLE_API_KEY", "[GOOGLE_API_KEY]")

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

    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000

    content_type = response.headers.get("content-type", "")
    if "ndjson" in content_type or "event-stream" in content_type:
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
conversation_histories: Dict[str, list] = {}

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
                mcp_servers["awslabs-aws-api-mcp-server"] = {
                    "command": "uvx",
                    "args": ["awslabs.aws-api-mcp-server@latest"],
                    "env": { 
                        "FASTMCP_LOG_LEVEL": "ERROR",
                        "AWS_ACCESS_KEY_ID": aws.accessKeyId,
                        "AWS_SECRET_ACCESS_KEY": aws.secretAccessKey,
                        "AWS_REGION": aws.region,
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

        ## 역할
        당신은 멀티 클라우드 플랫폼 전문가이자 실행 에이전트입니다.
        사용자의 요청에 따라 AWS, Azure, GCP 리소스를 직접 생성·조회·수정·삭제합니다.

        ## 핵심 원칙: 도구를 반드시 호출하라
        - 리소스 생성/조회/수정/삭제 요청이 오면 **반드시 해당 MCP 도구를 호출**하여 실제로 수행하십시오.
        - 코드 예시(Terraform, CLI 명령어 등)만 제공하고 실행을 미루는 것은 금지입니다.
        - 도구 호출 없이 "다음 명령어를 실행하세요" 식의 응답은 허용되지 않습니다.
        - 작업 전 필요한 파라미터가 불분명하면 한 번만 확인하고, 확인 후에는 즉시 실행하십시오.

        ## 작업 수행 절차
        1. **의도 파악**: 생성(Create) / 조회(Read) / 수정(Update) / 삭제(Delete) / 분석 중 무엇인지 판단합니다.
        2. **즉시 실행**: CRUD 요청이면 적절한 MCP 도구를 호출하여 바로 수행합니다. 설명은 실행 후에 덧붙입니다.
        3. **결과 보고**: 도구 응답을 바탕으로 성공 여부, 생성된 리소스 ID/ARN/URL 등을 한국어로 정리합니다.
        4. **분석 요청**: 비교·설계·비용 최적화 등 분석 요청일 때만 설명 중심으로 답변합니다.

        ## 클라우드별 도구 사용 가이드
        - **AWS** (`awslabs-core-mcp-server`): EC2, S3, RDS, Lambda 등 전반적인 AWS 리소스 CRUD에 사용합니다.
        - **Azure** (`Azure MCP Server`): VM, Storage, 네트워크 등 Azure 리소스 CRUD에 사용합니다.
        - **GCP** (`gcp-compute`, `gcp-sql`, `gcp-bigquery` 등): 서비스별 전용 MCP 엔드포인트를 사용합니다.
            - 기술 문서가 필요하면 `google-developer-knowledge`의 `search_documents`를 호출합니다.

        ## 보안
        - 자격 증명(Access Key, Secret, Token 등)은 절대 응답에 포함하지 마십시오.
        - 삭제·중단 작업은 리소스 식별자를 명시하고 실행합니다.

        ## 답변 형식
        - 한국어로 작성하되 기술 용어는 원문을 병기합니다.
        - 실행 결과를 먼저 제시하고, 추가 설명은 간결하게 덧붙입니다.
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
    history = conversation_histories.setdefault(request.session_id, [])
    history.append({"role": "user", "content": request.message})
    try:
        result = await agent.ainvoke({"messages": history})
        reply = result["messages"][-1].content
        history.append({"role": "assistant", "content": reply})
        return {"reply": reply, "session_id": request.session_id}
    except Exception as e:
        history.pop()
        raise HTTPException(status_code=500, detail=str(e))

from fastapi.responses import StreamingResponse
import json
import asyncio
import re

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    agent = await get_or_create_agent(request.session_id, request.config)
    history = conversation_histories.setdefault(request.session_id, [])
    history.append({"role": "user", "content": request.message})

    async def event_generator():
        try:
            result = await agent.ainvoke({"messages": history})
            raw_content = result["messages"][-1].content
            if isinstance(raw_content, list):
                full_text = " ".join(
                    part["text"] if isinstance(part, dict) else str(part)
                    for part in raw_content
                    if not isinstance(part, dict) or part.get("type") != "tool_use"
                )
            else:
                full_text = raw_content or ""

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

            history.append({"role": "assistant", "content": response_content})
            yield json.dumps({"type": "done"}) + "\n"

        except Exception as e:
            history.pop()
            logger.exception(f"Agent error for session {request.session_id}: {e}")
            yield json.dumps({"type": "error", "error": str(e)}) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")

@app.post("/clear")
async def clear_session(request: Dict[str, str] = Body(...)):
    session_id = request.get("session_id", "default")
    if session_id in agents:
        del agents[session_id]
    if session_id in conversation_histories:
        del conversation_histories[session_id]
    logger.info(f"Cleared session: {session_id}")
    return {"status": "cleared", "session_id": session_id}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)
