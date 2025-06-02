import base64
import logging
import os
import uuid
import streamlit as st
import asyncio
import json
from authlib.integrations.requests_client import OAuth1Session

from azure.identity.aio import DefaultAzureCredential, AzureDeveloperCliCredential
from otel_setup import setup_otel, get_span
from logging_tools.tool_log_base import ToolCall
from chat_with_agent_base import ChatWithAgentBase
from utils import FileInput
from agent_chat_placeholder import AgentChatPlaceholder

st.set_page_config(initial_sidebar_state="collapsed", layout="wide")

from msal import PublicClientApplication

# Initialize MSAL PublicClientApplication
app = PublicClientApplication(
    "3a430c31-eecd-4397-8f64-9ce3daf644b0",
    authority="https://login.microsoftonline.com/c29d6c2b-f765-41b3-b2a2-971a14239dfd",
    client_credential=None
    )

# Function to acquire and use token
def acquire_and_use_token():
    result = None

    # Attempt to get token from cache or acquire interactively
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(["User.Read"], account=accounts[0])
    else:
        result = app.acquire_token_interactive(scopes=["User.Read"], prompt="select_account")

    # Check if token was obtained successfully
    if "access_token" in result:
        st.write("Token acquisition successful!")
        st.write("Access token:", result["access_token"])

    else:
        st.error("Token acquisition failed")
        st.error(result.get("error_description", "No further details"))
    if result and "access_token" in result:
        st.session_state.token = result["access_token"]

if not st.user.is_logged_in:
    if st.button("Log in with Microsoft"):
       acquire_and_use_token()
    st.stop()

if st.button("Log out"):
    st.logout()
st.markdown(f"Welcome! {st.user.name}")

# Sidebar for tool call logs
with st.sidebar:
    st.header("🛠️ Tool Call Log")

@st.cache_resource()
def get_logger():
    setup_otel()
    return (logging.getLogger("azure-ai-agent-demo"))


@st.cache_resource(ttl=3600)
def get_credentials():
    logger.info("Creating credentials object")
    tenant = os.environ.get("AZURE_TENANT_ID")
    if tenant:
        return AzureDeveloperCliCredential(tenant_id=tenant)
    else:
        return DefaultAzureCredential()

logger = get_logger()
credentials = get_credentials()

# --- AGENT SETUP ---
@st.cache_resource(ttl=3600)
def get_chat(_credentials) -> ChatWithAgentBase:
    logger.info("Creating chat object")
    # todo - create a new chat instance

    return AgentChatPlaceholder()


chat = get_chat(credentials)

# generate unique UUID and save thread in session state
if "thread" not in st.session_state:
    st.session_state.thread = chat.get_thread(str(uuid.uuid4()))

if "span" not in st.session_state:
    st.session_state.span = get_span(
        name="azure-ai-agent-demo",
        attributes={"thread_id": str(st.session_state.thread)},
    )
span = st.session_state.span

# --- STREAMLIT UI ---
st.title("💬 Azure AI Agent Demo")

# Initialize tool log in session state
if "tool_log" not in st.session_state:
    st.session_state.tool_log = []

if "history" not in st.session_state:
    st.session_state.history = []

if "file_uploader_key" not in st.session_state:
    st.session_state["file_uploader_key"] = 0

if "current_agent" not in st.session_state:
    st.session_state.current_agent = "Main"

# Add buttons for sample chat messages
st.subheader("Sample Questions")
one, two, three, four = st.columns(4)
if one.button("Tell me about Harry Potter"):
    user_input = "Tell me about Harry Potter"
elif two.button("What makes popcorn pop?"):
    user_input = "What makes popcorn pop?"
elif three.button("How to choose the right paddle board?"):
    user_input = "How to choose the right paddle board?"
elif four.button("Explain the V-scale in climbing"):
    user_input = "Explain the V-scale in climbing"
else:
    user_input = st.chat_input("Type your question for the agents...")

st.markdown(f"Current Agent: **:rainbow[{st.session_state.current_agent}]**")


async def run_agent(
    user_input,
    thread,
    agent_name: str,
    file_input: FileInput = None,
):
    with span:
        if user_input or file_input:
            st.chat_message("user").write(user_input if user_input else "File uploaded")
            st.session_state.history.append(
                ("User", user_input if user_input else "File uploaded")
            )

            # if user mentioned an existign agent using @mention - switch to that agent
            if user_input and "@" in user_input:
                agent_name = user_input.split("@")[1].split(" ")[0]
                if agent_name in chat.agents:
                    st.session_state.current_agent = agent_name
                    st.chat_message("user").write(f"Switching to agent: {agent_name}")
                    st.session_state.history.append(
                        ("User", f"Switching to agent: {agent_name}")
                    )

            with st.spinner("Thinking..."):

                def on_stream_start(message: str):
                    placeholder = st.chat_message("assistant").empty()
                    placeholder.markdown(message)

                    def on_stream_chunk(chunk: str):
                        placeholder.markdown(chunk)

                    return on_stream_chunk

                def on_stream_done(agent: str, message: str):
                    st.session_state.history.append((agent, message))

                async for persona, msg, new_thred, new_agent in chat.agent_chat(
                    user_input,
                    thread,
                    agent_name=agent_name,
                    on_stream_start=on_stream_start,
                    on_stream_done=on_stream_done,
                    file_input=file_input,
                ):
                    st.session_state.thread = new_thred
                    st.session_state.current_agent = new_agent
                    st.session_state.history.append((persona, msg))
                    # Display each message as it arrives
                    if persona == "User":
                        st.chat_message("user").write(msg)
                    else:
                        st.chat_message("assistant").markdown(
                            chat.format_agent_message(persona, msg), unsafe_allow_html=True
                        )


# Display chat history
for agent, msg in st.session_state.history:
    if agent == "User":
        st.chat_message("user").write(msg)
    else:
        with st.chat_message("assistant"):
            st.markdown(chat.format_agent_message(agent, ""), unsafe_allow_html=True)

            def flush_markdown(markdown_lines: list[str]):
                if markdown_lines:
                    st.markdown("\n".join(markdown_lines), unsafe_allow_html=True)
                    markdown_lines.clear()
                return markdown_lines

            if isinstance(msg, str):
                lines = msg.split("\n")
                in_code = False
                code_lines = []
                in_latex = False
                latex_lines = []
                markdown_lines = []
                for line in lines:
                    line_stripped = line.strip()
                    # Multiline code block
                    if line_stripped.startswith("```"):
                        if not in_code:
                            markdown_lines = flush_markdown(markdown_lines)
                            in_code = True
                            code_language = line_stripped[3:].strip() or "python"
                            code_lines = []
                        else:
                            in_code = False
                            st.code("\n".join(code_lines), language=code_language)
                        continue
                    if in_code:
                        code_lines.append(line)
                        continue
                    # Multiline LaTeX block
                    if (
                        line_stripped.startswith("$$")
                        or line_stripped.startswith("\\[")
                        or line_stripped.endswith("$$")
                        or line_stripped.endswith("\\]")
                    ):
                        if not in_latex:
                            markdown_lines = flush_markdown(markdown_lines)
                            in_latex = True
                            latex_lines = []
                        else:
                            in_latex = False
                            st.latex("\n".join(latex_lines))
                        continue
                    if in_latex:
                        latex_lines.append(line)
                        continue
                    # Single-line code
                    if line_stripped.startswith("`") and line_stripped.endswith("`"):
                        markdown_lines = flush_markdown(markdown_lines)
                        st.code(line_stripped[1:-1])
                    # Single-line LaTeX
                    elif line_stripped.startswith("$") and line_stripped.endswith("$"):
                        arkdown_lines = flush_markdown(markdown_lines)
                        st.latex(line_stripped[1:-1])
                    elif (
                        line_stripped.startswith("[")
                        and line_stripped.endswith("]")
                        and line_stripped[1:-1].count("[") == 0
                    ):
                        arkdown_lines = flush_markdown(markdown_lines)
                        st.latex(line_stripped[1:-1])
                    else:
                        markdown_lines.append(line)
                # Output any remaining markdown
                flush_markdown(markdown_lines)


# Display tool call logs
if st.session_state.tool_log:
    for tool_call in st.session_state.tool_log:
        chat.tool_logger.log(tool_call, save=False)

# File upload section
uploaded_file = st.file_uploader(
    "Upload an Image",
    type=["png", "jpg", "jpeg"],
    key=st.session_state["file_uploader_key"],
)

# run task
if user_input and not uploaded_file:
    query = user_input
    user_input = None
    asyncio.run(
        run_agent(
            query,
            thread=st.session_state.thread,
            file_input=None,
            agent_name=st.session_state.current_agent,
        )
    )
    st.rerun()

if uploaded_file:
    query = user_input
    file = uploaded_file
    user_input = None
    uploaded_file = None
    st.session_state["file_uploader_key"] += 1

    # Process the uploaded file
    if file.type in ["image/png", "image/jpeg"]:
        bytes = file.read()
        data_url = f"data:{file.type};base64,{base64.b64encode(bytes).decode('utf-8')}"
        st.success("Image file uploaded successfully!")

        file_upload_tool_call: ToolCall = ToolCall(
            name="File Upload", args=file.name, output=f"Uploaded {file.type} file."
        )
        chat.tool_logger.log(file_upload_tool_call, save=True)

        st.session_state.current_agent = "CloudArchitecture"
        asyncio.run(
            run_agent(
                user_input=query,
                thread=st.session_state.thread,
                agent_name=st.session_state.current_agent,
                file_input=FileInput(data_url_b64=data_url, mime_type=file.type),
            )
        )
        st.rerun()
    else:
        st.error("Unsupported file type. Please upload a PDF or Image.")
