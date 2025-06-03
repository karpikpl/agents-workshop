# 🧑‍💻 03 - Building Custom Tools: Code Interpreter

![Code Interpreter](https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/examples/example-assistant-code?pivots=programming-language-python)

---

## 🤔 What is the Code Interpreter?

The **Code Interpreter** is a powerful built-in tool that enables your agent to write, execute, and debug code in a secure, sandboxed environment. This allows the agent to:

- Analyze and visualize data (e.g., CSV, JSON, images)
- Perform calculations and generate plots
- Transform and clean datasets
- Provide code-based solutions to user queries
- Enhance chat experiences with dynamic, code-driven answers

The code interpreter is especially useful for data science, analytics, and scenarios where the agent needs to reason with or manipulate data on the fly.

> **Note:** The code interpreter runs in a restricted environment for security. It cannot access the internet or external resources unless explicitly allowed.

---

## 🚀 Task: Use the Code Interpreter on a Sample CSV File

In this exercise, you'll enable the code interpreter for your agent and use it to analyze a sample CSV file.

### 📝 Steps

1. **Modify [`agent.py`](./agent.py):**
   - Update the `create_update_agent_definition` function to enable the code interpreter tool for your agent.
   - Example:  
     ```python
     # ...existing code...
     agent_definition = await client.agents.create_agent(
         # ...existing code...
         tools=["code_interpreter"],  # Add this line to enable the code interpreter
         # ...existing code...
     )
     # ...existing code...
     ```

2. **Handle Agent Responses:**
   - Update your code to properly display or process responses that include code interpreter outputs (such as charts, tables, or code snippets).

3. **Upload and Analyze a CSV File:**
   - Interact with your agent, upload a sample CSV file, and ask the agent to analyze or visualize the data.
   - Example prompt:  
     > "Please analyze the uploaded sales_data.csv and show me a summary and a chart of sales by region."

---

## 📚 Reference

- [Semantic Kernel Reference Implementation](https://github.com/microsoft/semantic-kernel/blob/079594d29792071c0474dc30543697972b77dbc9/python/samples/getting_started_with_agents/azure_ai_agent/step4_azure_ai_agent_code_interpreter.py)
- [Semantic Kernel Plugins Documentation](https://learn.microsoft.com/en-us/semantic-kernel/concepts/plugins/?pivots=programming-language-python)

---

## 🧪 Extra Task: Experiment with Your Own Data

- Try uploading different CSV files or data formats (e.g., JSON, images).
- Change your prompts to ask for different types of analysis or visualizations.
- Explore the limits of what the code interpreter can do (e.g., ask for data cleaning, advanced plots, or code explanations).

---

## 💡 Tips

- The code interpreter can generate Python code, run it, and return results (including images and tables).
- If you get errors, check that your data is formatted correctly and that your prompt is clear.
- For more advanced use, try combining code interpreter with other plugins or tools.

---

✨ **Unlock the full power of your agent by letting it code for you!** ✨