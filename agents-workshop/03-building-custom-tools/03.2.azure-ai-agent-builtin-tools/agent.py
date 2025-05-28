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
from azure.ai.agents.models import CodeInterpreterTool, FilePurpose
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.functions import KernelArguments
from semantic_kernel.contents.file_reference_content import FileReferenceContent
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

async def create_update_agent_definition(
    agent_name: str, agent_instructions: str, client: AIProjectClient, agent_id: str|None=None, path_to_file: str|None=None) ->  tuple[AzureAIAgent, CodeInterpreterTool]:

    code_interpreter = CodeInterpreterTool()

    if path_to_file:
        csv_file_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), path_to_file
        )
        file = await client.agents.files.upload_and_poll(
            file_path=csv_file_path,
            purpose=FilePurpose.AGENTS,
        )
        code_interpreter.add_file(file.id)

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
            tools=code_interpreter.definitions,
            tool_resources=code_interpreter.resources
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
            tools=code_interpreter.definitions,
            tool_resources=code_interpreter.resources
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

    return agent, code_interpreter


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
    agent, code_interpreter = await create_update_agent_definition(agent_name=agent_name, agent_instructions=agent_instructions, client=client)
    thread = AzureAIAgentThread(client=client)

    try:
        user_input = (
            "Ask the user how they are doing today and offer to help with anything. Suggest working with a file (type 'file' to upload a file)."
        )
        print("Welcome! (type 'exit' to exit. type 'file' to upload a file.)")
        try:
            while user_input.lower() != "exit":
                async for agent_response in agent.invoke(
                    messages=user_input, 
                    thread=thread, 
                    tools=[code_interpreter],
                    on_intermediate_message=lambda agent_response: print(f"Intermediate response: {agent_response}"),
                ):
                    print(f"Agent: {agent_response}")
                    for item in agent_response.items:
                        if isinstance(item, FileReferenceContent):
                            await client.agents.files.save(file_id=item.file_id, file_name=f"downloaded__{item.file_id}.png")
                            print(f"Downloaded file: {item.file_id} saved as downloaded_file.png")
                user_input = input("You: ")

                if user_input.lower() == "file":
                    agent, code_interpreter = await create_update_agent_definition(agent_name, agent_instructions, client, agent.id, "resources/organizations-100000.csv")
                    user_input= "Analyze the uploaded file and provide insights."

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
