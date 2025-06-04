# 🔧 03 - Building Custom Tools

This advanced section introduces you to **tool calling** - one of the most powerful features of Azure AI agents. You'll learn how to enhance your agents with both built-in Azure tools and your own custom-built tools.

## 🎯 Learning Objectives

- Understand the concept of tool calling and its benefits
- Implement simple custom tools using Semantic Kernel plugins
- Utilize built-in tools like Code Interpreter to work with data
- Connect your agent to external services with OpenAPI tools
- **Stretch goal** - Configure authentication for tools using On-Behalf-Of (OBO) flow
- **Stretch goal** - Create complex custom tools for specific services like Stack Overflow or Azure DevOps


## 🔌 Tool Calling Overview

**Tool calling** allows your AI agent to interact with external systems and perform actions beyond simple text generation. With tools, your agent can:

- Access real-time data and information
- Control external services and applications
- Retrieve or modify data in external systems
- Perform complex calculations or data manipulations

### How Tool Calling Works

1. The AI agent recognizes when a tool needs to be called based on user input
2. It formats the appropriate parameters for the tool
3. The system executes the tool with those parameters
4. The results are returned to the agent, which incorporates them into its response

## 🧰 Azure AI Service Built-in Tools

Azure provides several ready-to-use tools that you can integrate with your agent:

| Tool | Purpose | Documentation |
|------|---------|---------------|
| **Grounding with Bing Search** | Search the web for current information | [Docs](https://learn.microsoft.com/en-gb/azure/ai-services/agents/how-to/tools/bing-grounding) |
| **Azure AI Search** | Connect to your data sources via AI Search | [Docs](https://learn.microsoft.com/en-gb/azure/ai-services/agents/how-to/tools/azure-ai-search?tabs=azurecli) |
| **File Search** | Use built-in vector store to agument agents with knowledge | [Docs](https://learn.microsoft.com/en-gb/azure/ai-services/agents/how-to/tools/file-search) |
| **Code Interpreter** | Let agents write and run Python code in sandbox environment | [Docs](https://learn.microsoft.com/en-gb/azure/ai-services/agents/how-to/tools/code-interpreter) |
| **OpenAPI Tools** | Connect agents to OpenAPI specified external APIs | [Docs](https://learn.microsoft.com/en-gb/azure/ai-services/agents/how-to/tools/openapi-spec) |
| **Azure Functions** | Execute custom code | [Docs](https://learn.microsoft.com/en-gb/azure/ai-services/agents/how-to/tools/azure-functions) |

## 🛠️ Building Custom Tools

Create your own tools to extend your agent's capabilities to specific services and data sources.

### Custom Tool Components

1. **Function Definition**: Specify name, description, and parameters
2. **Implementation**: Write the code that performs the action
3. **Authentication**: Set up how the tool authenticates with external services
4. **Registration**: Register the tool with your agent

## Workshop Exercises

> **💡Hint** For each workshop task, you can either use one of agent apps created in previous modules (console applications) or more advanced sample from [on-behalf-of UI Application built with gradio](../../gradio_app/main.py)

### Exercise 1: Simple Custom Tools
Learn how to create and integrate basic custom tools using Semantic Kernel plugins.
- 📁 **Directory**: [03.1.azure-ai-agent-simple-tools](./03.1.azure-ai-agent-simple-tools/)
- 🎯 **Goal**: Create and register simple plugins/tools with your agent

 Go to 👉[README.md](./03.1.azure-ai-agent-simple-tools/README.md).

### Exercise 2: Code Interpreter
Work with the Code Interpreter built-in tool to analyze data and generate visualizations.
- 📁 **Directory**: [03.2.azure-ai-agent-builtin-tools](./03.2.azure-ai-agent-builtin-tools/)
- 🎯 **Goal**: Use the Code Interpreter to analyze CSV data and generate insights

 Go to 👉[README.md](./03.2.azure-ai-agent-builtin-tools/README.md).

### Exercise 3: OpenAPI Tools
Connect your agent to external services using OpenAPI specifications.
- 📁 **Directory**: [03.3.azure-ai-agent-openapi-tools](./03.3.azure-ai-agent-complex-tools/)
- 🎯 **Goal**: Integrate external APIs with your agent using OpenAPI tools

 Go to 👉[README.md](./03.3.azure-ai-agent-complex-tools/README.md).

### Stretch Goals

These advanced topics are provided for learners who want to go further:

- **Stack Overflow Tool**: Build a tool to search and retrieve programming answers
- **Azure DevOps Tool**: Create a tool to interact with Azure DevOps work items and repositories
- **On-Behalf-Of Authentication**: Implement secure authentication for tools accessing protected resources

## 🔒 Authentication for Tools

### On-Behalf-Of (OBO) Authentication Flow

The OBO pattern allows your agent to access external resources using the end user's credentials:

1. User authenticates to your application
2. Your application requests a token for the desired resource
3. The token is used to authenticate tool calls

![OBO Flow](https://learn.microsoft.com/en-us/azure/active-directory/develop/media/v2-oauth2-on-behalf-of-flow/protocols-oauth-on-behalf-of-flow.png)

### Workshop Exercise 4: Implementing OBO Authentication

Learn how to set up OBO authentication for your custom tools to securely access user resources.

## 🚀 Getting Started

1. Complete the previous workshop sections first
2. Ensure you have all necessary Azure resources provisioned
3. Open the example code for each exercise
4. Follow the step-by-step instructions in each subdirectory

## 📚 Additional Resources

- [Azure OpenAI Functions Calling](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/function-calling)
- [Semantic Kernel Plugin Development](https://learn.microsoft.com/en-us/semantic-kernel/agents/plugins/)
- [Microsoft Authentication Library (MSAL)](https://learn.microsoft.com/en-us/azure/active-directory/develop/msal-overview)

---

Ready to supercharge your agent with powerful tools? Let's begin! 🤖✨
