from typing import List
import gradio as gr
from agent_chat import create_enterprise_chat

# Use asyncio to run the async function in a sync context
enterprise_chat = None


async def get_enterprise_chat():
    global enterprise_chat
    if enterprise_chat is None:
        enterprise_chat = await create_enterprise_chat(
            "Bob", """
            You are a helpful assistant for enterprise queries. Use bing search and file search tools to answer questions.
            
            ## Tool usage

            ### Bing Search Tool
            Use the Bing Search tool to find information on the web. You can search for company policies, weather forecasts, stock prices, and more.
            Example: prompt:"Who won champions league" should produce a Bing search query 'https://api.bing.microsoft.com/v7.0/search?q=champions league 2025 winner'
            """,
        )
    return enterprise_chat


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


async def clear_thread():
    # Placeholder for thread reset logic if using AzureAIAgent threads
    await enterprise_chat.reset_thread()
    return []


def on_example_clicked(evt: gr.SelectData):
    return evt.value["text"]


async def chat_with_agent(user_message: dict, history: List[dict]):
    for x in user_message["files"]:
        history.append({"role": "user", "content": {"path": x}})
    if user_message["text"] is not None:
        history.append({"role": "user", "content": user_message["text"]})

    yield history, gr.MultimodalTextbox(interactive=False, value=None)

    agent = await get_enterprise_chat()
    async for new_history in agent.azure_enterprise_chat(user_message, history):
        # print('\nupdating history')
        yield new_history, gr.MultimodalTextbox(interactive=False, value=None)


with gr.Blocks(
    theme=brand_theme, css="footer {visibility: hidden;}", fill_height=True
) as demo:
    gr.HTML('<h1 style="text-align: center;">Azure AI Agent Service</h1>')
    chatbot = gr.Chatbot(
        label="Agent",
        type="messages",
        examples=[
            {"text": "What's my company's remote work policy?"},
            {"text": "Check if it will rain tomorrow?"},
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
    )

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
