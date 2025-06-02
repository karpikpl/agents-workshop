# 03 - Building Custom Tools - Code Interpreter

![Code Interpreter](https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/examples/example-assistant-code?pivots=programming-language-python)

## Adding Code Interpreter

Code Interpreter can develop and run code in a sandboxed environment to analyze data and enhacing the chat experience.

## Task - use code interpreter on a sample CSV file

Goal of the exercise is to use

Reference implementation by [Semantic Kernel](https://github.com/microsoft/semantic-kernel/blob/079594d29792071c0474dc30543697972b77dbc9/python/samples/getting_started_with_agents/azure_ai_agent/step4_azure_ai_agent_code_interpreter.py)

1. Modify [agent.py](./agent.py) by updating `create_update_agent_definition` function.

2. Handle agent responses that include items from code interpreter.

## Extra Task - experiment with your own data

Try changing the prompts and the uploaded file.