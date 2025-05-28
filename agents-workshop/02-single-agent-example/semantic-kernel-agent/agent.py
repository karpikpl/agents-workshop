"""
Agent implementation using Semantic Kernel with telemetry enabled.
Application Insights connection string can be added via environment variable: APPLICATIONINSIGHTS_CONNECTION_STRING
"""

import asyncio
from datetime import date
import logging
import os
from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai.open_ai import (
    AzureChatCompletion,
)
from semantic_kernel.connectors.ai.open_ai import (
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.functions import KernelArguments
from otel_setup import setup_otel
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Set up OpenTelemetry (logging, tracing, metrics)
setup_otel()

# Example: Initialize Semantic Kernel
kernel = Kernel()

def create_agent(agent_name: str, agent_instructions: str):
    """Create a Semantic Kernel agent."""
    # Example: Create a simple agent with a function
    kernel = Kernel()
    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    deployment_name = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME")
    api_version = os.environ.get("AZURE_OPENAI_API_VERSION", None)
    model_name = os.environ.get("AZURE_OPENAI_MODEL_NAME")

    kernel.add_service(
        AzureChatCompletion(
            service_id=agent_name,
            deployment_name=deployment_name,
            endpoint=endpoint,
            api_version=api_version,
        )
    )
    agent = ChatCompletionAgent(
        kernel=kernel,
        name=agent_name,
        instructions=agent_instructions,
        arguments=KernelArguments(
            OpenAIChatPromptExecutionSettings(
                # response_format=<TBD>,
                temperature=0.2,
                stream=False,
                model=model_name,
            )
        ),
    )
    return agent


def main():
    asyncio.run(main_async())


async def main_async():
    logger = logging.getLogger("semantic_kernel.agent")
    logger.info("Semantic Kernel agent with telemetry started.")

    agent_name = "MyAgent"
    agent_instructions = (
        f"Today is {date.today().strftime('%Y-%m-%d')}. You are a helpful assistant."
    )

    agent = create_agent(agent_name, agent_instructions)
    thread = ChatHistoryAgentThread()

    user_input = (
        "Ask the user how they are doing today and offer to help with anything."
    )
    print("Welcome! (type 'exit' to exit.)")
    try:
        while user_input.lower() != "exit":
            async for agent_response in agent.invoke(messages=user_input, thread=thread):
                print(f"Agent: {agent_response}")
            user_input = input("You: ")
            if not user_input.strip():
                continue
    except KeyboardInterrupt:
        print("\nExiting. Goodbye!")


if __name__ == "__main__":
    main()
