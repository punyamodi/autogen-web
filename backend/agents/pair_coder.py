import queue

import autogen

from .base import CapturingUserProxy


def run_pair_coder(message: str, llm_config: dict, capture_queue: queue.Queue) -> None:
    assistant = autogen.AssistantAgent(
        name="CTO",
        llm_config=llm_config,
        system_message=(
            "You are a Chief Technical Officer and expert software engineer. "
            "Write clean, efficient, production-ready code in any language. "
            "Always handle edge cases and provide complete, runnable solutions. "
            "After solving the task reply TERMINATE."
        ),
    )

    executor = CapturingUserProxy(
        capture_queue=capture_queue,
        name="Executor",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=10,
        is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
        code_execution_config={"work_dir": "backend/workspace", "use_docker": False},
        system_message=(
            "Reply TERMINATE if the task has been solved at full satisfaction. "
            "Otherwise reply CONTINUE, or explain why the task is not yet solved."
        ),
    )

    executor.initiate_chat(assistant, message=message)
