# About

[Azure AI Agents](https://github.com/microsoft/semantic-kernel/blob/main/python/samples/getting_started_with_agents/azure_ai_agent/README.md)

## Creating your first agent

### AI Project Client

First step is to create an AI Project Client which connect to AI Foundry.

Open [agent.py](./agent.py) and add required code.

```python
def create_project_client() -> tuple[AIProjectClient, DefaultAzureCredential]:
    """Create an AIProjectClient instance."""

    # TODO: implement 
    return client,creds
```

<details>
  <summary>Code snippet if stuck</summary>

    ```python
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


### Azure AI Agent

Following Azure AI Agent documentation create AI Agent.

Open [agent.py](./agent.py) and add required code.

```python
async def create_agent(
    agent_name: str, agent_instructions: str, client: AIProjectClient
) -> AzureAIAgent:
    
    return agent
```

<details>
  <summary>Code snippet if stuck</summary>

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

### Call the Agent

Call the agent, by implementing a chat loop

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
  <summary>Code snippet if stuck</summary>

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