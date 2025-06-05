from typing import List
import gradio as gr
from agent_chat import EnterpriseChat, create_enterprise_chat


# Global dictionary to store user-specific instances
instances: dict[str, EnterpriseChat] = {}


def get_user(request: gr.Request) -> str:
    if request.username:
        return f"Hello, **{request.username}**!"
    return "Hello, **Guest**!"


async def set_enterprise_chat(request: gr.Request) -> None:

    stackoverflow_token: str = None
    if request and request.request and request.request.session:
        stackoverflow_token = request.request.session.get("stackoverflow_token", None)

    if request.session_hash in instances:
        # If an instance already exists for this session, return it
        chat = instances[request.session_hash]
        chat.set_stack_token(stackoverflow_token)
        return None

    chat = await create_enterprise_chat(
        "Bob",
        f"""
            You are a helpful assistant for enterprise queries.
            The user you're assisting is {request.username}.
            
            ## Tool usage

            ### Bing Search Tool
            Use the Bing Search tool to find information on the web. You can search for company policies, weather forecasts, stock prices, and more.
            Example: prompt:"Who won champions league" should produce a Bing search query 'https://api.bing.microsoft.com/v7.0/search?q=champions league 2025 winner'

            ### WeatherAPI
            Use the WeatherAPI tool to get real-time weather forecasts. You can ask about the weather in specific locations.
            Do not make up alternative sources or suggest alternative data sources.
            When making tool/function calls, ensure you understand the description of the arguments/properties. 
            They may give useful information as to why types of values are allowed or required. 
            For example, the \'query\' argument takes a latitude, longitude value, so you must convert a string location to this type.
            """,
    )
    chat.set_stack_token(stackoverflow_token)
    instances[request.session_hash] = chat
    return None


# Example: custom theme for a more modern look
brand_theme = gr.themes.Default(
    primary_hue="blue",
    secondary_hue="blue",
    neutral_hue="gray",
    font=["Segoe UI", "Arial", "sans-serif"],
    font_mono=["Courier New", "monospace"],
    text_size="lg",
).set(
    button_primary_background_fill="#0f6cbd",
    button_primary_background_fill_hover="#115ea3",
    button_primary_background_fill_hover_dark="#4f52b2",
    button_primary_background_fill_dark="#5b5fc7",
    button_primary_text_color="#ffffff",
    button_secondary_background_fill="#e0e0e0",
    button_secondary_background_fill_hover="#c0c0c0",
    button_secondary_text_color="#000000",
    body_background_fill="#f5f5f5",
    block_background_fill="#ffffff",
    body_text_color="#242424",
    body_text_color_subdued="#616161",
    block_border_color="#d1d1d1",
    block_border_color_dark="#333333",
    input_background_fill="#ffffff",
    input_border_color="#d1d1d1",
    input_border_color_focus="#0f6cbd",
)


async def clear_thread(request: gr.Request):
    # Placeholder for thread reset logic if using AzureAIAgent threads
    chat = instances.get(request.session_hash)
    await chat.reset_thread()
    return []


def on_example_clicked(evt: gr.SelectData):
    return evt.value["text"]


async def chat_with_agent(request: gr.Request, user_message: dict, history: List[dict]):
    for x in user_message["files"]:
        history.append({"role": "user", "content": {"path": x}})
    if user_message["text"] is not None:
        history.append({"role": "user", "content": user_message["text"]})

    assistant_msg = {
        "role": "assistant",
        "content": "Thinking..",
        "metadata": {"status": "pending"},
    }
    yield history + [assistant_msg], gr.MultimodalTextbox(interactive=False, value=None)

    chat = instances.get(request.session_hash)

    agent_response = chat.azure_enterprise_chat(user_message, history)

    async for new_history in agent_response:
        assistant_msg["metadata"]["status"] = "done"
        yield [] + new_history, gr.MultimodalTextbox(interactive=False, value=None)


with gr.Blocks(
    theme=brand_theme,
    css="""
    footer {visibility: hidden;}
    .header-row {display: flex; justify-content: space-between; align-items: center;}
    .header-title {text-align: left; font-size: 2rem; font-weight: bold; flex: 1;}
    .user-display {text-align: right; font-size: 1.1rem; font-weight: normal; min-width: 200px;}
    """,
    fill_height=True,
) as demo:
    with gr.Row(elem_classes="header-row"):
        gr.HTML('<div class="header-title">Azure AI Agent Service</div>')
        user_display = gr.Markdown(
            value="", elem_id="user-display", elem_classes="user-display"
        )
    demo.load(get_user, None, user_display)
    chatbot = gr.Chatbot(
        label="Agent",
        type="messages",
        examples=[
            {"text": "Get user information from Stack Overflow."},
            {
                "text": "What's the forecast for next 5 days for Redmond,WA? Build a table, use emojis."
            },
            {"text": "How is Contoso's stock doing today?"},
            {"text": "Send my direct report a summary of the HR policy."},
        ],
        show_label=False,
        scale=1,
        avatar_images=(
            None,
            "https://em-content.zobj.net/source/twitter/53/robot-face_1f916.png",
        ),
    )
    chat_input = gr.MultimodalTextbox(
        interactive=True,
        file_count="single",
        placeholder="Enter message or upload file...",
        show_label=False,
        sources=["upload"],
        file_types=[
            ".c",
            ".cs",
            ".cpp",
            ".doc",
            ".docx",
            ".html",
            ".java",
            ".json",
            ".md",
            ".pdf",
            ".php",
            ".pptx",
            ".py",
            ".rb",
            ".tex",
            ".txt",
            ".css",
            ".js",
            ".sh",
            ".ts",
            ".csv",
            ".jpeg",
            ".jpg",
            ".gif",
            ".png",
            ".tar",
            ".xlsx",
            ".xml",
            ".zip",
        ],
    )

    chat_input.attach_load_event(set_enterprise_chat, every=None)

    # On submit: call azure_enterprise_chat, then clear the textbox
    (
        chat_input.submit(
            fn=chat_with_agent,
            show_progress="full",
            inputs=[chat_input, chatbot],
            outputs=[chatbot, chat_input],
        ).then(
            fn=lambda: gr.MultimodalTextbox(interactive=True, value=None),
            outputs=chat_input,
        )
    )

    # Populate textbox when an example is clicked
    chatbot.example_select(fn=on_example_clicked, inputs=None, outputs=chat_input)

    chatbot.clear(fn=clear_thread, outputs=chatbot)

# demo.launch()
