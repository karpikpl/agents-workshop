from abc import ABC, abstractmethod
import logging
from logging_tools.tool_log_base import ToolLogBase
from azure.identity.aio import DefaultAzureCredential, get_bearer_token_provider
from semantic_kernel.agents import Agent, AgentThread

from typing import AsyncGenerator, Callable, Optional

from utils import FileInput


class ChatWithAgentBase(ABC):
    """Abstract base class chatting with agents."""

    def __init__(
        self,
        tool_logger: ToolLogBase | None = None,
        credential: DefaultAzureCredential = None,
    ):
        self.tool_logger = tool_logger
        agents = self._get_agents(tool_logger=tool_logger)
        self.agents: dict[str, Agent] = agents

        self.on_stream_start: Optional[Callable[[str], Callable[[str], None]]] = None
        self.on_stream_done: Optional[Callable[[str, str], None]] = None
        self.credential = credential or DefaultAzureCredential(
            exclude_shared_token_cache_credential=True
        )

    @staticmethod
    def get_thread(thread_id: str | None) -> AgentThread:
        pass

    async def _get_bearer_token(
        self, scope: str = "https://cognitiveservices.azure.com/.default"
    ) -> str:
        provider = get_bearer_token_provider(self.credential, scope)
        logging.info(
            f"Using Azure AD token provider with scope: {scope}"
        )
        token = await provider()
        return token

    def format_agent_message(self, agent, message):
        return f"**{agent}**: {message}"

    async def _get_agent_response_with_streaming(
        self,
        agent_name: str,
        task: str,
        thread: AgentThread,
        audience: str = "🧑",
    ) -> str:
        agent = self.agents[agent_name]

        # start streaming
        if self.on_stream_start:
            on_stream_chunk = self.on_stream_start(
                self.format_agent_message(
                    # 📝{PLANNER_NAME}
                    f"🤖{agent_name} to {audience}",
                    "Thinking...",
                )
            )
        else:

            def on_stream_chunk(x):
                pass

            on_stream_chunk = on_stream_chunk

        partial_response = self.format_agent_message(
            f"🤖{agent_name} to {audience}\n", ""
        )

        async for response in agent.invoke_stream(messages=task, thread=thread):
            if response.content:
                partial_response += response.content.content
                on_stream_chunk(partial_response)

        # call the on_stream_done callback if provided
        if self.on_stream_done:
            self.on_stream_done(agent_name, partial_response)

        # at this point, the response is complete
        return partial_response

    @abstractmethod
    def _get_agents(
        self, tool_logger: ToolLogBase | None = None
    ) -> dict[str, Agent]:
        """Get the agents for the chat completion."""
        pass

    @abstractmethod
    async def agent_chat(
        self,
        user_request: str,
        thread: AgentThread,
        agent_name: str = "Planner",
        on_stream_start: Optional[Callable[[str], Callable[[str], None]]] = None,
        on_stream_done: Optional[Callable[[str, str], None]] = None,
        file_input: FileInput | None = None,
    ) -> AsyncGenerator[tuple[str, str, AgentThread, str], None]:
        """Chat with the agent."""
        pass
