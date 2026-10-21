"""Safe public errors and resource bounds for the offline toolbox."""

MAX_INPUT_BYTES = 256 * 1024
MAX_TEXT_BYTES = 64 * 1024
MAX_OUTPUT_BYTES = 1024 * 1024
MAX_DEPTH = 32
MAX_NODES = 10_000


class ToolError(ValueError):
    """An error whose code and message never include submitted values."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message
