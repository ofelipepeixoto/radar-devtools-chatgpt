"""Strict request boundary shared by CLI and future adapters."""

import json
from decimal import Decimal

from .errors import MAX_INPUT_BYTES, MAX_OUTPUT_BYTES, MAX_TEXT_BYTES, ToolError
from .json_tools import strict_loads
from .operations import LIMITATIONS, OPERATIONS


def parse_request(raw: bytes) -> dict:
    if type(raw) is not bytes:
        raise ToolError("invalid_input", "A entrada deve conter bytes UTF-8.")
    if len(raw) > MAX_INPUT_BYTES:
        raise ToolError("input_limit", "A entrada excede 256 KiB.")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeError:
        raise ToolError("invalid_utf8", "A entrada não contém UTF-8 válido.") from None
    request = strict_loads(text)
    # The only supported numeric argument is indent; keep it an integer.
    if isinstance(request, dict) and isinstance(request.get("arguments"), dict):
        indent = request["arguments"].get("indent")
        if isinstance(indent, Decimal) and indent.as_tuple().exponent == 0 and indent in (Decimal(2), Decimal(4)):
            request["arguments"]["indent"] = int(indent)
    return request


def execute_request(request: dict) -> dict:
    if type(request) is not dict or set(request) != {"schema_version", "operation", "arguments"}:
        raise ToolError("invalid_request", "Campos obrigatórios ou adicionais inválidos.")
    if request["schema_version"] != "1.0":
        raise ToolError("schema_version", "Versão de contrato não suportada.")
    operation = request["operation"]
    if type(operation) is not str or operation not in OPERATIONS:
        raise ToolError("unknown_operation", "Operação não suportada.")
    args = request["arguments"]
    keys, handler = OPERATIONS[operation]
    if type(args) is not dict or set(args) != keys:
        raise ToolError("invalid_arguments", "Argumentos obrigatórios ou adicionais inválidos.")
    for key, value in args.items():
        if key == "indent":
            if type(value) is not int or value not in (2, 4):
                raise ToolError("invalid_arguments", "Recuo precisa ser o inteiro 2 ou 4.")
        elif type(value) is not str:
            raise ToolError("invalid_arguments", "O argumento precisa ser texto.")
        else:
            try:
                size = len(value.encode("utf-8", errors="strict"))
            except UnicodeError:
                raise ToolError("invalid_utf8", "Texto contém caractere Unicode inválido.") from None
            if size > MAX_TEXT_BYTES:
                raise ToolError("text_limit", "Texto excede 64 KiB em UTF-8.")
    result = handler(args)
    report = {
        "schema_version": "1.0", "operation": operation,
        "result": result, "limitations": list(LIMITATIONS[operation]),
    }
    if len(json.dumps(report, ensure_ascii=True, allow_nan=False).encode("utf-8")) > MAX_OUTPUT_BYTES:
        raise ToolError("output_limit", "A saída excede 1 MiB.")
    return report
