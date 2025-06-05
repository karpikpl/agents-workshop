# 04 - Multi-Agent Workflows

Multi-agent workflows enable complex scenarios where multiple agents collaborate, delegate, or route tasks among themselves. Orchestration is the process of coordinating these agents to solve problems that are too complex for a single agent.

## Orchestration Options

There are several approaches to orchestrating multi-agent systems:

- **Router Agent**: A central agent that receives user input and routes questions or tasks to specialized sub-agents based on intent or topic.
- **Agent as Tool**: Agents can expose their capabilities as tools, allowing other agents to invoke them as needed.
- **Task Decomposition**: An orchestrator agent can break down a complex task into subtasks and assign them to different agents.
- **Collaborative Planning**: Multiple agents can plan together, sharing context and results to achieve a common goal.

## Semantic Kernel Orchestration

Semantic Kernel provides flexible orchestration patterns for multi-agent systems. You can compose agents, route requests, and manage agent collaboration using the SDK.

For a hands-on example, see the official Semantic Kernel sample:
- [Multi-Agent Orchestration Sample (Python)](https://github.com/microsoft/semantic-kernel/blob/main/python/samples/getting_started_with_agents/multi_agent_orchestration/README.md)

This sample demonstrates:
- Creating multiple agents with different skills
- Routing user queries to the appropriate agent
- Composing agents for collaborative workflows

## Upcoming Azure AI Agent Service Capabilities

Azure AI Agent Service is evolving to support advanced orchestration, including:
- Built-in agent routing and delegation
- Native support for agent-to-agent communication
- Enhanced monitoring and management for multi-agent systems

Stay tuned for updates as these features become generally available.
