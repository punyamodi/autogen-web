from typing import Any, AsyncIterator, Dict

from autogen_agentchat.agents import AssistantAgent, CodeExecutorAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import SelectorGroupChat

from .base import build_code_executor, build_model_client, stream_team


async def coding_team_stream(message: str, llm_config: dict) -> AsyncIterator[Dict[str, Any]]:
    model_client = build_model_client(llm_config)
    code_executor = build_code_executor()

    planner = AssistantAgent(
        name="Planner",
        model_client=model_client,
        system_message=(
            "You are a senior technical planner. Design step-by-step execution plans. "
            "Clearly mark which steps require engineering and which require scientific analysis. "
            "Revise your plan based on feedback from the team."
        ),
        description="Creates and revises the overall execution plan.",
    )

    engineer = AssistantAgent(
        name="Engineer",
        model_client=model_client,
        system_message=(
            "You are a senior software engineer. Implement plans with clean, production-ready code. "
            "Fix errors automatically when execution fails. "
            "Never write incomplete code blocks. When all tasks are done, say TERMINATE."
        ),
        description="Writes and fixes code to implement the plan.",
    )

    scientist = AssistantAgent(
        name="Scientist",
        model_client=model_client,
        system_message=(
            "You are a data scientist. Analyse results, categorise outputs, and provide insights. "
            "You do not write code."
        ),
        description="Analyses data and provides scientific insights without writing code.",
    )

    executor = CodeExecutorAgent(
        name="Executor",
        code_executor=code_executor,
        description="Executes code written by the Engineer and reports results.",
    )

    critic = AssistantAgent(
        name="Critic",
        model_client=model_client,
        system_message=(
            "Critically review all plans, code, and factual claims from the team. "
            "Ensure solutions are correct, complete, and include verifiable sources where applicable."
        ),
        description="Reviews all team outputs and enforces quality standards.",
    )

    termination = TextMentionTermination("TERMINATE") | MaxMessageTermination(30)
    team = SelectorGroupChat(
        participants=[planner, engineer, scientist, executor, critic],
        model_client=model_client,
        termination_condition=termination,
    )

    async for msg in stream_team(team, message):
        yield msg
