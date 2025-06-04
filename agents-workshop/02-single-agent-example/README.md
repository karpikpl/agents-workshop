# 02 - Single Agent Example

- 🐍 Walkthrough of creating an agent using Python SDK.
- 🛠️ Introduction to built-in tools and integrations (e.g., AI search, Bing grounding).

---

## 🚀 Available SDKs for Building Agents

When building AI agents on Azure, you can choose from several SDKs depending on your use case and integration needs:

### 🤖 **Azure AI Inference SDK (Foundry)**
- Official SDK for interacting with Azure AI Foundry services.
- Provides access to advanced inference capabilities, including prompt orchestration, tool calling, and agentic workflows.
- ⭐ Recommended for production scenarios and when leveraging Azure AI Foundry features.

### 💡 **Azure OpenAI SDK**
- Direct access to Azure-hosted OpenAI models (e.g., GPT-4, GPT-3.5).
- Useful for prompt-based LLM scenarios, completions, chat, and embeddings.
- 📚 [Docs: Azure OpenAI Python SDK](https://learn.microsoft.com/en-us/azure/ai-services/openai/quickstart?tabs=command-line&pivots=programming-language-python)

### 🧠 **Semantic Kernel SDK**
- Open-source orchestration SDK for building agentic and tool-using AI applications.
- Supports plugins, memory, planning, and integration with multiple LLM providers (including Azure OpenAI).
- 📚 [Docs: Semantic Kernel](https://github.com/microsoft/semantic-kernel)

### 🧰 **Other SDKs and Tools**
- **LangChain**: 🦜 Framework for building LLM-powered applications with tool and memory support. Integrates with Azure OpenAI.
- **Gradio**: 🎛️ For building interactive web UIs for your agents.
- **Azure Cognitive Search SDK**: 🔎 For integrating search capabilities into your agent workflows.

> 💡 **Tip:** Choose the SDK that best matches your workflow and integration requirements. For most Azure agentic scenarios, start with the Azure AI Inference SDK or Semantic Kernel.

> 🏆 **Recommendation:** Use Semantic Kernel SDK for the best developer experience.

## Workshop Task 1

### 🤓 Creating a Simple Chat Completion Agent

In this task, you'll create your first AI agent using the **Semantic Kernel SDK** directly with Azure OpenAI:

- 📁 **Directory**: [semantic-kernel-agent](./semantic-kernel-agent/)
- 🎯 **Goal**: Build a conversational agent using Azure OpenAI and Semantic Kernel
- 🔑 **Key Concepts**: 
  - Setting up Azure OpenAI connection
  - Configuring and initializing Semantic Kernel
  - Creating a ChatCompletionAgent
  - Managing conversation state with ChatHistoryAgentThread

This task provides a foundation for understanding how agents work before moving to more complex scenarios with Azure AI Foundry integration.

Follow the instructions in 👉[semantic-kernel-agent/README.md](./semantic-kernel-agent/README.md) to get started.

## Workshop Task 2

### 🤖 Creating an Azure AI Agent with AI Foundry

In this task, you'll create an agent using **Azure AI Foundry** and the Azure AI Agent SDK:

- 📁 **Directory**: [azure-ai-agent](./azure-ai-agent/)
- 🎯 **Goal**: Build and deploy a conversational agent using Azure AI Foundry
- 🔑 **Key Concepts**: 
  - Connecting to Azure AI Foundry with AIProjectClient
  - Creating and configuring an Azure AI Agent
  - Managing conversation state with AzureAIAgentThread
  - Exploring agent customization options

This task demonstrates how to leverage Azure's managed agent service to create, deploy, and interact with AI agents in a production-ready environment.

Follow the instructions in 👉[azure-ai-agent/README.md](./azure-ai-agent/README.md) to get started.
