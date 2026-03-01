import queue
import threading
from typing import Optional

import autogen


class CapturingGroupChatManager(autogen.GroupChatManager):
    def __init__(self, capture_queue: queue.Queue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._capture_queue = capture_queue

    def receive(self, message, sender, request_reply=None, silent=False):
        if not silent and self._capture_queue:
            content = message if isinstance(message, str) else message.get("content", "")
            if content and content.strip():
                self._capture_queue.put({
                    "type": "agent_message",
                    "sender": getattr(sender, "name", "unknown"),
                    "content": content,
                })
        return super().receive(message, sender, request_reply, silent)


class CapturingUserProxy(autogen.UserProxyAgent):
    def __init__(self, capture_queue: queue.Queue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._capture_queue = capture_queue

    def receive(self, message, sender, request_reply=None, silent=False):
        if not silent and self._capture_queue:
            content = message if isinstance(message, str) else message.get("content", "")
            if content and content.strip():
                self._capture_queue.put({
                    "type": "agent_message",
                    "sender": getattr(sender, "name", "unknown"),
                    "content": content,
                })
        return super().receive(message, sender, request_reply, silent)


class CapturingAssistant(autogen.AssistantAgent):
    def __init__(self, capture_queue: queue.Queue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._capture_queue = capture_queue

    def receive(self, message, sender, request_reply=None, silent=False):
        if not silent and self._capture_queue:
            content = message if isinstance(message, str) else message.get("content", "")
            if content and content.strip():
                self._capture_queue.put({
                    "type": "agent_message",
                    "sender": getattr(sender, "name", "unknown"),
                    "content": content,
                })
        return super().receive(message, sender, request_reply, silent)


class AgentRunner:
    def __init__(self, mode: str, llm_config: dict):
        self.mode = mode
        self.llm_config = llm_config
        self.capture_queue: queue.Queue = queue.Queue()
        self._thread: Optional[threading.Thread] = None

    def start(self, message: str) -> None:
        self._thread = threading.Thread(
            target=self._execute,
            args=(message,),
            daemon=True,
        )
        self._thread.start()

    def _execute(self, message: str) -> None:
        try:
            from .pair_coder import run_pair_coder
            from .coding_team import run_coding_team
            from .jarvis import run_jarvis
            from .research_team import run_research_team

            runners = {
                "pair_coder": run_pair_coder,
                "coding_team": run_coding_team,
                "jarvis": run_jarvis,
                "research": run_research_team,
            }

            runner_fn = runners.get(self.mode, run_pair_coder)
            runner_fn(message, self.llm_config, self.capture_queue)
        except Exception as exc:
            self.capture_queue.put({"type": "error", "content": str(exc)})
        finally:
            self.capture_queue.put({"type": "done"})

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()
