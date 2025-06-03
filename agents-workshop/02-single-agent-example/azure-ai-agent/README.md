# Azure AI Agent Workshop

This workshop will guide you through creating and interacting with your first Azure AI Agent using the [Azure AI Agents](https://github.com/microsoft/semantic-kernel/blob/main/python/samples/getting_started_with_agents/azure_ai_agent/README.md) library.

## Prerequisites

- Python 3.8+
- Azure subscription with access to Azure OpenAI and AI Foundry
- Required environment variables set:
  - `AZURE_AI_FOUNDRY_CONNECTION_STRING`
  - `AZURE_OPENAI_CHAT_DEPLOYMENT_NAME`
  - `AZURE_OPENAI_API_VERSION` (optional)

---

## 1. Create an AI Project Client

The first step is to create an AI Project Client to connect to Azure AI Foundry.

**Task:**  
Open [`agent.py`](./agent.py) and implement the `create_project_client` function.

```python
def create_project_client() -> tuple[AIProjectClient, DefaultAzureCredential]:
    """Create an AIProjectClient instance."""

    # TODO: implement 
    return client, creds
```

<details>
  <summary>Show solution</summary>

  ```python
  import os
  from azure.identity import DefaultAzureCredential
  from azure.ai.agent import AzureAIAgent, AzureAIAgentSettings

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
  ```
</details>

---

## 2. Create an Azure AI Agent

Next, create an Azure AI Agent using the client.

**Task:**  
Implement the `create_agent` function in [`agent.py`](./agent.py):

```python
async def create_agent(
    agent_name: str, agent_instructions: str, client: AIProjectClient
) -> AzureAIAgent:
    # TODO: implement
    return agent
```

<details>
  <summary>Show solution</summary>

  ```python
  """Create a Semantic Kernel agent."""
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
  )

  agent = AzureAIAgent(
      client=client,
      definition=agent_definition,
  )
  ```
</details>

---

## 3. Interact with the Agent

Finally, implement a chat loop to interact with your agent.

**Task:**  
Complete the following code in [`agent.py`](./agent.py):

```python
client, creds = create_project_client()
agent = await create_agent(agent_name, agent_instructions, client)
thread = AzureAIAgentThread(client=client)

try:
    # Add code here
finally:
    await thread.delete() if thread else None
    await client.agents.delete_agent(agent.id) if agent else None
    await client.close()
    await creds.close()
```

<details>
  <summary>Show solution</summary>

  ```python
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
  ```
</details>

---

## Summary

You have learned how to:

1. Connect to Azure AI Foundry with a project client.
2. Create and configure an Azure AI Agent.
3. Interact with your agent in a chat loop.

For more details, see the [Azure AI Agents documentation](https://github.com/microsoft/semantic-kernel/blob/main/python/samples/getting_started_with_agents/azure_ai_agent/README.md).