import asyncio
import json
import logging
from semantic_kernel.filters import AutoFunctionInvocationContext, FilterTypes
from semantic_kernel import Kernel
from azure.ai.agents.models import Agent

from otel_setup import get_span

logger = logging.getLogger(f"workshop.agent.{__name__}")
logger.setLevel(logging.INFO)  # Ensure logger level allows INFO logs
logger.propagate = True  # Ensure propagation is enabled (default)


class KernelFactory:
    @staticmethod
    async def create_kernel(agent: Agent) -> Kernel:
        with get_span("create_kernel") as span:
            span.set_attribute("agent_id", agent.id)

            kernel = Kernel()

            return kernel
