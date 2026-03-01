import queue

import autogen

from .base import CapturingGroupChatManager


def run_coding_team(message: str, llm_config: dict, capture_queue: queue.Queue) -> None:
    admin = autogen.UserProxyAgent(
        name="Admin",
        system_message=(
            "You are the human admin. Approve plans and review deliverables. "
            "Provide clear feedback to the team."
        ),
        code_execution_config=False,
        human_input_mode="NEVER",
    )

    planner = autogen.AssistantAgent(
        name="Planner",
        llm_config=llm_config,
        system_message=(
            "You are a senior technical planner. Design step-by-step execution plans. "
            "Clearly mark which steps require engineering and which require scientific analysis. "
            "Revise your plan based on feedback from the admin and critic."
        ),
        description="Creates and revises the overall execution plan.",
    )

    engineer = autogen.AssistantAgent(
        name="Engineer",
        llm_config=llm_config,
        system_message=(
            "You are a senior software engineer. Implement plans with clean, production-ready code. "
            "Fix errors automatically when execution fails. "
            "Never write incomplete code blocks or ask others to modify your code."
        ),
        description="Writes and fixes code to implement the plan.",
    )

    scientist = autogen.AssistantAgent(
        name="Scientist",
        llm_config=llm_config,
        system_message=(
            "You are a data scientist. Analyse results, categorise outputs, and provide insights. "
            "You do not write code."
        ),
        description="Analyses data and provides scientific insights without writing code.",
    )

    executor = autogen.UserProxyAgent(
        name="Executor",
        system_message="Execute code written by the Engineer and report results accurately.",
        human_input_mode="NEVER",
        code_execution_config={
            "last_n_messages": 3,
            "work_dir": "backend/workspace",
            "use_docker": False,
        },
    )

    critic = autogen.AssistantAgent(
        name="Critic",
        llm_config=llm_config,
        system_message=(
            "Critically review all plans, code, and factual claims from the team. "
            "Ensure solutions are correct, complete, and include verifiable sources where applicable."
        ),
        description="Reviews all team outputs and enforces quality standards.",
    )

    groupchat = autogen.GroupChat(
        agents=[admin, planner, engineer, scientist, executor, critic],
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
