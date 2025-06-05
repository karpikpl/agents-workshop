import json
from datetime import datetime as pydatetime, timedelta, timezone

from semantic_kernel.functions import kernel_function


class SimpleTool:
    """
    A simple sample tool class for use by an AI agent.
    This tool provides basic arithmetic operations and a greeting.
    """

    @kernel_function(description="Returns a greeting message for the given name.")
    def greet(self, name: str) -> str:
        """
        Returns a greeting message for the given name.
        """
        return f"Hello, {name}! How can I assist you today?"

    @kernel_function(description="Returns the sum of two numbers.")
    def add(self, a: float, b: float) -> float:
        """
        Returns the sum of two numbers.
        """
        return a + b

    @kernel_function(description="Returns the difference between two numbers.")
    def subtract(self, a: float, b: float) -> float:
        """
        Returns the difference between two numbers.
        """
        return a - b

    @kernel_function(description="Returns the product of two numbers.")
    def multiply(self, a: float, b: float) -> float:
        """
        Returns the product of two numbers.
        """
        return a * b

    @kernel_function(
        description="Returns the quotient of two numbers. Raises ValueError if division by zero is attempted."
    )
    def divide(self, a: float, b: float) -> float:
        """
        Returns the quotient of two numbers.
        Raises ValueError if division by zero is attempted.
        """
        if b == 0:
            raise ValueError("Division by zero is not allowed.")
        return a / b

    @kernel_function(
        description="""
    Returns either the current UTC date/time in the given format, or if unix_ts
    is given, converts that timestamp to either UTC or local time (tz_offset_seconds).

    :param format_str: The strftime format, e.g. "%Y-%m-%d %H:%M:%S".
    :param unix_ts: Optional Unix timestamp. If provided, returns that specific time.
    :param tz_offset_seconds: If provided, shift the datetime by this many seconds from UTC.
    :return: A JSON string containing the "datetime" or an "error" key/value.
    """
    )
    def fetch_datetime(
        self,
        format_str: str = "%Y-%m-%d %H:%M:%S",
        unix_ts: int | None = None,
        tz_offset_seconds: int | None = None,
    ) -> str:
        """
        Returns either the current UTC date/time in the given format, or if unix_ts
        is given, converts that timestamp to either UTC or local time (tz_offset_seconds).

        :param format_str: The strftime format, e.g. "%Y-%m-%d %H:%M:%S".
        :param unix_ts: Optional Unix timestamp. If provided, returns that specific time.
        :param tz_offset_seconds: If provided, shift the datetime by this many seconds from UTC.
        :return: A JSON string containing the "datetime" or an "error" key/value.
        """
        try:
            if unix_ts is not None:
                dt_utc = pydatetime.fromtimestamp(unix_ts, tz=timezone.utc)
            else:
                dt_utc = pydatetime.now(timezone.utc)

            if tz_offset_seconds is not None:
                local_tz = timezone(timedelta(seconds=tz_offset_seconds))
                dt_local = dt_utc.astimezone(local_tz)
                result_str = dt_local.strftime(format_str)
            else:
                result_str = dt_utc.strftime(format_str)

            return json.dumps({"datetime": result_str})
        except Exception as e:
            return json.dumps({"error": f"Exception: {str(e)}"})
