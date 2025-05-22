# Workshop Agenda

## 01 - Introduction to Agentic AI
- Overview of agentic AI and its applications.
- High-level introduction to the Azure AI agent service.
- Discuss the evolution from chatbots to agentic workflows.

## 02 - Single Agent Example
- Walkthrough of creating an agent using Python SDK.
- Introduction to built-in tools and integrations (e.g., AI search, Bing grounding).

## 03 - Building Custom Tools
- Demonstrate building a custom tool for Stack Overflow or Azure DevOps.
- Discuss the on-behalf-of (OBO) authentication workflow.

## 04 - Multi-Agent Workflows
- Introduction to semantic kernel and its applications.
- Example of a router agent for question routing.
- Discuss upcoming orchestration capabilities in Azure AI agent service.

## 05 - Wrap-Up and Next Steps
- Summarize key learnings and takeaways.
- Discuss potential applications and future workshops.

# Prerequisistes 

## Tools

- [Install Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest)
- [Install Azure Developer CLI](https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/install-azd?tabs=winget-windows%2Cbrew-mac%2Cscript-linux&pivots=os-windows)
- [Install UV](https://docs.astral.sh/uv/getting-started/installation/)
  - uv can be used to install Python e.g. `uv python install 3.12`
- Python 3.12
- [OPTIONAL] [VSCode](https://code.visualstudio.com/download)

## Azure

- Azure Subscription with **User Access Management** permission and **Contributor** permission
- On-behalf-of requirement - permission to register applications in Entra Id.