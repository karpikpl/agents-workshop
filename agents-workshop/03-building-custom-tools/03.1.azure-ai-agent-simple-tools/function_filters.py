from semantic_kernel.contents import ChatMessageContent, FunctionCallContent
from semantic_kernel.filters import AutoFunctionInvocationContext


def print_tool_calls(message: ChatMessageContent) -> None:
    # A helper method to pretty print the tool calls from the message.
    # This is only triggered if auto invoke tool calls is disabled.
    items = message.items
    formatted_tool_calls = []
    for i, item in enumerate(items, start=1):
        if isinstance(item, FunctionCallContent):
            tool_call_id = item.id
            function_name = item.name
            function_arguments = item.arguments
            formatted_str = (
                f"tool_call {i} id: {tool_call_id}\n"
                f"tool_call {i} function name: {function_name}\n"
                f"tool_call {i} arguments: {function_arguments}"
            )
            formatted_tool_calls.append(formatted_str)
    print("Tool calls:\n" + "\n\n".join(formatted_tool_calls))


# A filter is a piece of custom code that runs at certain points in the process
# this sample has a filter that is called during Auto Function Invocation
# this filter will be called for each function call in the response.
# You can name the function itself with arbitrary names, but the signature needs to be:
# `context, next`
# You are then free to run code before the call to the next filter or the function itself.
# if you want to terminate the function calling sequence. set context.terminate to True
async def auto_function_invocation_filter(context: AutoFunctionInvocationContext, next):
    """A filter that will be called for each function call in the response."""
    print("\nAuto function invocation filter")
    print(f"Function: {context.function.name}")
    print(f"Request sequence: {context.request_sequence_index}")
    print(f"Function sequence: {context.function_sequence_index}")

    # as an example
    function_calls = context.chat_history.messages[-1].items
    print(f"Number of function calls: {len(function_calls)}")
    # if we don't call next, it will skip this function, and go to the next one
    await next(context)
    #############################
    # Note: to simply return the unaltered function results, uncomment the `context.terminate = True` line and
    # comment out the lines starting with `result = context.function_result` through `context.terminate = True`.
    context.terminate = True
    #############################
    # result = context.function_result
    # if context.function.plugin_name == "math":
    #     print("Altering the Math plugin")
    #     context.function_result = FunctionResult(
    #         function=result.function,
    #         value="Stop trying to ask me to do math, I don't like it!",
    #     )
    #     context.terminate = True
