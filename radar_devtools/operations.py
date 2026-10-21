"""Small transformations implemented independently with the Python standard library."""

import base64
import binascii
import hashlib
import ipaddress
import re
import uuid
from datetime import datetime, timezone
from urllib.parse import quote, unquote_to_bytes, urlsplit

from .errors import ToolError
from .json_tools import json_diff, render_json, strict_loads

_BAD_PERCENT = re.compile(r"%(?![0-9a-fA-F]{2})")
_TIME = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})\Z"
)


def _url_decode(text):
    if _BAD_PERCENT.search(text):
        raise ToolError("invalid_url_encoding", "Escape percentual inválido.")
    try:
        return unquote_to_bytes(text).decode("utf-8", errors="strict")
    except (UnicodeError, ValueError):
        raise ToolError("invalid_utf8", "O conteúdo decodificado não é UTF-8 válido.") from None


def _url_inspect(text):
    if any(ord(c) < 33 or ord(c) == 127 or c.isspace() for c in text) or "\\" in text:
        raise ToolError("invalid_url", "URL contém caracteres proibidos.")
    if _BAD_PERCENT.search(text):
        raise ToolError("invalid_url_encoding", "Escape percentual inválido.")
    try:
        parts = urlsplit(text)
        if parts.scheme not in ("http", "https") or not parts.hostname:
            raise ValueError
        if parts.username is not None or parts.password is not None:
            raise ToolError("url_credentials", "URL com credenciais não é aceita.")
        port = parts.port
        host = parts.hostname
        try:
            ipaddress.ip_address(host)
        except ValueError:
            ascii_host = host.encode("idna").decode("ascii")
            labels = ascii_host.removesuffix(".").split(".")
            if len(ascii_host) > 253 or any(
                not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?", label)
                for label in labels
            ):
                raise ValueError
    except ToolError:
        raise
    except (ValueError, UnicodeError):
        raise ToolError("invalid_url", "A URL absoluta HTTP/HTTPS não é válida.") from None
    return {
        "scheme": parts.scheme, "host": host, "port": port,
        "path": parts.path, "query": parts.query, "fragment": parts.fragment,
        "network_accessed": False,
    }


def _base64_decode(text):
    try:
        raw = base64.b64decode(text.encode("ascii"), validate=True)
        if base64.b64encode(raw).decode("ascii") != text:
            raise ValueError
        return raw.decode("utf-8", errors="strict")
    except (ValueError, UnicodeError, binascii.Error):
        raise ToolError("invalid_base64", "Base64 canônico UTF-8 inválido.") from None


def _uuid_inspect(text):
    try:
        value = uuid.UUID(text)
        if str(value) != text or value.variant != uuid.RFC_4122 or value.version not in range(1, 9):
            raise ValueError
    except (ValueError, AttributeError):
        raise ToolError("invalid_uuid", "UUID RFC 4122 canônico em minúsculas inválido.") from None
    return {"value": str(value), "version": value.version, "variant": "RFC 4122"}


def _network(text):
    try:
        if "/" not in text:
            raise ValueError
        network = ipaddress.ip_network(text, strict=True)
    except ValueError:
        raise ToolError("invalid_cidr", "CIDR inválido ou com bits de host ativos.") from None
    return {
        "network": str(network), "version": network.version,
        "prefix_length": network.prefixlen, "address_count": str(network.num_addresses),
        "first_address": str(network.network_address),
        "last_address": str(network.broadcast_address),
    }


def _time(text):
    if not _TIME.fullmatch(text):
        raise ToolError("invalid_time", "Data exige ISO 8601 com hora, segundos e fuso explícito.")
    if not text.endswith("Z") and (int(text[-5:-3]) > 23 or int(text[-2:]) > 59):
        raise ToolError("invalid_time", "Data ou fuso inválido.")
    try:
        value = datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)
    except (ValueError, OverflowError):
        raise ToolError("invalid_time", "Data ou fuso inválido.") from None
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    delta = value - epoch
    micros = (delta.days * 86400 + delta.seconds) * 1_000_000 + delta.microseconds
    return {"utc": value.isoformat().replace("+00:00", "Z"), "unix_microseconds": str(micros)}


OPERATIONS = {
    "json.format": ({"text", "indent"}, lambda a: {"text": render_json(strict_loads(a["text"]), a["indent"])}),
    "json.diff": ({"before", "after"}, lambda a: json_diff(strict_loads(a["before"]), strict_loads(a["after"]))),
    "base64.encode": ({"text"}, lambda a: {"text": base64.b64encode(a["text"].encode("utf-8")).decode("ascii")}),
    "base64.decode": ({"text"}, lambda a: {"text": _base64_decode(a["text"])}),
    "url.inspect": ({"url"}, lambda a: _url_inspect(a["url"])),
    "url.encode": ({"text"}, lambda a: {"text": quote(a["text"], safe="", encoding="utf-8", errors="strict")}),
    "url.decode": ({"text"}, lambda a: {"text": _url_decode(a["text"])}),
    "hash.sha256": ({"text"}, lambda a: {"hex": hashlib.sha256(a["text"].encode("utf-8")).hexdigest(), "encoding": "UTF-8"}),
    "uuid.inspect": ({"value"}, lambda a: _uuid_inspect(a["value"])),
    "network.cidr": ({"value"}, lambda a: _network(a["value"])),
    "time.convert": ({"value"}, lambda a: _time(a["value"])),
}

LIMITATIONS = {
    "json.format": ["Preserva números decimais sem ponto flutuante binário; não valida schema de negócio."],
    "json.diff": ["Compara estrutura JSON; arrays são comparados por posição; máximo de 200 alterações."],
    "base64.encode": ["Base64 é codificação reversível, não criptografia."],
    "base64.decode": ["Base64 é codificação reversível, não criptografia; aceita apenas saída UTF-8."],
    "url.inspect": ["Somente parsing local; não confirma existência, propriedade ou segurança do destino."],
    "url.encode": ["Codifica um componente completo; espaços viram %20."],
    "url.decode": ["Decodifica percentuais UTF-8; o caractere + permanece +."],
    "hash.sha256": ["Hash de texto UTF-8; não prova autoria nem autenticidade da origem."],
    "uuid.inspect": ["Formato e variante não comprovam unicidade nem origem."],
    "network.cidr": ["A contagem inclui todos os endereços; não enumera hosts nem acessa a rede."],
    "time.convert": ["Usa fuso fixo explícito; não aplica calendários de mercado ou regras regionais de horário de verão."],
}
