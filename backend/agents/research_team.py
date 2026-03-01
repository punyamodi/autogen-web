from typing import Any, AsyncIterator, Dict

from autogen_agentchat.agents import AssistantAgent, CodeExecutorAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import SelectorGroupChat

from .base import build_code_executor, build_model_client, stream_team


async def research_team_stream(message: str, llm_config: dict) -> AsyncIterator[Dict[str, Any]]:
    model_client = build_model_client(llm_config)
    code_executor = build_code_executor()

    researcher = AssistantAgent(
        name="Researcher",
        model_client=model_client,
        system_message=(
            "You are a thorough research specialist. Gather information, identify key concepts, "
            "and propose research approaches. Always cite sources and note confidence levels."
        ),
        description="Gathers and organises research information.",
    )

    analyst = AssistantAgent(
        name="Analyst",
        model_client=model_client,
        system_message=(
            "You are a data analyst and critical thinker. Evaluate research findings, "
            "identify patterns and gaps, and draw well-supported conclusions."
        ),
        description="Analyses research data and draws conclusions.",
    )

    writer = AssistantAgent(
        name="Writer",
        model_client=model_client,
        system_message=(
            "You are a technical writer. Transform research and analysis into clear, "
            "well-structured documents. Use plain language and logical organisation. "
            "When the final report is ready, say TERMINATE."
        ),
        description="Produces clear written deliverables from research findings.",
    )

    executor = CodeExecutorAgent(
        name="Executor",
        code_executor=code_executor,
        description="Executes any code needed for data analysis.",
    )

    fact_checker = AssistantAgent(
        name="FactChecker",
        model_client=model_client,
        system_message=(
            "Verify all factual claims made by the team. Flag unsupported assertions, "
            "request source URLs, and ensure accuracy before the final report is produced."
        ),
        description="Verifies factual accuracy of all research outputs.",
    )

    termination = TextMentionTermination("TERMINATE") | MaxMessageTermination(30)
    team = SelectorGroupChat(
        participants=[researcher, analyst, writer, executor, fact_checker],
        model_client=model_client,
        termination_condition=termination,
    )

    async for msg in stream_team(team, message):
        yield msg
