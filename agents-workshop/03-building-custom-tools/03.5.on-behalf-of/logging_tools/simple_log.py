import json
import logging
from rich.logging import RichHandler

from logging_tools.tool_log_base import ToolLogBase, ToolCall

logging.basicConfig(
    level=logging.WARNING,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)


class SimpleLog(ToolLogBase):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    def log(self, toolCall: ToolCall, save: bool = True):
        message = f"🔧Tool Call {toolCall.name}"

        if toolCall.args and isinstance(toolCall.args, (str, float, int)):
            message += f" with {toolCall.args}"
        if toolCall.result and isinstance(toolCall.result, (str, float, int)):
            message += f" = {toolCall.result}"

        self.logger.info(message)

        if toolCall.args and isinstance(toolCall.args, (dict, list)):
            self.logger.info(f"Arguments: {json.dumps(toolCall.args, indent=2)}")
        if toolCall.result and isinstance(toolCall.result, (dict, list)):
            self.logger.info(f"Result: {json.dumps(toolCall.result, indent=2)}")
