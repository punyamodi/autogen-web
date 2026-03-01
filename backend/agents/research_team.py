import queue

import autogen

from .base import CapturingGroupChatManager


def run_research_team(message: str, llm_config: dict, capture_queue: queue.Queue) -> None:
    admin = autogen.UserProxyAgent(
        name="Admin",
        system_message=(
            "You are the research director. Approve research plans and review final deliverables. "
            "Provide feedback on scope and quality."
        ),
        code_execution_config=False,
        human_input_mode="NEVER",
    )

    researcher = autogen.AssistantAgent(
        name="Researcher",
        llm_config=llm_config,
        system_message=(
            "You are a thorough research specialist. Gather information, identify key concepts, "
            "and propose research approaches. Always cite sources and note confidence levels."
        ),
        description="Gathers and organises research information.",
    )

    analyst = autogen.AssistantAgent(
        name="Analyst",
        llm_config=llm_config,
        system_message=(
            "You are a data analyst and critical thinker. Evaluate research findings, "
            "identify patterns and gaps, and draw well-supported conclusions."
        ),
        description="Analyses research data and draws conclusions.",
    )

    writer = autogen.AssistantAgent(
        name="Writer",
        llm_config=llm_config,
        system_message=(
            "You are a technical writer. Transform research and analysis into clear, "
            "well-structured documents. Use plain language and logical organisation."
        ),
        description="Produces clear written deliverables from research findings.",
    )

    executor = autogen.UserProxyAgent(
        name="Executor",
        system_message="Execute any code needed for data analysis and report results accurately.",
        human_input_mode="NEVER",
        code_execution_config={
            "last_n_messages": 3,
            "work_dir": "backend/workspace",
            "use_docker": False,
        },
    )

    fact_checker = autogen.AssistantAgent(
        name="FactChecker",
        llm_config=llm_config,
        system_message=(
            "Verify all factual claims made by the team. Flag unsupported assertions, "
            "request source URLs, and ensure accuracy before the final report is produced."
        ),
        description="Verifies factual accuracy of all research outputs.",
    )

    groupchat = autogen.GroupChat(
        agents=[admin, researcher, analyst, writer, executor, fact_checker],
        messages=[],
        max_round=20,
        speaker_selection_method="auto",
    )

    manager = CapturingGroupChatManager(
        capture_queue=capture_queue,
        groupchat=groupchat,
        llm_config=llm_config,
    )

    admin.initiate_chat(manager, message=message)
