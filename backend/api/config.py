from typing import List

import httpx
from fastapi import APIRouter

from ..core.schemas import AgentModeInfo, HealthResponse, LLMConfig
from ..core.settings import settings

router = APIRouter(prefix="/api/config", tags=["config"])

AGENT_MODES: List[AgentModeInfo] = [
    AgentModeInfo(
        id="pair_coder",
        name="Pair Coder",
        description="A two-agent setup with a CTO and an Executor. Best for focused coding tasks.",
        agents=["CTO", "Executor"],
        icon="code",
    ),
    AgentModeInfo(
        id="coding_team",
        name="Coding Team",
        description="A six-agent team covering planning, engineering, science, execution, and critique.",
        agents=["Admin", "Planner", "Engineer", "Scientist", "Executor", "Critic"],
        icon="users",
    ),
    AgentModeInfo(
        id="jarvis",
        name="Jarvis",
        description="A comprehensive nine-agent assistant for coding, conversation, and strategic advice.",
        agents=["Jarvis", "PythonCoder", "CppCoder", "Coder", "Critic", "CTO", "Advisor", "Friend", "Aggregator"],
        icon="cpu",
    ),
    AgentModeInfo(
        id="research",
        name="Research Team",
        description="A research-focused team with dedicated roles for investigation, analysis, writing, and fact-checking.",
        agents=["Admin", "Researcher", "Analyst", "Writer", "Executor", "FactChecker"],
        icon="search",
    ),
]


@router.get("/modes", response_model=List[AgentModeInfo])
def get_modes():
    return AGENT_MODES


@router.get("/llm", response_model=LLMConfig)
def get_llm_config():
    return LLMConfig(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        timeout=settings.llm_timeout,
    )


@router.get("/health", response_model=HealthResponse)
async def health_check():
    reachable = False
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.llm_base_url}/models")
            reachable = resp.status_code < 500
    except Exception:
        reachable = False

    return HealthResponse(
        status="ok",
        version="1.0.0",
        llm_reachable=reachable,
        llm_base_url=settings.llm_base_url,
    )
