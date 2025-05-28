# 03 - Building Custom Tools

![Function Calling](https://learn.microsoft.com/en-us/semantic-kernel/media/functioncalling.png)

## Simple Tool Calling

Tools/Plugins make the agent finally do useful things.

More about [Plugins in Semantic Kernel](https://learn.microsoft.com/en-us/semantic-kernel/concepts/plugins/?pivots=programming-language-python)

### Adding plugins/functions/tools

First define your plugin in a Python class.
Annotate functions with `@kernel_function(description="<Description of your function for the agent>")`.

To add plugins for the agent, simply add them to `AzureAIAgent` definition in [agent.py](./agent.py).

```python
agent = AzureAIAgent(
    arguments=KernelArguments(kernel_settings),
    kernel=kernel,
    client=client,
    definition=agent_definition,
    plugins=[SimpleTool()],
)
```

#### [Extra] Function filters

Modify `KernelFactory` to add function filter used for logging:

```python
class KernelFactory:
    @staticmethod
    async def create_kernel(agent: Agent) -> Kernel:
        with get_span("create_kernel") as span:
            span.set_attribute("agent_id", agent.id)

            kernel = Kernel()

            async def auto_function_filter(
                context: AutoFunctionInvocationContext, next
            ):
                """A filter that will be called for auto-invoked functions."""
                with get_span("auto_function_filter"):
                    function_name = context.function.name
                    plugin_name = context.function.plugin_name

                    # Format arguments for logging/display
                    safe_args = {}
                    if context.arguments:
                        # Create a sanitized copy of arguments
                        for arg_name, arg_value in context.arguments.items():
                            if arg_name.lower() in [
                                "key",
                                "password",
                                "secret",
                                "token",
                                "authorization",
                            ]:
                                safe_args[arg_name] = "***REDACTED***"
                            elif isinstance(arg_value, str) and len(arg_value) > 100:
                                safe_args[arg_name] = f"{arg_value[:97]}..."
                            else:
                                safe_args[arg_name] = arg_value

                    # Record start time for duration calculation
                    start_time = asyncio.get_event_loop().time()

                    # Create function call info
                    call_info = {
                        "type": "function_start",
                        "function": function_name,
                        "plugin": plugin_name,
                        "arguments": safe_args,
                        "timestamp": start_time,
                    }

                    # Add to function call stream
                    # function_stream.add_function_call(call_info)
                    logger.info(json.dumps(call_info, indent=2))

                    # Log the function call with more context
                    prefix = "[AUTO]"
                    logger.debug(
                        f"{prefix} Function called: {plugin_name}.{function_name} with arguments: {safe_args}"
                    )

                    # Execute the function
                    try:
                        await next(context)
                        status = "success"
                    except Exception as e:
                        status = "error"
                        logger.error(
                            f"Error in function {plugin_name}.{function_name}: {str(e)}"
                        )
                        raise
                    finally:
                        # End time for duration calculation
                        end_time = asyncio.get_event_loop().time()

                        # Create completion info
                        completion_info = {
                            "type": "function_end",
                            "function": function_name,
                            "plugin": plugin_name,
                            "status": status,
                            "timestamp": end_time,
                            "start_timestamp": start_time,  # Include start timestamp for duration calculation
                        }

                        # Add result info if available
                        if hasattr(context, "result") and context.result is not None:
                            result_value = (
                                str(context.result.value)
                                if hasattr(context.result, "value")
                                else "N/A"
                            )
                            if len(result_value) > 100:
                                result_value = f"{result_value[:97]}..."
                            completion_info["result"] = result_value

                        # Add to function call stream
                        # function_stream.add_function_call(completion_info)
                        logger.info(json.dumps(completion_info, indent=2))

                        # Log the function completion with more context
                        duration_ms = (end_time - start_time) * 1000
                        logger.debug(
                            f"{prefix} Function completed: {plugin_name}.{function_name} with status: {status} in {duration_ms:.2f}ms"
                        )

            # Add the auto function invocation filter
            kernel.add_filter(
                FilterTypes.AUTO_FUNCTION_INVOCATION, auto_function_filter
            )

            # Also add as regular function invocation filter for compatibility
            # kernel.add_filter(FilterTypes.FUNCTION_INVOCATION, auto_function_filter)

            return kernel
```


- Demonstrate building a custom tool for Stack Overflow or Azure DevOps.
- Discuss the on-behalf-of (OBO) authentication workflow.
