from typing import Any, AsyncIterator, Dict

from autogen_agentchat.agents import AssistantAgent, CodeExecutorAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import SelectorGroupChat

from .base import build_code_executor, build_model_client, stream_team


async def jarvis_stream(message: str, llm_config: dict) -> AsyncIterator[Dict[str, Any]]:
    model_client = build_model_client(llm_config)
    code_executor = build_code_executor()

    python_coder = AssistantAgent(
        name="PythonCoder",
        model_client=model_client,
        system_message=(
            "You are an expert Python engineer. Write efficient, idiomatic Python code. "
            "Handle all edge cases and follow PEP 8 conventions."
        ),
        description="Writes expert-level Python code.",
    )

    cpp_coder = AssistantAgent(
        name="CppCoder",
        model_client=model_client,
        system_message=(
            "You are an expert C++ engineer. Write performant, modern C++17/20 code. "
            "Handle memory management and edge cases correctly."
        ),
        description="Writes expert-level C++ code.",
    )

    general_coder = AssistantAgent(
        name="Coder",
        model_client=model_client,
        system_message=(
            "You are a polyglot software engineer proficient in all major languages. "
            "Choose the best language for each task and write complete solutions."
        ),
        description="Writes code in any programming language.",
    )

    critic = AssistantAgent(
        name="Critic",
        model_client=model_client,
        system_message=(
            "Analyse all code produced by the team. Identify bugs, missing edge cases, "
            "and performance issues. Guide agents to improve their solutions."
        ),
        description="Reviews code quality and correctness.",
    )

    cto = AssistantAgent(
        name="CTO",
        model_client=model_client,
        system_message=(
            "You are the Chief Technical Officer. Oversee all work, "
            "ensure architectural soundness, and give final approval on solutions. "
            "When the task is fully complete, say TERMINATE."
        ),
        description="Provides technical leadership and final approval.",
    )

    advisor = AssistantAgent(
        name="Advisor",
        model_client=model_client,
        system_message=(
            "You are a wise senior advisor. Offer strategic guidance when the team is stuck. "
            "Provide concise, actionable recommendations."
        ),
        description="Gives strategic advice when the team is uncertain.",
    )

    friend = AssistantAgent(
        name="Friend",
        model_client=model_client,
        system_message=(
            "You are a friendly conversationalist. Engage naturally on any topic, "
            "provide encouragement, and keep conversations light and helpful."
        ),
        description="Handles casual conversation and general questions.",
    )

    aggregator = AssistantAgent(
        name="Aggregator",
        model_client=model_client,
        system_message=(
            "Collect all contributions from the team and synthesise a clear, "
            "complete final response for the user."
        ),
        description="Synthesises all agent outputs into a final answer.",
    )

    executor = CodeExecutorAgent(
        name="Executor",
        code_executor=code_executor,
        description="Executes code and reports results.",
    )

    termination = TextMentionTermination("TERMINATE") | MaxMessageTermination(50)
    team = SelectorGroupChat(
        participants=[python_coder, cpp_coder, general_coder, critic, cto, advisor, friend, aggregator, executor],
        model_client=model_client,
        termination_condition=termination,
    )

    async for msg in stream_team(team, message):
        yield msg
