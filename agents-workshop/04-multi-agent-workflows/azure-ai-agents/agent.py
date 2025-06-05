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
from otel_setup import setup_otel
from dotenv import load_dotenv
from kernel_factory import KernelFactory

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


async def create_update_agent_definition(
    agent_name: str,
    agent_instructions: str,
    client: AIProjectClient,
    agent_id: str | None = None,
    agents: list[AzureAIAgent] = [],
) -> AzureAIAgent:

    if not agent_id:
        endpoint = os.environ.get("AZURE_AI_FOUNDRY_CONNECTION_STRING")
        deployment_name = os.environ.get("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")
        api_version = os.environ.get("AZURE_OPENAI_API_VERSION", None)

        ai_agent_settings = AzureAIAgentSettings(
            endpoint=endpoint,
            model_deployment_name=deployment_name,
            api_version=api_version,
        )

        # Create an agent on the Azure AI agent service
        agent_definition = await client.agents.create_agent(
            model=ai_agent_settings.model_deployment_name,
            name=agent_name,
            instructions=agent_instructions,
            tools=agents
        )
    else:
        # get the agent
        agent_definition = await client.agents.get_agent(agent_id)

        # update the agent definition with the new file
        agent_definition = await client.agents.update_agent(
            agent_id=agent_id,
            model=agent_definition.model,
            name=agent_definition.name,
            instructions=agent_definition.instructions,
            tools=agents
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
    )

    return agent


# Example agent logic (replace with your own)
def main():
    asyncio.run(main_async())


async def main_async():
    logger = logging.getLogger("workshop.agent")
    logger.info("Semantic Kernel agent with telemetry started.")


    client, creds = create_project_client()
    agent = await create_update_agent_definition(
        agent_name="Main Agent", agent_instructions="You're a helpful agent, handle user query using tools available.", client=client
    )
    thread = AzureAIAgentThread(client=client)

    try:
        user_input = "Ask the user how they are doing today and offer to help with anything. Suggest working with a file (type 'file' to upload a file)."
        print("Welcome! (type 'exit' to exit. type 'file' to upload a file.)")
        try:
            while user_input.lower() != "exit":
                async for agent_response in agent.invoke(
                    messages=user_input,
                    thread=thread,
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
