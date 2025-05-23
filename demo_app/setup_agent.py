import json
import logging
import os
import subprocess
import sys

from azure.ai.projects import AIProjectClient
from azure.identity import AzureDeveloperCliCredential
from azure.ai.projects.models import CodeInterpreterTool

# from opentelemetry import trace
# from azure.monitor.opentelemetry import configure_azure_monitor

from azure.ai.projects.models import (
    FunctionTool,
    ConnectionType,
    AzureAISearchTool,
    ToolSet,
)
from dotenv import load_dotenv
from rich.logging import RichHandler

from chat_with_main_agent import (
    PLANNER_NAME,
    PLANNER_INSTRUCTIONS,
    SCI_ENGINEER_NAME,
    SCI_ENGINEER_INSTRUCTIONS,
    RESEARCHER_NAME,
    RESEARCHER_INSTRUCTIONS,
    ILLUSTRATOR_NAME,
    ILLUSTRATOR_INSTRUCTIONS,
    ARCHITECT_NAME,
    ARCHITECT_INSTRUCTIONS,
)

from engineer_plugin import EngineerPlugin
from research_plugin import ResearchPlugin, AzureVMsPlugin
from logging_tools import simple_log

engineer_plugin = EngineerPlugin(ui_log=simple_log)
research_plugin = ResearchPlugin(ui_log=simple_log)
azure_vms_plugin = AzureVMsPlugin(ui_log=simple_log)

# functions = FunctionTool(functions=[
#     EngineerPlugin.calculate_SCI,
#     EngineerPlugin.total_SCI,
#     EngineerPlugin.call_research_agent,
#     EngineerPlugin.get_grid_intensity,
# ])

logging.basicConfig(
    level=logging.WARNING,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)
logger = logging.getLogger("setup_agent")
logger.setLevel(logging.INFO)


def set_azd_variable(name, value):
    """Set azd variable using azd cli"""
    logger.info(f"Setting azd variable {name} to {value}")
    result = subprocess.run(
        f"azd env set {name} {value}", shell=True, capture_output=True, text=True
    )
    if result.returncode != 0:
        raise Exception("Error setting azd variable")
    logger.info(f"Set azd variable {name} to {value}")


def load_azd_env():
    """Get path to current azd env file and load file using python-dotenv"""
    result = subprocess.run(
        "azd env list -o json", shell=True, capture_output=True, text=True
    )
    if result.returncode != 0:
        raise Exception("Error loading azd env")
    env_json = json.loads(result.stdout)
    env_file_path = None
    for entry in env_json:
        if entry["IsDefault"]:
            env_file_path = entry["DotEnvPath"]
    if not env_file_path:
        raise Exception("No default azd env file found")
    logger.info(f"Loading azd env from {env_file_path}")
    load_dotenv(env_file_path, override=True)


def add_update_agent(
    project_client: AIProjectClient,
    agent_name: str,
    agents: dict[str, str],
    openai_model: str,
    instructions: str,
    temperature: float,
    tool_set: ToolSet = None,
):
    if agent_name in agents:
        try:
            agent = project_client.agents.get_agent(agents[agent_name])
            logger.info(f"Agent ID: {agents[agent_name]}")

            # update agent if it exists
            agent = project_client.agents.update_agent(
                agent_id=agent.id,
                # assistant_id=agent.id,
                model=openai_model,
                instructions=instructions,
                temperature=temperature,
                toolset=tool_set,
            )
        except Exception as e:
            logger.error(f"Error getting agent: {e}")
    else:
        logger.info("Creating agent")
        agent = project_client.agents.create_agent(
            model=openai_model,
            name=agent_name,
            instructions=instructions,
            temperature=temperature,
            toolset=tool_set,
        )


def setup_agents(hubConectionString: str):
    azure_credential = AzureDeveloperCliCredential(
        tenant_id=os.environ["AZURE_TENANT_ID"], process_timeout=60
    )
    project_client = AIProjectClient.from_connection_string(
        credential=azure_credential,
        conn_str=hubConectionString,
        # logging_enable = True
    )

    if os.environ.get("DEBUG", "false") == "true":
        project_client.telemetry.enable(destination=sys.stdout)

    openai_model = os.environ.get("AZURE_OPENAI_AGENTS_MODEL", "gpt-4o")

    conn_list = project_client.connections.list()
    ai_search_connection_id = ""
    for conn in conn_list:
        if conn.connection_type == ConnectionType.AZURE_AI_SEARCH:
            ai_search_connection_id = conn.id
            logger.info(f"AI Search Connection Name: {conn.name}")
            break
    # Initialize agent AI search tool and add the search index connection id
    logger.info(f"AI Search Connection ID: {ai_search_connection_id}")

    ## AI search tool is not included because it does not work with managed identity as of 3/4/2025
    ai_search = AzureAISearchTool(
        # TODO: fix index name when Search tool is working again.
        index_connection_id=ai_search_connection_id,
        index_name=os.environ["AZURE_PATTERNS_SEARCH_INDEX"],
    )

    # find all agents
    agentsList = project_client.agents.list_agents()
    agents: dict[str, str] = {}

    for agent in agentsList.data:
        logger.info(f"Agent: {agent.name} with id {agent.id}")
        agents[agent.name] = agent.id

    add_update_agent(
        project_client,
        PLANNER_NAME,
        agents,
        openai_model,
        PLANNER_INSTRUCTIONS,
        0.2,
    )

    architect_tools = ToolSet()
    architect_tools.add(FunctionTool(functions=[azure_vms_plugin.query_azure_db]))

    add_update_agent(
        project_client=project_client,
        agent_name=ARCHITECT_NAME,
        agents=agents,
        openai_model=openai_model,
        instructions=ARCHITECT_INSTRUCTIONS,
        temperature=0.3,
        tool_set=architect_tools,
    )

    illustrator_tools = ToolSet()
    illustrator_tools.add(CodeInterpreterTool())

    add_update_agent(
        project_client,
        agent_name=ILLUSTRATOR_NAME,
        agents=agents,
        openai_model=openai_model,
        instructions=ILLUSTRATOR_INSTRUCTIONS,
        temperature=1.0,
        tool_set=illustrator_tools,
    )

    research_tools = ToolSet()
    research_tools.add(ai_search)
    research_tools.add(
        FunctionTool(
            functions=[
                research_plugin.retrieve_green_software_patterns_from_user_index,
                azure_vms_plugin.query_azure_db,
            ]
        )
    )

    add_update_agent(
        project_client,
        agent_name=RESEARCHER_NAME,
        agents=agents,
        openai_model=openai_model,
        instructions=RESEARCHER_INSTRUCTIONS,
        temperature=0.3,
        tool_set=research_tools,
    )

    sci_engineer_tools = ToolSet()
    sci_engineer_tools.add(CodeInterpreterTool())
    sci_engineer_tools.add(
        FunctionTool(
            functions=[
                engineer_plugin.calculate_SCI,
                azure_vms_plugin.query_azure_db,
            ]
        )
    )

    add_update_agent(
        project_client,
        agent_name=SCI_ENGINEER_NAME,
        agents=agents,
        openai_model=openai_model,
        instructions=SCI_ENGINEER_INSTRUCTIONS,
        temperature=0.3,
        tool_set=sci_engineer_tools,
    )

    logger.info("Agent setup complete")


if __name__ == "__main__":
    load_azd_env()

    is_debug = bool(os.environ.get("DEBUG", "false"))

    if is_debug:
        # Acquire the logger for this client library. Use 'azure' to affect both
        # 'azure.core` and `azure.ai.inference' libraries.
        logger = logging.getLogger("azure")

        # Set the desired logging level. logging.INFO or logging.DEBUG are good options.
        logger.setLevel(logging.DEBUG)

        # Direct logging output to stdout:
        handler = logging.StreamHandler(stream=sys.stdout)
        # Or direct logging output to a file:
        # handler = logging.FileHandler(filename="sample.log")
        logger.addHandler(handler)

    hubConectionString = os.environ["AZURE_AI_FOUNDRY_CONNECTION_STRING"]

    logger.info("Setting up agent")
    try:
        setup_agents(hubConectionString)
    except Exception as e:
        logger.error(f"Error setting up agent: {e}")
        logger.warning("403 Error may require making Azure OpenAI resource public.")
