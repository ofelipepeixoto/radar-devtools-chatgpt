"""Strict JSON handling without binary floating point or executable evaluation."""

import json
from decimal import Decimal, DecimalException

from .errors import MAX_DEPTH, MAX_NODES, ToolError


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ToolError("duplicate_key", "JSON contém chave duplicada.")
        result[key] = value
    return result


def _number(text):
    if len(text) > 128:
        raise ToolError("number_limit", "Número JSON excede o limite de 128 caracteres.")
    try:
        return Decimal(text)
    except DecimalException:
        raise ToolError("number_limit", "Expoente numérico fora do limite suportado.") from None


def _constant(_text):
    raise ToolError("invalid_json", "JSON não permite números não finitos.")


def validate_tree(value):
    """Bound recursion, object count and types before later serialization."""
    stack = [(value, 0)]
    count = 0
    while stack:
        item, depth = stack.pop()
        count += 1
        if count > MAX_NODES or depth > MAX_DEPTH:
            raise ToolError("structure_limit", "Estrutura JSON excede o limite permitido.")
        if isinstance(item, dict):
            if not all(isinstance(k, str) for k in item):
                raise ToolError("invalid_json", "As chaves JSON precisam ser texto.")
            for key in item:
                try:
                    key.encode("utf-8", errors="strict")
                except UnicodeError:
                    raise ToolError("invalid_utf8", "JSON contém Unicode inválido.") from None
            stack.extend((child, depth + 1) for child in item.values())
        elif isinstance(item, list):
            stack.extend((child, depth + 1) for child in item)
        elif not (item is None or type(item) in (str, bool, int, Decimal)):
            raise ToolError("invalid_json", "Tipo de dado incompatível com JSON estrito.")
        if isinstance(item, Decimal) and not item.is_finite():
            raise ToolError("invalid_json", "JSON não permite números não finitos.")
        if isinstance(item, str):
            try:
                item.encode("utf-8", errors="strict")
            except UnicodeError:
                raise ToolError("invalid_utf8", "JSON contém Unicode inválido.") from None


def strict_loads(text):
    try:
        value = json.loads(
            text, object_pairs_hook=_pairs, parse_int=_number,
            parse_float=_number, parse_constant=_constant,
        )
    except ToolError:
        raise
    except (ValueError, TypeError, RecursionError, OverflowError):
        raise ToolError("invalid_json", "O conteúdo não é JSON válido.") from None
    validate_tree(value)
    return value


def render_json(value, indent=None, level=0):
    """Serialize Decimal lexically; exponent notation avoids exponent expansion."""
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        items = [(json.dumps(k, ensure_ascii=True), v) for k, v in value.items()]
        if not items:
            return "{}"
        if indent is None:
            return "{" + ",".join(k + ":" + render_json(v) for k, v in items) + "}"
        pad = " " * indent * (level + 1)
        end = " " * indent * level
        return "{\n" + ",\n".join(
            pad + k + ": " + render_json(v, indent, level + 1) for k, v in items
        ) + "\n" + end + "}"
    if isinstance(value, list):
        if not value:
            return "[]"
        if indent is None:
            return "[" + ",".join(render_json(v) for v in value) + "]"
        pad = " " * indent * (level + 1)
        end = " " * indent * level
        return "[\n" + ",\n".join(
            pad + render_json(v, indent, level + 1) for v in value
        ) + "\n" + end + "]"
    return json.dumps(value, ensure_ascii=True, allow_nan=False)


def _pointer(path, key):
    return path + "/" + str(key).replace("~", "~0").replace("/", "~1")


def json_diff(before, after):
    changes = []

    def emit(kind, path, old=None, new=None):
        if len(changes) >= 200:
            raise ToolError("diff_limit", "A diferença excede 200 alterações.")
        entry = {"kind": kind, "path": path}
        if kind != "added":
            entry["before_json"] = render_json(old)
        if kind != "removed":
            entry["after_json"] = render_json(new)
        changes.append(entry)

    def walk(old, new, path):
        if type(old) is not type(new):
            emit("changed", path, old, new)
        elif isinstance(old, dict):
            for key in sorted(old.keys() - new.keys()):
                emit("removed", _pointer(path, key), old[key])
            for key in sorted(new.keys() - old.keys()):
                emit("added", _pointer(path, key), new=new[key])
            for key in sorted(old.keys() & new.keys()):
                walk(old[key], new[key], _pointer(path, key))
        elif isinstance(old, list):
            for index in range(max(len(old), len(new))):
                child = _pointer(path, index)
                if index >= len(old):
                    emit("added", child, new=new[index])
                elif index >= len(new):
                    emit("removed", child, old[index])
                else:
                    walk(old[index], new[index], child)
        elif old != new:
            emit("changed", path, old, new)

    walk(before, after, "")
    return {"equal": not changes, "changes": changes}
