from typing import Any, AsyncIterator, Dict

from autogen_agentchat.agents import AssistantAgent, CodeExecutorAgent
from autogen_agentchat.base import TaskResult
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import SelectorGroupChat
from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor
from autogen_ext.models.openai import OpenAIChatCompletionClient


def build_model_client(llm_config: dict) -> OpenAIChatCompletionClient:
    cfg = llm_config["config_list"][0]
    return OpenAIChatCompletionClient(
        model=cfg["model"],
        base_url=cfg.get("base_url"),
        api_key=cfg.get("api_key", "NULL"),
    )


def build_code_executor(work_dir: str = "backend/workspace") -> LocalCommandLineCodeExecutor:
    import pathlib
    pathlib.Path(work_dir).mkdir(parents=True, exist_ok=True)
    return LocalCommandLineCodeExecutor(work_dir=work_dir)


async def stream_team(team: SelectorGroupChat, task: str) -> AsyncIterator[Dict[str, Any]]:
    async for event in team.run_stream(task=task):
        if isinstance(event, TaskResult):
            return
        sender = getattr(event, "source", None) or getattr(event, "sender", "Agent")
        content = getattr(event, "content", None)
        if content is None:
            continue
        text = content if isinstance(content, str) else str(content)
        if text.strip():
            yield {"type": "agent_message", "sender": sender, "content": text}


async def run_stream(message: str, mode: str, llm_config: dict) -> AsyncIterator[Dict[str, Any]]:
    from .pair_coder import pair_coder_stream
    from .coding_team import coding_team_stream
    from .jarvis import jarvis_stream
    from .research_team import research_team_stream

    runners = {
        "pair_coder": pair_coder_stream,
        "coding_team": coding_team_stream,
        "jarvis": jarvis_stream,
        "research": research_team_stream,
    }

    runner_fn = runners.get(mode, pair_coder_stream)
    async for msg in runner_fn(message, llm_config):
        yield msg
