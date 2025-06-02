"""
Agent implementation using Semantic Kernel with telemetry enabled.
Application Insights connection string can be added via environment variable: APPLICATIONINSIGHTS_CONNECTION_STRING
"""

import asyncio
from datetime import date
import logging
import os
from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient
from semantic_kernel.agents import (
    AzureAIAgent,
    AzureAIAgentThread,
    AzureAIAgentSettings,
)
from semantic_kernel.connectors.ai.prompt_execution_settings import (
    PromptExecutionSettings,
)
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.functions import KernelArguments
from azure.ai.agents.models import (
    BingGroundingTool,
    CodeInterpreterTool,
    FileSearchTool,
)

from otel_setup import setup_otel
from dotenv import load_dotenv
from kernel_factory import KernelFactory

from simple_tool import SimpleTool

# Load environment variables from the .env file
load_dotenv()

# Set up OpenTelemetry (logging, tracing, metrics)
setup_otel()

# Add standard Python console logging handler (text format, not OTEL) only to app logger
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
console_handler.setFormatter(formatter)
app_logger = logging.getLogger("workshop.agent")
app_logger.addHandler(console_handler)


def create_project_client() -> tuple[AIProjectClient, DefaultAzureCredential]:
    """Create an AIProjectClient instance."""

    endpoint = os.environ.get("AZURE_AI_FOUNDRY_CONNECTION_STRING")
    deployment_name = os.environ.get("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")
    api_version = os.environ.get("AZURE_OPENAI_API_VERSION", None)

    ai_agent_settings = AzureAIAgentSettings(
        endpoint=endpoint,
        model_deployment_name=deployment_name,
        api_version=api_version,
    )

    creds = DefaultAzureCredential()
    client = AzureAIAgent.create_client(
        credential=creds,
        endpoint=ai_agent_settings.endpoint,
        api_version=ai_agent_settings.api_version,
    )
    return client, creds


async def create_agent(
    agent_name: str, agent_instructions: str, client: AIProjectClient
) -> AzureAIAgent:
    endpoint = os.environ.get("AZURE_AI_FOUNDRY_CONNECTION_STRING")
    deployment_name = os.environ.get("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")
    api_version = os.environ.get("AZURE_OPENAI_API_VERSION", None)

    ai_agent_settings = AzureAIAgentSettings(
        endpoint=endpoint,
        model_deployment_name=deployment_name,
        api_version=api_version,
    )

    existing_agent = None

    # Find agent by name
    async for existing_agent in client.agents.list_agents():
        if existing_agent.name == agent_name:
            app_logger.info(f"Found existing agent: {existing_agent.name} - {existing_agent.id}")
            break

    bing_connection_id = None
    # get all connections
    async for connection in client.connections.list(
        connection_type="GroundingWithBingSearch"
    ):
        app_logger.info(f"Connection: {connection.name} - {connection.id}")
        bing_connection_id = connection.id

    # async for connection in client.connections.list():
    #     app_logger.info(f"Connection: {connection.name} - {connection.id}")


    bing = BingGroundingTool(connection_id=bing_connection_id, market="en-US", count=10)
    code_interpreter = CodeInterpreterTool()
    file_search = FileSearchTool()

    tools = (
        bing.definitions
        if bing_connection_id
        else [] + code_interpreter.definitions + file_search.definitions
    )

    # Create an agent on the Azure AI agent service
    if existing_agent:
        app_logger.info(f"Using existing agent: {existing_agent.name} - {existing_agent.id}")
        agent_definition = await client.agents.update_agent(
            agent_id=existing_agent.id,
            model=ai_agent_settings.model_deployment_name,
            name=agent_name,
            instructions=agent_instructions,
            tools=tools,
        )
    else:
        app_logger.info(f"Creating new agent: {agent_name}")
        # Create a new agent if it does not exist
        agent_definition = await client.agents.create_agent(
            model=ai_agent_settings.model_deployment_name,
            name=agent_name,
            instructions=agent_instructions,
            tools=tools,
        )

    kernel_settings = PromptExecutionSettings(
        function_choice_behavior=FunctionChoiceBehavior.Auto()
    )

    kernel = await KernelFactory.create_kernel(agent_definition)

    agent = AzureAIAgent(
        arguments=KernelArguments(kernel_settings),
        kernel=kernel,
        client=client,
        definition=agent_definition,
        plugins=[SimpleTool()],
    )
    return agent


# Example agent logic (replace with your own)
def main():
    asyncio.run(main_async())


async def main_async():
    logger = logging.getLogger("workshop.agent")
    logger.info("Semantic Kernel agent with telemetry started.")

    agent_name = "MyAgent"
    agent_instructions = (
        f"Today is {date.today().strftime('%Y-%m-%d')}. You are a helpful assistant."
    )

    client, creds = create_project_client()
    agent = await create_agent(agent_name, agent_instructions, client)
    thread = AzureAIAgentThread(client=client)

    try:
        user_input = (
            "Ask the user how they are doing today and offer to help with anything."
        )
        print("Welcome! (type 'exit' to exit.)")
        try:
            while user_input.lower() != "exit":
                async for agent_response in agent.invoke(
                    messages=user_input, thread=thread
                ):
                    print(f"Agent: {agent_response}")
                user_input = input("You: ")
                if not user_input.strip():
                    continue
        except KeyboardInterrupt:
            print("\nExiting. Goodbye!")
    finally:
        await thread.delete() if thread else None
        await client.agents.delete_agent(agent.id) if agent else None
        await client.close()
        await creds.close()


if __name__ == "__main__":
    main()
