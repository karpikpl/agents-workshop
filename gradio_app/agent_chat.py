import json
import logging
from typing import Dict, List
import uuid
from gradio import ChatMessage
import gradio as gr
from urllib.parse import urlparse, parse_qs, unquote_plus
import io
from PIL import Image
import numpy as np

from semantic_kernel import Kernel
from semantic_kernel.agents import (
    AzureAIAgent,
    AzureAIAgentThread,
)
from azure.ai.projects.aio import AIProjectClient
from agent_factory import create_agent, create_project_client
from otel_setup import get_span
from semantic_kernel.filters import AutoFunctionInvocationContext, FilterTypes

from semantic_kernel.contents import (
    ChatMessageContent,
    FunctionCallContent,
    FunctionResultContent,
    StreamingAnnotationContent,
    StreamingChatMessageContent,
    StreamingFileReferenceContent,
    StreamingTextContent,
    TextContent,
    ImageContent,
)

from azure.ai.agents.models import (
    # FileSearchTool,
    FilePurpose,
)

from kernel_factory import KernelFactory
from semantic_kernel.functions import FunctionResult

app_logger = logging.getLogger("workshop.agent")


class EnterpriseChat:
    def __init__(
        self,
        client: AIProjectClient,
        agent: AzureAIAgent,
        thread: AzureAIAgentThread,
        kernel: Kernel,
    ):
        self.thread = thread
        self.agent = agent
        self.client = client
        self.kernel = kernel
        self.stack_token = ""
        self.kernel.add_filter(
            FilterTypes.AUTO_FUNCTION_INVOCATION, self.auth_function_filter
        )

    async def auth_function_filter(self, context: AutoFunctionInvocationContext, next):
        """A filter that will be called for auto-invoked functions."""
        with get_span("auth_function_filter"):
            function_name = context.function.name
            plugin_name = context.function.plugin_name
            if plugin_name == "StackOverflowTool":
                if self.stack_token:
                    context.arguments["kwargs"]["token"] = self.stack_token
                else:
                    context.function_result = FunctionResult(
                        function=context.function_result.function,
                        value="""Please authenticate with Stack Overflow to use this tool.
                        Visit: http://localhost:8001/auth/stackoverflow""",
                    )
                    context.terminate = True
                    return

            # Execute the function
            try:
                await next(context)
            except Exception as e:
                app_logger.error(
                    f"Error in function {plugin_name}.{function_name}: {str(e)}"
                )
                raise

    def set_stack_token(self, stack_token: str) -> None:
        """
        Set the Stack Overflow authentication tokens.
        This is used to authenticate the Stack Overflow tool.
        """
        self.stack_token = stack_token

    async def reset_thread(self) -> None:
        """
        Reset the thread by creating a new one.
        This is useful for clearing the conversation history.
        """
        new_thread = await self.client.agents.threads.create()
        self.thread = AzureAIAgentThread(client=self.client, thread_id=new_thread.id)

    async def azure_enterprise_chat(
        self, user_message: dict, history: List[ChatMessage]
    ):
        """
        Accumulates partial function arguments into ChatMessage['content'], sets the
        corresponding tool bubble status from "pending" to "done" on completion,
        and also handles non-function calls like bing_grounding or file_search by appending a
        "pending" bubble. Then it moves them to "done" once tool calls complete.

        This function returns a list of ChatMessage objects directly (no dict conversion).
        Your Gradio Chatbot should be type="messages" to handle them properly.
        """
        # Convert existing history from dict to ChatMessage
        conversation = []
        for msg_dict in history:
            conversation.append(convert_dict_to_chatmessage(msg_dict))

        # # Immediately yield two outputs to clear the textbox
        # yield conversation

        # Mappings for partial function calls
        in_progress_tools: Dict[str, ChatMessage] = {}

        # Titles for tool bubbles
        function_titles = {
            "fetch_weather": "☁️ fetching weather",
            "fetch_datetime": "🕒 fetching datetime",
            "fetch_stock_price": "📈 fetching financial info",
            "send_email": "✉️ sending mail",
            "file_search": "📄 searching docs",
            "bing_grounding": "🔍 searching bing",
        }

        def get_function_title(fn_name: str) -> str:
            return function_titles.get(fn_name, f"🛠 calling {fn_name}")

        def upsert_tool_call(tcall: FunctionCallContent | FunctionResultContent):
            """
            1) Check the call type
            2) If "function", gather partial name/args
            3) If "bing_grounding" or "file_search", show a pending bubble
            """
            # TODO how to get type?
            t_type = tcall.content_type
            function_name = tcall.function_name or tcall.name
            call_id = tcall.call_id or tcall.id

            # --- BING GROUNDING ---
            if function_name == "bing_grounding":
                # check for previous bing grounding calls
                response_metadata = tcall.arguments.get("response_metadata", {})
                pending_msg = None

                # check if any pending call is for bing grounding even if call_id is None
                if not call_id:
                    for cid, msg_obj in in_progress_tools.items():
                        if msg_obj.metadata.get("log") == "bing_grounding":
                            pending_msg = msg_obj
                            break

                if pending_msg and response_metadata:
                    # If we already have a pending call, just update the content
                    pending_msg.metadata["log"] = json.dumps(response_metadata)
                    pending_msg.metadata["status"] = "done"
                    # remove it from in_progress_tools
                    in_progress_tools.pop(
                        pending_msg.metadata.get("id", "tool-noid"), None
                    )
                    return

                request_url = tcall.arguments.get("requesturl", "")
                # if not request_url.strip():
                #     return

                query_str = extract_bing_query(request_url or "")
                # if not query_str.strip():
                #     return

                if pending_msg:
                    # If we already have a pending call, just update the content
                    pending_msg.content = query_str
                    return

                msg_obj = ChatMessage(
                    role="assistant",
                    content=query_str,
                    metadata={
                        "title": get_function_title("bing_grounding"),
                        "status": "pending",
                        "log": "bing_grounding",
                        "id": f"tool-{call_id}" if call_id else "tool-noid",
                    },
                )
                conversation.append(msg_obj)
                if call_id:
                    in_progress_tools[call_id] = msg_obj
                return

            # --- FILE SEARCH ---
            elif function_name == "file_search":
                msg_obj = ChatMessage(
                    role="assistant",
                    content="searching docs...",
                    metadata={
                        "title": get_function_title("file_search"),
                        "status": "pending",
                        "id": f"tool-{call_id}" if call_id else "tool-noid",
                    },
                )
                conversation.append(msg_obj)
                if call_id:
                    in_progress_tools[call_id] = msg_obj
                return

            elif t_type == "function_result":
                in_progress_tools[call_id].metadata["status"] = "done"
                in_progress_tools.pop(call_id)
                return
            # --- NON-FUNCTION CALLS ---
            elif t_type != "function_call":
                return

            # --- FUNCTION CALL PARTIAL-ARGS ---
            # name_chunk = tcall.name
            # arg_chunk = tcall.arguments
            msg_obj = ChatMessage(
                role="assistant",
                content=tcall.arguments or "",
                metadata={
                    "title": get_function_title(tcall.function_name),
                    "status": "pending",
                    "id": f"tool-{call_id}",
                },
            )
            conversation.append(msg_obj)
            in_progress_tools[call_id] = msg_obj

        async def handle_streaming_intermediate_steps(step: ChatMessageContent):
            for item in step.items or []:
                if isinstance(item, FunctionResultContent):
                    app_logger.info(
                        f"Function Result:> {item.result} for function: {item.name}"
                    )
                    upsert_tool_call(item)
                elif isinstance(item, FunctionCallContent):
                    app_logger.info(
                        f"Function Call:> {item.name} with arguments: {item.arguments}"
                    )
                    upsert_tool_call(item)
                else:
                    # most likely code returned from a tool
                    # TODO: handle code snippets

                    app_logger.warning(f"Unknown item in intermediate steps: {item}")

        message = ChatMessageContent(role="user", content=user_message["text"] or "")

        if user_message["files"]:
            file_path: str
            for file_path in user_message["files"]:
                uploaded = await self.client.agents.files.upload_and_poll(
                    file_path=file_path, purpose=FilePurpose.AGENTS
                )
                # todo = specify tools for the attachment
                # attachment = MessageAttachment(file_id=uploaded.id, tools=CodeInterpreterTool().definitions + FileSearchTool().definitions)

                if file_path.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
                    message.items.append(ImageContent.from_image_file(path=file_path))

                # Update tools with file attachment
                #  tools_definitions,tool_resources = await setup_tools(client=self.client, file_attachment_path=file_path)

                # get thread
                agent_thread = await self.client.agents.threads.get(
                    thread_id=self.thread.id,
                )

                if (
                    not agent_thread.tool_resources
                    or not agent_thread.tool_resources.code_interpreter
                ):
                    break

                # Update files
                agent_thread.tool_resources.code_interpreter.file_ids = (
                    agent_thread.tool_resources.code_interpreter.file_ids
                    + [uploaded.id]
                )

                # Probably a bug in the SDK, so we need to update the tool resources manually
                if (
                    agent_thread.tool_resources
                    and agent_thread.tool_resources.azure_ai_search
                    and len(agent_thread.tool_resources.azure_ai_search.index_list) == 0
                ):
                    agent_thread.tool_resources.azure_ai_search = None

                # Update the thread with the new tool resources
                agent_thread = await self.client.agents.threads.update(
                    thread_id=self.thread.id,
                    tool_resources=agent_thread.tool_resources,
                )
                # update Azure AI Agent Thread
                self.thread = AzureAIAgentThread(
                    client=self.client,
                    thread_id=agent_thread.id,
                    tool_resources=agent_thread.tool_resources,
                )
                break  # only handle the first file for now

        # -- EVENT STREAMING --
        first_chunk = True
        async for response in self.agent.invoke_stream(
            messages=message,
            thread=self.thread,
            on_intermediate_message=handle_streaming_intermediate_steps,
        ):
            if first_chunk:
                print(f"# {response.name}: ", end="", flush=True)
                first_chunk = False
            print(f"{response}", end="", flush=True)
            self.thread = response.thread

            # with project_client.agents.create_stream(
            #     thread_id=thread.id,
            #     assistant_id=agent_id,
            #     event_handler=MyEventHandler()  # the event handler handles console output
            # ) as stream:
            msg_id = uuid.uuid4().hex
            for item in response.items:
                event_type, event_data, *_ = item

                if (
                    not isinstance(item, StreamingTextContent)
                    and not isinstance(item, StreamingFileReferenceContent)
                    and not isinstance(item, StreamingAnnotationContent)
                ):
                    app_logger.warning(f"Unknown item in response: {item}")

                if isinstance(item, FunctionResultContent):
                    # this result is never returned - it's handled in on_intermediate_message
                    app_logger.info(
                        f"Function Result:> {item.result} for function: {item.name}"
                    )
                elif isinstance(item, FunctionCallContent):
                    # this result is never returned - it's handled in on_intermediate_message
                    app_logger.info(
                        f"Function Call:> {item.name} with arguments: {item.arguments}"
                    )
                elif isinstance(item, StreamingAnnotationContent):
                    # Handle streaming annotations
                    if conversation and conversation[-1].role == "assistant":
                        last_msg = conversation[-1]

                    if not last_msg:
                        break

                    if last_msg.content.endswith("】"):
                        start_index = last_msg.content.rfind("【")
                        # replace with markdown link
                        last_msg.content = (
                            last_msg.content[:start_index]
                            + f"【[{item.title}]({item.url})】"
                        )

                elif isinstance(item, StreamingChatMessageContent):
                    # This is never returned
                    if item.items:
                        for msg_item in item.items:
                            if isinstance(msg_item, ChatMessageContent):
                                print(f"Chat Message:> {msg_item.content}")
                            else:
                                print(f"Unknown item in chat message: {msg_item}")
                elif isinstance(item, StreamingFileReferenceContent):
                    # This is never returned
                    # Download the file reference
                    file_info = await self.client.agents.files.get(file_id=item.file_id)
                    app_logger.info(
                        f"Downloading file: {file_info.name} ({file_info.size} bytes)"
                    )
                    file_bytes = bytearray()
                    data = await self.client.agents.files.get_content(
                        file_id=item.file_id
                    )
                    async for byte in data:
                        file_bytes.extend(byte)

                    # Append the file reference to the conversation
                    # Convert bytes to numpy array for gr.Image
                    image = Image.open(io.BytesIO(file_bytes))
                    image_np = np.array(image)
                    conversation.append(
                        ChatMessage(role="assistant", content=gr.Image(image_np))
                    )

                elif isinstance(item, StreamingTextContent):
                    # Handle streaming text content
                    agent_msg = item.text or ""
                    message_id = msg_id

                    # Try to find a matching assistant bubble
                    matching_msg = None
                    for msg in reversed(conversation):
                        if (
                            msg.metadata
                            and msg.metadata.get("id") == message_id
                            and msg.role == "assistant"
                        ):
                            matching_msg = msg
                            break

                    if matching_msg:
                        # Append newly streamed text
                        matching_msg.content += agent_msg
                    else:
                        # Append to last assistant or create new
                        if (
                            not conversation
                            or conversation[-1].role != "assistant"
                            or (
                                conversation[-1].metadata
                                and str(
                                    conversation[-1].metadata.get("id", "")
                                ).startswith("tool-")
                            )
                            or not isinstance(conversation[-1].content, str)
                        ):
                            conversation.append(
                                ChatMessage(role="assistant", content=agent_msg)
                            )
                        else:
                            matching_msg = conversation[-1]
                            matching_msg.content += agent_msg

                    yield conversation
                elif isinstance(item, TextContent):
                    # Handle regular text content
                    if item.text:
                        conversation.append(
                            ChatMessage(role="assistant", content=item.text)
                        )
                        yield conversation
                else:
                    print(f"{item}")

                # Remove any None items that might have been appended
                conversation = [m for m in conversation if m is not None]

        yield conversation


# Implement the Main Chat Functions
def extract_bing_query(request_url: str) -> str:
    """
    Extract the query string from something like:
      https://api.bing.microsoft.com/v7.0/search?q="latest news about Microsoft January 2025"
    Returns: latest news about Microsoft January 2025
    """
    parsed = urlparse(request_url)
    qs = parse_qs(parsed.query)
    q = qs.get("q", [""])[0]
    return unquote_plus(q) if q else request_url


def convert_dict_to_chatmessage(msg: dict) -> ChatMessage:
    """
    Convert a legacy dict-based message to a gr.ChatMessage.
    Uses the 'metadata' sub-dict if present.
    """
    return ChatMessage(
        role=msg["role"], content=msg["content"], metadata=msg.get("metadata", None)
    )


async def create_enterprise_chat(
    agent_name: str, agent_instructions: str
) -> EnterpriseChat:
    """
    Factory function to create an EnterpriseChat instance.
    """
    kernel = KernelFactory.create_kernel()
    client, creds = create_project_client()
    agent = await create_agent(agent_name, agent_instructions, client, kernel)
    agent_thread = await client.agents.threads.create()
    thread = AzureAIAgentThread(client=client, thread_id=agent_thread.id)

    return EnterpriseChat(client, agent, thread, kernel)
