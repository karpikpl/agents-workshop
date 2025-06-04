# 🤖 Azure AI Agent Workshop

Welcome! This workshop will guide you through creating and interacting with your first Azure AI Agent using the [Azure AI Agents](https://github.com/microsoft/semantic-kernel/blob/main/python/samples/getting_started_with_agents/azure_ai_agent/README.md) library.

---

## 🚦 Prerequisites

- 🐍 Python 3.8+
- ☁️ Azure subscription with access to Azure OpenAI and AI Foundry
- 🛡️ Required environment variables set:
  - `AZURE_AI_FOUNDRY_CONNECTION_STRING`
  - `AZURE_OPENAI_CHAT_DEPLOYMENT_NAME`
  - `AZURE_OPENAI_API_VERSION` (optional)

---

## 1️⃣ Create an AI Project Client

The first step is to create an AI Project Client to connect to Azure AI Foundry.

**📝 Task:**  
Open [`agent.py`](./agent.py) and implement the `create_project_client` function.

```python
def create_project_client() -> tuple[AIProjectClient, DefaultAzureCredential]:
    """Create an AIProjectClient instance."""

    # TODO: implement 
    return client, creds
```

<details>
  <summary>💡 Show solution</summary>

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

## 2️⃣ Create an Azure AI Agent

Next, create an Azure AI Agent using the client.

**📝 Task:**  
Implement the `create_agent` function in [`agent.py`](./agent.py):

```python
async def create_agent(
    agent_name: str, agent_instructions: str, client: AIProjectClient
) -> AzureAIAgent:
    # TODO: implement
    return agent
```

<details>
  <summary>💡 Show solution</summary>

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

## 3️⃣ Interact with the Agent

Finally, implement a chat loop to interact with your agent.

**📝 Task:**  
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
  <summary>💡 Show solution</summary>

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

## Additional Tasks

Looking to go further? Try these experiments to deepen your understanding:

1. **Customize Agent Instructions:**  
   Edit the agent's instructions to give it a specific domain expertise or personality (e.g., "You are a helpful travel assistant" or "You are a witty science tutor"). Observe how this changes the agent's responses.

2. **Switch Model Deployments:**  
   Change the `model_deployment_name` in your agent setup to use a different model available in your Azure AI Foundry. Compare how different models affect the agent's capabilities and style.

3. **Tune Agent Creativity:**  
   Adjust the `top_p` parameter in the agent definition (if supported). Lower values make responses more focused and deterministic; higher values increase creativity and randomness. Try different values and note the differences.
   
   > **💡Hint** look at `client.agents.create_agent`

4. **Explore in Azure AI Foundry:**  
   Visit [🤖 AI Foundry](https://ai.azure.com/) to view, manage, and interact with your agent through the Azure portal UI.

5. **Explore structured outputs:**  
   Experiment with configuring your agent to return structured outputs (such as JSON or specific data formats) by adjusting the prompt or agent settings. This is useful for scenarios where you want the agent to provide data that can be programmatically processed.

   > **💡Hint** look at `client.agents.create_agent`
   
6. **Bonus:**  
   - Add new tools or functions to your agent and see how it handles more complex tasks.
   - Try integrating your agent into a simple web or chat interface.

## 🏁 Summary

You have learned how to:

1. 🔗 Connect to Azure AI Foundry with a project client.
2. 🧑‍💻 Create and configure an Azure AI Agent.
3. 💬 Interact with your agent in a chat loop.

For more details, see the [Azure AI Agents documentation](https://github.com/microsoft/semantic-kernel/blob/main/python/samples/getting_started_with_agents/azure_ai_agent/README.md).

For information how to write prompts see:

- [Open AI Prompt Engineering](https://platform.openai.com/docs/guides/prompt-engineering/prompt-engineering)
- [GPT-4.1 Prompting Guide](https://cookbook.openai.com/examples/gpt4-1_prompting_guide)

---

Happy hacking! 🤖✨