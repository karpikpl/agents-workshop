import streamlit as st
import json

from logging_tools.tool_log_base import ToolLogBase, ToolCall


class StreamlitToolLog(ToolLogBase):
    def log(self, toolCall: ToolCall, save: bool = True):
        if save:
            st.session_state.tool_log.append(toolCall)

        with st.sidebar:
            with st.container():
                message = f'\n<i><span style="color: limegreen;">🔧Tool Call </span></i> {toolCall.name}'

                if toolCall.args and isinstance(toolCall.args, (str, float, int)):
                    message += (
                        f' with <span style="color: limegreen;">{toolCall.args}</span>'
                    )
                if toolCall.result and isinstance(toolCall.result, (str, float, int)):
                    message += (
                        f' = <span style="color: limegreen;">{toolCall.result}</span>'
                    )
                message += "</i>"
                st.html(message)

                if toolCall.args and isinstance(toolCall.args, (dict, list)):
                    with st.expander(f"{toolCall.name} arguments", expanded=False):
                        st.json(json.dumps(toolCall.args, indent=2))
                if toolCall.result and isinstance(toolCall.result, (dict, list)):
                    with st.expander(f"{toolCall.name} result", expanded=False):
                        st.json(json.dumps(toolCall.result, indent=2))
