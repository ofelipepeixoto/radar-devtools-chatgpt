import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest

from radar_devtools.cli import main


@unittest.skipUnless(os.name == "posix", "POSIX file adapter")
class FileContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.input = self.root / "request.json"
        self.output = self.root / "result.json"
        self.request = b'{"schema_version":"1.0","operation":"hash.sha256","arguments":{"text":"abc"}}'
        self.input.write_bytes(self.request)

    def run_cli(self, source=None, destination=None):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = main([str(source or self.input), "--output", str(destination or self.output)])
        return code, stdout.getvalue(), stderr.getvalue()

    def test_real_report_input_preserved_digest_and_mode(self):
        code, stdout, stderr = self.run_cli()
        self.assertEqual((code, stderr), (0, ""))
        report = json.loads(self.output.read_text())
        self.assertEqual(report["input_sha256"], hashlib.sha256(self.request).hexdigest())
        self.assertEqual(self.input.read_bytes(), self.request)
        self.assertEqual(self.output.stat().st_mode & 0o777, 0o600)
        self.assertNotIn('"text"', stdout)

    def test_existing_output_never_overwritten(self):
        self.output.write_bytes(b"preserve")
        self.assertEqual(self.run_cli()[0], 2)
        self.assertEqual(self.output.read_bytes(), b"preserve")

    def test_same_path_never_overwrites_input(self):
        self.assertEqual(self.run_cli(destination=self.input)[0], 2)
        self.assertEqual(self.input.read_bytes(), self.request)

    def test_input_symlink_refused(self):
        link = self.root / "link"
        link.symlink_to(self.input)
        self.assertEqual(self.run_cli(source=link)[0], 2)
        self.assertFalse(self.output.exists())

    def test_output_symlink_refused(self):
        self.output.symlink_to(self.input)
        self.assertEqual(self.run_cli()[0], 2)
        self.assertEqual(self.input.read_bytes(), self.request)

    def test_parent_symlink_refused_for_input_and_output(self):
        link = self.root / "alias"
        link.symlink_to(self.root, target_is_directory=True)
        self.assertEqual(self.run_cli(source=link / self.input.name)[0], 2)
        self.assertEqual(self.run_cli(destination=link / self.output.name)[0], 2)
        self.assertFalse(self.output.exists())

    def test_fifo_rejected_without_wait(self):
        fifo = self.root / "fifo"
        os.mkfifo(fifo)
        self.assertEqual(self.run_cli(source=fifo)[0], 2)

    def test_failed_validation_no_report_no_input_in_error(self):
        marker = "DADO_FICTICIO_PRIVADO_123"
        self.input.write_text('{"schema_version":"1.0","operation":"' + marker + '","arguments":{}}')
        code, stdout, stderr = self.run_cli()
        self.assertEqual(code, 2)
        self.assertEqual(stdout, "")
        self.assertNotIn(marker, stderr)
        self.assertFalse(self.output.exists())

    def test_file_limit_is_bounded(self):
        self.input.write_bytes(b" " * (256 * 1024 + 1))
        self.assertEqual(self.run_cli()[0], 2)
        self.assertFalse(self.output.exists())

    def test_parent_traversal_refused(self):
        self.assertEqual(self.run_cli(source=self.root / ".." / self.root.name / self.input.name)[0], 2)


if __name__ == "__main__":
    unittest.main()
