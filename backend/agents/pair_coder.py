from typing import Any, AsyncIterator, Dict

from autogen_agentchat.agents import AssistantAgent, CodeExecutorAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat

from .base import build_code_executor, build_model_client, stream_team


async def pair_coder_stream(message: str, llm_config: dict) -> AsyncIterator[Dict[str, Any]]:
    model_client = build_model_client(llm_config)
    code_executor = build_code_executor()

    cto = AssistantAgent(
        name="CTO",
        model_client=model_client,
        system_message=(
            "You are a Chief Technical Officer and expert software engineer. "
            "Write clean, efficient, production-ready code in any language. "
            "Handle all edge cases and provide complete, runnable solutions. "
            "When the task is complete, end your final message with TERMINATE."
        ),
    )

    executor = CodeExecutorAgent(
        name="Executor",
        code_executor=code_executor,
    )

    termination = TextMentionTermination("TERMINATE") | MaxMessageTermination(20)
    team = RoundRobinGroupChat(
        participants=[cto, executor],
        termination_condition=termination,
    )

    async for msg in stream_team(team, message):
        yield msg
