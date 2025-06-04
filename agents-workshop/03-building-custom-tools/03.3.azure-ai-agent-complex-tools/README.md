## 📝 Workshop Tasks

> For each workshop task, you can either use one of agent apps created in previous modules (console applications) or more advanced sample from [on-behalf-of UI Application built with gradio](../../../gradio_app/main.py)

### Task 1: 🌦️ Connect to a Weather API with OpenApiTool

**Goal:** Use the `OpenApiTool` to connect your agent to a weather API, so it can answer questions about the weather.

#### Steps:
1. **Review the sample code:**
   - See the [Semantic Kernel sample](https://github.com/microsoft/semantic-kernel/blob/main/python/samples/getting_started_with_agents/azure_ai_agent/step6_azure_ai_agent_openapi.py) for how to use `OpenApiTool`.
   - Use code from previous exercises
2. **Add the OpenApiTool to your agent:**
   - Import and configure the tool with the weather API's OpenAPI/Swagger spec.
   - Register the tool when creating your agent.
3. **Test your agent:**
   - Ask your agent questions like "What's the weather in London?"
   - The agent should call the weather API and return real data!

### Task 2: 🌦️ Connect to a Azure Weather API by building a plugin

While using OpenAPI may yield quick results, in general agents do better with well defined tools.

**Goal:** Use GitHub Copilot Agent mode to create a plugin based on [Azure Maps Weather API spec](https://github.com/Azure/azure-rest-api-specs/blob/main/specification/maps/data-plane/Microsoft.Maps/Weather/preview/1.0/weather.json)

#### Steps:
1. **Work with copilot to build a plugin:**
   - See the [Semantic Kernel sample](https://github.com/microsoft/semantic-kernel/blob/4f0bf163b29e797839ddc6281e196bb4ea2ce837/python/samples/getting_started_with_agents/azure_ai_agent/step2_azure_ai_agent_plugin.py) for how to build plugins.
   - Use code from previous exercises
   - Use `AZURE_MAPS_CLIENT_ID` from deployed resources.
   - Use JWT to authenticate with Azure service - Scope: `https://atlas.microsoft.com/.default` 
2. **Add the Weather plugin to your agent:**
   - Import and configure the plugin.
   - Register the plugin when creating your agent.
3. **Test your agent:**
   - Ask your agent questions like "What's the weather in London?"
   - The agent should call the weather API and return real data!

# Task 3
