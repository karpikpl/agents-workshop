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

from otel_setup import setup_otel
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Set up OpenTelemetry (logging, tracing, metrics)
setup_otel()

def create_project_client() -> tuple[AIProjectClient, DefaultAzureCredential]:
    """Create an AIProjectClient instance."""

    # TODO: implement 
    return client,creds

async def create_agent(
    agent_name: str, agent_instructions: str, client: AIProjectClient
) -> AzureAIAgent:
   
    return agent


# Example agent logic (replace with your own)
def main():
    asyncio.run(main_async())


async def main_async():
    logger = logging.getLogger("semantic_kernel.agent")
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
                async for plan_response in agent.invoke(messages=user_input, thread=thread):
                    print(f"Agent: {plan_response}")
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
