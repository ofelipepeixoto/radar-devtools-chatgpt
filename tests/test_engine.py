"""Synthetic behavior checks for the strict offline request boundary."""

import json
import unittest
from unittest.mock import patch

from radar_devtools import ToolError, execute_request, parse_request


def run(operation, **arguments):
    return execute_request({"schema_version": "1.0", "operation": operation, "arguments": arguments})


class ErrorAssertions:
    def assert_code(self, code, callable_, *args):
        with self.assertRaises(ToolError) as context:
            callable_(*args)
        self.assertEqual(context.exception.code, code)
        self.assertNotIn("PRIVATE-SYNTHETIC", str(context.exception))


class BoundaryTests(ErrorAssertions, unittest.TestCase):
    def test_roundtrip_envelope_and_explicit_limits(self):
        request = parse_request(b'{"schema_version":"1.0","operation":"json.format","arguments":{"text":"{}","indent":2}}')
        result = execute_request(request)
        self.assertEqual(result["result"], {"text": "{}"})
        self.assertEqual(result["schema_version"], "1.0")
        self.assertTrue(result["limitations"])

    def test_duplicate_outer_key_rejected(self):
        self.assert_code("duplicate_key", parse_request, b'{"operation":"a","operation":"b"}')

    def test_duplicate_argument_key_rejected(self):
        self.assert_code("duplicate_key", parse_request, b'{"arguments":{"text":"a","text":"b"}}')

    def test_invalid_utf8(self):
        self.assert_code("invalid_utf8", parse_request, b'\xff')

    def test_input_requires_bytes(self):
        self.assert_code("invalid_input", parse_request, "{}")

    def test_input_size_bound(self):
        self.assert_code("input_limit", parse_request, b" " * (256 * 1024 + 1))

    def test_text_bound_counts_utf8_bytes(self):
        self.assert_code("text_limit", lambda: run("hash.sha256", text="é" * 32769))
        self.assertIn("hex", run("hash.sha256", text="é" * 32768)["result"])

    def test_unicode_surrogate_is_safe_error(self):
        self.assert_code("invalid_utf8", lambda: run("hash.sha256", text="\ud800"))

    def test_extra_missing_and_wrong_types(self):
        cases = [
            {"schema_version": "1.0", "operation": "hash.sha256", "arguments": {"text": "x"}, "extra": 1},
            {"operation": "hash.sha256", "arguments": {}},
            [], None,
        ]
        for value in cases:
            with self.subTest(value=value):
                self.assert_code("invalid_request", execute_request, value)
        self.assert_code("invalid_arguments", lambda: run("hash.sha256", text=True))
        self.assert_code("invalid_arguments", lambda: run("hash.sha256", text="x", extra="x"))

    def test_unknown_operation_and_schema(self):
        self.assert_code("unknown_operation", lambda: run("shell.run", text="PRIVATE-SYNTHETIC"))
        self.assert_code("schema_version", execute_request, {"schema_version": "2.0", "operation": "hash.sha256", "arguments": {"text": "x"}})

    def test_errors_do_not_echo_bad_content(self):
        self.assert_code("invalid_json", lambda: run("json.format", text="PRIVATE-SYNTHETIC", indent=2))

    def test_output_limit(self):
        with patch("radar_devtools.core.MAX_OUTPUT_BYTES", 10):
            self.assert_code("output_limit", lambda: run("hash.sha256", text="x"))


class JSONTests(ErrorAssertions, unittest.TestCase):
    def test_format_keeps_decimal_digits(self):
        report = run("json.format", text='{"n":0.12345678901234567890123456789}', indent=2)
        self.assertIn("0.12345678901234567890123456789", report["result"]["text"])

    def test_format_escapes_strings_and_preserves_unicode(self):
        source = '{"text":"Ação\\n\\\"x\\\"","items":[1,null,true]}'
        formatted = run("json.format", text=source, indent=4)["result"]["text"]
        self.assertEqual(json.loads(formatted), json.loads(source))
        self.assertIn("\n    ", formatted)

    def test_json_number_limits_and_nonfinite(self):
        self.assert_code("number_limit", lambda: run("json.format", text="1" * 129, indent=2))
        self.assert_code("number_limit", lambda: run("json.format", text="1e999999999999999999999999999", indent=2))
        for value in ("NaN", "Infinity", "-Infinity"):
            self.assert_code("invalid_json", lambda: run("json.format", text=value, indent=2))

    def test_exponent_does_not_expand_output(self):
        result = run("json.format", text="1e1000000", indent=2)["result"]["text"]
        self.assertEqual(result, "1E+1000000")

    def test_duplicate_inner_keys(self):
        self.assert_code("duplicate_key", lambda: run("json.format", text='{"a":1,"a":2}', indent=2))

    def test_deep_or_many_nodes_rejected(self):
        self.assert_code("structure_limit", lambda: run("json.format", text="[" * 33 + "0" + "]" * 33, indent=2))
        self.assert_code("structure_limit", lambda: run("json.format", text="[" + ",".join(["0"] * 10001) + "]", indent=2))

    def test_indent_is_not_bool_or_float(self):
        for value in (True, 2.0, 3, "2"):
            self.assert_code("invalid_arguments", lambda: run("json.format", text="{}", indent=value))
        request = parse_request(b'{"schema_version":"1.0","operation":"json.format","arguments":{"text":"{}","indent":2.0}}')
        self.assert_code("invalid_arguments", execute_request, request)

    def test_diff_boolean_is_not_number(self):
        report = run("json.diff", before='{"x":true}', after='{"x":1}')["result"]
        self.assertFalse(report["equal"])
        self.assertEqual(report["changes"][0], {"kind": "changed", "path": "/x", "before_json": "true", "after_json": "1"})

    def test_diff_ignores_object_order_and_numeric_lexeme(self):
        result = run("json.diff", before='{"b":2,"a":1}', after='{"a":1.0,"b":2}')["result"]
        self.assertEqual(result, {"equal": True, "changes": []})

    def test_diff_array_and_json_pointer_escaping(self):
        result = run("json.diff", before='{"a/b~":[1,2],"gone":null}', after='{"a/b~":[3],"new":false}')["result"]
        self.assertEqual([v["path"] for v in result["changes"]], ["/gone", "/new", "/a~1b~0/0", "/a~1b~0/1"])
        self.assertEqual(result["changes"][-1]["kind"], "removed")

    def test_diff_root_change(self):
        result = run("json.diff", before="null", after="[]")["result"]
        self.assertEqual(result["changes"][0]["path"], "")

    def test_diff_limit_is_error_not_truncation(self):
        self.assert_code("diff_limit", lambda: run("json.diff", before="[]", after=json.dumps(list(range(201)))))


class TransformTests(ErrorAssertions, unittest.TestCase):
    def test_base64_unicode_roundtrip(self):
        encoded = run("base64.encode", text="Ação 🚀")["result"]["text"]
        self.assertEqual(encoded, "QcOnw6NvIPCfmoA=")
        self.assertEqual(run("base64.decode", text=encoded)["result"]["text"], "Ação 🚀")

    def test_base64_canonical_and_utf8(self):
        for bad in ("YQ", "YQ===", "YR==", "YQ==\n", "_w==", "/w==", "é"):
            self.assert_code("invalid_base64", lambda: run("base64.decode", text=bad))

    def test_url_component_roundtrip_and_plus(self):
        encoded = run("url.encode", text="Ação /+?")["result"]["text"]
        self.assertEqual(encoded, "A%C3%A7%C3%A3o%20%2F%2B%3F")
        self.assertEqual(run("url.decode", text=encoded)["result"]["text"], "Ação /+?")
        self.assertEqual(run("url.decode", text="a+b")["result"]["text"], "a+b")

    def test_bad_url_encoding(self):
        self.assert_code("invalid_url_encoding", lambda: run("url.decode", text="a%2"))
        self.assert_code("invalid_utf8", lambda: run("url.decode", text="%FF"))

    def test_hash_known_vector(self):
        self.assertEqual(run("hash.sha256", text="abc")["result"]["hex"], "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")

    def test_url_inspection_never_requests_network(self):
        with patch("socket.socket", side_effect=AssertionError("network used")):
            result = run("url.inspect", url="https://example.invalid:8443/a?q=x#f")["result"]
        self.assertEqual(result, {"scheme": "https", "host": "example.invalid", "port": 8443, "path": "/a", "query": "q=x", "fragment": "f", "network_accessed": False})

    def test_url_credentials_are_rejected(self):
        self.assert_code("url_credentials", lambda: run("url.inspect", url="https://PRIVATE-SYNTHETIC:pass@example.invalid/"))

    def test_url_parser_rejects_ambiguous_values(self):
        bad_urls = ["javascript:alert(1)", "//example.invalid", "https://example.invalid:99999", "https://a\\b/", "https://a/\n", "https://a b/", "https://a/%QQ", "https://-bad.invalid/", "https://a..b/", "https://[bad]/"]
        for value in bad_urls:
            with self.subTest(value=value):
                with self.assertRaises(ToolError):
                    run("url.inspect", url=value)

    def test_url_ipv6_and_idna(self):
        self.assertEqual(run("url.inspect", url="https://[2001:db8::1]/")["result"]["host"], "2001:db8::1")
        self.assertEqual(run("url.inspect", url="https://ação.example/")["result"]["host"], "ação.example")

    def test_uuid_canonical_variant_version(self):
        result = run("uuid.inspect", value="550e8400-e29b-41d4-a716-446655440000")["result"]
        self.assertEqual(result["version"], 4)
        for bad in ("550E8400-E29B-41D4-A716-446655440000", "00000000-0000-0000-0000-000000000000", "bad"):
            self.assert_code("invalid_uuid", lambda: run("uuid.inspect", value=bad))

    def test_cidr_has_no_host_expansion(self):
        result = run("network.cidr", value="2001:db8::/32")["result"]
        self.assertEqual(result["address_count"], str(2 ** 96))
        self.assertEqual(result["last_address"], "2001:db8:ffff:ffff:ffff:ffff:ffff:ffff")

    def test_cidr_strict_network(self):
        self.assert_code("invalid_cidr", lambda: run("network.cidr", value="192.0.2.1/24"))
        self.assert_code("invalid_cidr", lambda: run("network.cidr", value="192.0.2.1"))
        self.assertEqual(run("network.cidr", value="192.0.2.0/24")["result"]["address_count"], "256")

    def test_time_normalizes_offset_without_float_loss(self):
        result = run("time.convert", value="1970-01-01T00:00:00.000001Z")["result"]
        self.assertEqual(result["unix_microseconds"], "1")
        result = run("time.convert", value="2026-10-21T12:30:00-03:00")["result"]
        self.assertEqual(result["utc"], "2026-10-21T15:30:00Z")

    def test_time_rejects_naive_invalid_and_ambiguous_separator(self):
        for bad in ("2026-10-21", "2026-10-21T12:30:00", "2026-10-21X12:30:00Z", "2026-02-30T00:00:00Z", "2026-10-21T12:30:60Z", "2026-10-21T12:30:00+00:99", "2026-10-21T12:30:00+24:00"):
            self.assert_code("invalid_time", lambda: run("time.convert", value=bad))


if __name__ == "__main__":
    unittest.main()
