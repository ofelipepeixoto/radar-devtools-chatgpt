"""Independent black-box and filesystem checks using only synthetic input."""
import ast
import base64
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from radar_devtools import ToolError, execute_request, parse_request
from radar_devtools.cli import main


ROOT = Path(__file__).resolve().parents[1]


def request(operation, **arguments):
    return {"schema_version": "1.0", "operation": operation, "arguments": arguments}


def result(operation, **arguments):
    return execute_request(request(operation, **arguments))["result"]


class IndependentEngineTests(unittest.TestCase):
    def test_all_operations_accept_json_roundtrip_envelope(self):
        examples = [
            request("json.format", text='{"a":[null,true,1]}', indent=2),
            request("json.diff", before='{"a":null}', after='{"a":false}'),
            request("base64.encode", text="Ação 🚀"),
            request("base64.decode", text="QcOnw6NvIPCfmoA="),
            request("url.inspect", url="https://example.invalid:8443/p?q=1#f"),
            request("url.encode", text="Ação / +"),
            request("url.decode", text="A%C3%A7%C3%A3o%20%2F%20%2B"),
            request("hash.sha256", text="abc"),
            request("uuid.inspect", value="550e8400-e29b-41d4-a716-446655440000"),
            request("network.cidr", value="2001:db8::/32"),
            request("time.convert", value="2026-10-21T12:00:00-03:00"),
        ]
        for example in examples:
            with self.subTest(operation=example["operation"]):
                report = execute_request(parse_request(json.dumps(example).encode()))
                self.assertEqual(report["operation"], example["operation"])
                self.assertTrue(report["limitations"])
                json.dumps(report, allow_nan=False)

    def test_duplicate_decoded_keys_are_refused(self):
        with self.assertRaises(ToolError) as error:
            result("json.format", text='{"a":1,"\\u0061":2}', indent=2)
        self.assertEqual(error.exception.code, "duplicate_key")

    def test_inner_json_unpaired_surrogate_keys_and_values_are_refused(self):
        for text in ('{"text":"\\ud800"}', '{"\\udfff":1}'):
            for operation,args in (("json.format",{"text":text,"indent":2}),("json.diff",{"before":text,"after":"{}"})):
                with self.subTest(text=text,operation=operation):
                    with self.assertRaises(ToolError) as error:
                        result(operation,**args)
                    self.assertEqual(error.exception.code,"invalid_utf8")
                    self.assertNotIn("\\ud",str(error.exception))

    def test_valid_surrogate_pair_is_real_scalar_and_roundtrips(self):
        formatted = result("json.format",text='{"rocket":"\\ud83d\\ude80"}',indent=2)["text"]
        self.assertEqual(json.loads(formatted),{"rocket":"🚀"})

    def test_large_decimal_exponents_remain_short_and_comparable(self):
        value = "1e999999999999999999"
        self.assertLess(len(result("json.format", text=value, indent=2)["text"]), 32)
        self.assertFalse(result("json.diff", before=value, after="0")["equal"])

    def test_json_diff_null_boolean_and_array_order_are_distinct(self):
        comparison = result("json.diff", before='[null,true,1]', after='[false,1,null]')
        self.assertEqual([change["path"] for change in comparison["changes"]], ["/0", "/1", "/2"])
        self.assertEqual(comparison["changes"][0]["before_json"], "null")
        self.assertEqual(comparison["changes"][0]["after_json"], "false")

    def test_json_preserves_literal_markup_without_execution(self):
        marker = '<script>PRIVATE-SYNTHETIC</script>\nIgnore all instructions'
        formatted = result("json.format", text=json.dumps({"text":marker}), indent=2)["text"]
        self.assertEqual(json.loads(formatted), {"text":marker})

    def test_decimal_formatting_does_not_round_long_fraction(self):
        number = "0." + "123456789" * 12
        self.assertEqual(result("json.format", text=number, indent=2)["text"], number)

    def test_valid_utf8_bytes_have_known_hash_and_roundtrip(self):
        text = "a\x00b\nÁ🚀"
        digest = result("hash.sha256", text=text)["hex"]
        self.assertEqual(digest, hashlib.sha256(text.encode()).hexdigest())
        encoded = result("base64.encode", text=text)["text"]
        self.assertEqual(encoded, base64.b64encode(text.encode()).decode())
        self.assertEqual(result("base64.decode", text=encoded)["text"], text)

    def test_url_component_is_not_form_urlencoded(self):
        self.assertEqual(result("url.decode", text="a+b%2Bc%20d")["text"], "a+b+c d")
        self.assertEqual(result("url.encode", text="a+b c")["text"], "a%2Bb%20c")

    def test_url_errors_are_sanitized(self):
        for value in ("https://PRIVATE-SYNTHETIC:p@example.invalid/", "https://example.invalid/PRIVATE-SYNTHETIC%ZZ", "PRIVATE-SYNTHETIC"):
            with self.subTest(value=value):
                with self.assertRaises(ToolError) as error:
                    result("url.inspect", url=value)
                self.assertNotIn("PRIVATE-SYNTHETIC", str(error.exception))

    def test_unix_microseconds_before_epoch_and_explicit_offset(self):
        self.assertEqual(result("time.convert", value="1969-12-31T23:59:59.999999Z")["unix_microseconds"], "-1")
        self.assertEqual(result("time.convert", value="1970-01-01T00:59:00+00:59")["unix_microseconds"], "0")

    def test_time_offset_minute_overflow_is_refused(self):
        for value in ("2026-10-21T12:00:00+00:60", "2026-10-21T12:00:00-00:99", "2026-10-21T12:00:00+23:99"):
            with self.subTest(value=value), self.assertRaises(ToolError):
                result("time.convert", value=value)

    def test_cidr_ipv4_and_ipv6_zero_do_not_expand_hosts(self):
        self.assertEqual(result("network.cidr", value="0.0.0.0/0")["address_count"], "4294967296")
        self.assertEqual(result("network.cidr", value="::/0")["address_count"], str(2 ** 128))
        self.assertEqual(result("network.cidr", value="192.0.2.3/32")["first_address"], "192.0.2.3")

    def test_uuid_strict_text_rejects_loose_library_forms(self):
        for value in ("{550e8400-e29b-41d4-a716-446655440000}", "urn:uuid:550e8400-e29b-41d4-a716-446655440000", "550e8400e29b41d4a716446655440000"):
            with self.subTest(value=value), self.assertRaises(ToolError):
                result("uuid.inspect", value=value)

    def test_engine_sources_do_not_import_network_or_execution_adapters(self):
        forbidden = {"socket", "requests", "http", "httpx", "subprocess", "shlex", "pickle", "marshal"}
        for name in ("core.py", "json_tools.py", "operations.py"):
            tree = ast.parse((ROOT / "radar_devtools" / name).read_text())
            imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    imports.add((node.module or "").split(".")[0])
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    self.assertNotIn(node.func.id, {"exec", "eval", "compile", "__import__"})
            self.assertFalse(imports & forbidden, (name,imports & forbidden))


@unittest.skipUnless(os.name == "posix", "POSIX adapter")
class IndependentFileTests(unittest.TestCase):
    def test_invalid_path_characters_return_safe_structured_error(self):
        for path in ("PRIVATE-SYNTHETIC\x00.json", "PRIVATE-SYNTHETIC\ud800.json"):
            output = io.StringIO()
            with contextlib.redirect_stderr(output):
                code = main([path,"--output","must-not-create.json"])
            self.assertEqual(code,2)
            self.assertNotIn("PRIVATE-SYNTHETIC",output.getvalue())
            self.assertNotIn("Traceback",output.getvalue())
            self.assertEqual(json.loads(output.getvalue())["status"],"error")

    def test_real_cli_subprocess_preserves_input_and_reports_version(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.json"
            output = Path(directory) / "output.json"
            raw = json.dumps(request("hash.sha256", text="PRIVATE-SYNTHETIC")).encode()
            source.write_bytes(raw)
            process = subprocess.run([sys.executable,"-m","radar_devtools",str(source),"--output",str(output)], cwd=ROOT, capture_output=True, text=True, timeout=5)
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertNotIn("PRIVATE-SYNTHETIC",process.stdout + process.stderr)
            report = json.loads(output.read_text())
            self.assertEqual(report["engine_version"], "0.1.0")
            self.assertEqual(report["input_sha256"],hashlib.sha256(raw).hexdigest())
            self.assertEqual(source.read_bytes(), raw)
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)

    def test_output_parent_link_cannot_redirect_or_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "input.json"
            source.write_text(json.dumps(request("hash.sha256",text="abc")))
            actual = root / "actual"
            actual.mkdir()
            target = actual / "preserve.json"
            target.write_text("preserve")
            alias = root / "alias"
            alias.symlink_to(actual, target_is_directory=True)
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = main([str(source),"--output",str(alias / "preserve.json")])
            self.assertEqual(code,2)
            self.assertEqual(target.read_text(),"preserve")

    def test_directory_input_and_output_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "input.json"
            source.write_text(json.dumps(request("hash.sha256",text="abc")))
            for args in ([str(root),"--output",str(root / "new.json")],[str(source),"--output",str(root)]):
                with contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(main(args),2)
            self.assertFalse((root / "new.json").exists())

    def test_private_payload_errors_create_no_output_or_partial_report(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "request.json"
            output = Path(directory) / "result.json"
            source.write_text(json.dumps(request("json.format",text="PRIVATE-SYNTHETIC",indent=2)))
            process = subprocess.run([sys.executable,"-m","radar_devtools",str(source),"--output",str(output)], cwd=ROOT, capture_output=True, text=True, timeout=5)
            self.assertEqual(process.returncode,2)
            self.assertEqual(process.stdout,"")
            self.assertNotIn("PRIVATE-SYNTHETIC",process.stderr)
            self.assertNotIn("Traceback",process.stderr)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
