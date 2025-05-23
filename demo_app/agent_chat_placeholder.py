from chat_with_agent_base import ChatWithAgentBase

class AgentChatPlaceholder(ChatWithAgentBase):
    """
    Placeholder for the AgentChat class.
    This is used to avoid circular imports in the demo_app module.
    """

    def __init__(self):
        super().__init__()

    def _get_agents(self, tool_logger=None):
        """
        Placeholder implementation that returns an empty dict.
        """
        return {'MainAgent': DummyAgent()}

    async def agent_chat(
        self,
        user_request: str,
        thread,
        agent_name: str = "MainAgent",
        on_stream_start=None,
        on_stream_done=None,
        file_input=None,
    ):
        """
        Placeholder async generator for agent chat.
        """
        yield (f"{agent_name} to 🧑", f"[Placeholder] Agent chat not implemented. Cannot answer about: \n>{user_request}", thread, agent_name)

class DummyAgent:
    """
    Dummy agent class for testing. Implements async iterator invoke_stream.
    """
    def __init__(self, name="DummyAgent"):
        self.name = name

    class DummyResponse:
        def __init__(self, content):
            self.content = type("Content", (), {"content": content})()

    async def invoke_stream(self, messages, thread=None):
        # Simulate streaming by yielding a few dummy responses
        yield self.DummyResponse(f"[Dummy response] for: {messages}")