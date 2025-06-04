# Semantic Kernel Agent Workshop

This workshop guides you through **Task 1: Creating a Chat Completion Agent** using [Semantic Kernel](https://github.com/microsoft/semantic-kernel).

---

## 🚦 Task 1: Create a Chat Completion Agent

You will:

1. **Set up environment variables** for your Azure OpenAI deployment.
2. **Initialize Semantic Kernel** and configure telemetry.
3. **Create a Chat Completion Agent** using `AzureChatCompletion` and `ChatCompletionAgent`.
4. **Interact with your agent** in a chat loop.

### Steps

- Open `agent.py`.
- Fill in the agent creation logic using your Azure OpenAI endpoint, deployment, and model.
- Run the script and chat with your agent in the terminal.

---

## ⚠️ Notice: AI Foundry Not Used in This Setup

This example uses **Semantic Kernel** with the Azure OpenAI Service directly and does **not** leverage Azure AI Foundry.  
**Why?**  
- Semantic Kernel currently integrates with Azure OpenAI endpoints for chat completion, not with the AI Foundry orchestration layer.
- This approach demonstrates direct use of Azure OpenAI for agent creation and chat, which is suitable for many scenarios and aligns with Semantic Kernel's current capabilities.

## 📝 Task 1 Summary

In this task, you created a simple agent using Semantic Kernel's chat completion capabilities:

1. **Environment Setup**:
   - Configured Azure OpenAI endpoint, deployment, and model name via environment variables
   - Set up OpenTelemetry for capturing logs and metrics

2. **Agent Implementation**:
   - Initialized a Semantic Kernel instance
   - Created an Azure Chat Completion service and connected it to the kernel
   - Configured a ChatCompletionAgent with personalized instructions and settings
   - Implemented a chat loop for interactive conversations with the agent

3. **Key Concepts Learned**:
   - Direct integration with Azure OpenAI using Semantic Kernel
   - Agent conversation state management with ChatHistoryAgentThread
   - Streaming responses from the language model
   - Agent customization through instructions and execution settings

This implementation demonstrates the simplicity and power of creating AI agents with Semantic Kernel, leveraging Azure OpenAI directly without requiring the AI Foundry orchestration layer.

## Next step

Explore `Azure AI Agent` support in Semantic Kernel in the next task  Go to 👉[README.md](../azure-ai-agent/README.md).