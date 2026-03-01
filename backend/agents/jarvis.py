import queue

import autogen

from .base import CapturingGroupChatManager


def run_jarvis(message: str, llm_config: dict, capture_queue: queue.Queue) -> None:
    python_coder = autogen.AssistantAgent(
        name="PythonCoder",
        llm_config=llm_config,
        system_message=(
            "You are an expert Python engineer. Write efficient, idiomatic Python code. "
            "Handle all edge cases and follow PEP 8 conventions."
        ),
        description="Writes expert-level Python code.",
    )

    cpp_coder = autogen.AssistantAgent(
        name="CppCoder",
        llm_config=llm_config,
        system_message=(
            "You are an expert C++ engineer. Write performant, modern C++17/20 code. "
            "Handle memory management and edge cases correctly."
        ),
        description="Writes expert-level C++ code.",
    )

    general_coder = autogen.AssistantAgent(
        name="Coder",
        llm_config=llm_config,
        system_message=(
            "You are a polyglot software engineer proficient in all major languages. "
            "Choose the best language for each task and write complete solutions."
        ),
        description="Writes code in any programming language.",
    )

    critic = autogen.AssistantAgent(
        name="Critic",
        llm_config=llm_config,
        system_message=(
            "Analyse all code produced by the team. Identify bugs, missing edge cases, "
            "and performance issues. Guide agents to improve their solutions."
        ),
        description="Reviews code quality and correctness.",
    )

    cto = autogen.AssistantAgent(
        name="CTO",
        llm_config=llm_config,
        system_message=(
            "You are the Chief Technical Officer. Oversee all work, "
            "ensure architectural soundness, and give final approval on solutions."
        ),
        description="Provides technical leadership and final approval.",
    )

    advisor = autogen.AssistantAgent(
        name="Advisor",
        llm_config=llm_config,
        system_message=(
            "You are a wise senior advisor. Offer strategic guidance when the team is stuck. "
            "Provide concise, actionable recommendations."
        ),
        description="Gives strategic advice when the team is uncertain.",
    )

    friend = autogen.AssistantAgent(
        name="Friend",
        llm_config=llm_config,
        system_message=(
            "You are a friendly conversationalist. Engage naturally on any topic, "
            "provide encouragement, and keep conversations light and helpful."
        ),
        description="Handles casual conversation and general questions.",
    )

    aggregator = autogen.AssistantAgent(
        name="Aggregator",
        llm_config=llm_config,
        system_message=(
            "Collect all contributions from the team and synthesise a clear, "
            "complete final response for the user."
        ),
        description="Synthesises all agent outputs into a final answer.",
    )

    jarvis = autogen.UserProxyAgent(
        name="Jarvis",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=15,
        is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
        code_execution_config={"work_dir": "backend/workspace", "use_docker": False},
        system_message=(
            "Reply TERMINATE if the task has been fully solved. "
            "Otherwise reply CONTINUE with the reason the task is not yet done."
        ),
    )

    groupchat = autogen.GroupChat(
        agents=[jarvis, python_coder, cpp_coder, general_coder, critic, cto, advisor, friend, aggregator],
        messages=[],
        max_round=50,
        speaker_selection_method="auto",
        allow_repeat_speaker=False,
    )

    manager = CapturingGroupChatManager(
        capture_queue=capture_queue,
        groupchat=groupchat,
        llm_config=llm_config,
    )

    jarvis.initiate_chat(manager, message=message)
