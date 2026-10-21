"""Bounded file adapter. Never sends request data to a network or log."""
import argparse
import hashlib
import json
import os
import stat
import sys
from contextlib import contextmanager

from . import ToolError, execute_request, parse_request

INPUT_LIMIT = 256 * 1024
OUTPUT_LIMIT = 1024 * 1024


@contextmanager
def parent_handle(path):
    """Open each parent without following symbolic links (POSIX only)."""
    if os.name != "posix" or not hasattr(os, "O_NOFOLLOW"):
        raise ToolError("unsupported_platform", "Este adaptador exige POSIX.")
    raw = os.fspath(path)
    if type(raw) is not str or "\x00" in raw:
        raise ToolError("invalid_path", "Caminho inválido.")
    try:
        raw.encode("utf-8", errors="strict")
    except UnicodeError:
        raise ToolError("invalid_path", "Caminho inválido.") from None
    parts = raw.split("/")
    if not raw or raw.endswith("/") or ".." in parts:
        raise ToolError("invalid_path", "Caminho inválido.")
    start = "/" if raw.startswith("/") else "."
    parts = [p for p in parts if p not in ("", ".")]
    if not parts:
        raise ToolError("invalid_path", "Caminho inválido.")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    fd = os.open(start, flags)
    try:
        for part in parts[:-1]:
            next_fd = os.open(part, flags, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        yield fd, parts[-1]
    finally:
        os.close(fd)


def read_input(path):
    with parent_handle(path) as (parent, name):
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        with os.fdopen(fd, "rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise ToolError("invalid_file", "A entrada deve ser arquivo regular.")
            raw = stream.read(INPUT_LIMIT + 1)
    if len(raw) > INPUT_LIMIT:
        raise ToolError("input_limit", "A entrada excede o limite.")
    return raw


def write_new(path, raw):
    if len(raw) > OUTPUT_LIMIT:
        raise ToolError("output_limit", "A saída excede o limite.")
    with parent_handle(path) as (parent, name):
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
        fd = os.open(name, flags, 0o600, dir_fd=parent)
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())


class SafeParser(argparse.ArgumentParser):
    def error(self, message):
        raise ToolError("usage", "Use: python -m radar_devtools ENTRADA --output SAIDA_NOVA")


def main(argv=None):
    parser = SafeParser(description="Radar DevTools: utilitários locais com dados fictícios.")
    parser.add_argument("input")
    parser.add_argument("--output", required=True)
    try:
        args = parser.parse_args(argv)
        raw = read_input(args.input)
        report = execute_request(parse_request(raw))
        report["input_sha256"] = hashlib.sha256(raw).hexdigest()
        report["engine_version"] = "0.1.0"
        encoded = (json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
        write_new(args.output, encoded)
    except ToolError as error:
        print(json.dumps({"status": "error", "code": error.code, "message": error.message}, ensure_ascii=False), file=sys.stderr)
        return 2
    except OSError:
        print('{"status":"error","code":"file_error","message":"Falha de arquivo; verifique existência, permissões e links simbólicos."}', file=sys.stderr)
        return 2
    print(json.dumps({"status": "ok", "operation": report["operation"], "input_sha256": report["input_sha256"]}))
    return 0
