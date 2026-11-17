"""PyPI/CLI source contract, offline; never authorize training or clinical use."""
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
import json
import subprocess
import sys
import unittest

from muhu.cli import VERSION, inspect_fields, main


class PackageCliTests(unittest.TestCase):
    def test_valid_reviewable_is_not_qualified(self):
        data = inspect_fields(
            source_bound="true",
            sample_n=32,
            age_days=2,
            independent_check="true",
            contradiction="false",
        )
        self.assertEqual(data["state"], "REVIEWABLE")
        self.assertFalse(data["model_trained"])
        self.assertFalse(data["training_authorized"])
        self.assertFalse(data["clinical_qualified"])
        self.assertEqual(data["scientific_validity"], "NOT_ASSESSED")
        self.assertTrue(data["not_a_digital_signature"])

    def test_missing_input_is_unavailable_and_does_not_infer(self):
        data = inspect_fields(
            source_bound="true",
            sample_n=32,
            age_days=None,
            independent_check=None,
            contradiction="false",
        )
        self.assertEqual(data["state"], "UNAVAILABLE")
        self.assertEqual(data["missing_fields"], ["age_days", "independent_check"])
        self.assertFalse(data["training_authorized"])

    def test_zero_denominator_is_blocked(self):
        data = inspect_fields(
            source_bound="true",
            sample_n=0,
            age_days=0,
            independent_check="true",
            contradiction="false",
        )
        self.assertEqual(data["state"], "BLOCKED")
        self.assertFalse(data["training_authorized"])

    def test_conflict_preempts_staleness(self):
        data = inspect_fields(
            source_bound="true",
            sample_n=12,
            age_days=45,
            independent_check="true",
            contradiction="true",
        )
        self.assertEqual(data["state"], "CONFLICT")

    def test_negative_values_fail_without_success_claim(self):
        with self.assertRaises(ValueError):
            inspect_fields(
                source_bound="true",
                sample_n=3,
                age_days=-1,
                independent_check="true",
                contradiction="false",
            )

    def test_cli_json_result(self):
        stream = StringIO()
        with redirect_stdout(stream):
            rc = main(
                [
                    "--source-bound", "true",
                    "--sample-n", "20",
                    "--age-days", "7",
                    "--independent-check", "true",
                    "--contradiction", "false",
                ]
            )
        record = json.loads(stream.getvalue())
        self.assertEqual(rc, 0)
        self.assertEqual(record["state"], "REVIEWABLE")
        self.assertFalse(record["training_authorized"])

    def test_cli_missing_is_not_zero(self):
        stream = StringIO()
        with redirect_stdout(stream):
            rc = main(["--source-bound", "true"])
        obj = json.loads(stream.getvalue())
        self.assertEqual(rc, 0)
        self.assertEqual(obj["state"], "UNAVAILABLE")
        self.assertEqual(len(obj["missing_fields"]), 4)

    def test_cli_invalid_fails_closed(self):
        stream = StringIO()
        with redirect_stderr(stream):
            with self.assertRaises(SystemExit) as exc:
                main(
                    [
                        "--source-bound", "true", "--sample-n", "-1",
                        "--age-days", "2", "--independent-check", "true",
                        "--contradiction", "false",
                    ]
                )
        self.assertEqual(exc.exception.code, 2)
        self.assertIn("Invalid bounded synthetic evidence", stream.getvalue())

    def test_package_version_is_explicit(self):
        self.assertEqual(VERSION, "0.1.0")

    def test_module_entrypoint_runs_offline(self):
        process = subprocess.run(
            [sys.executable, "-B", "-m", "muhu.cli", "--source-bound", "false"],
            capture_output=True, text=True, timeout=10, check=True
        )
        self.assertEqual(json.loads(process.stdout)["state"], "UNAVAILABLE")
        self.assertNotIn("secret", process.stdout.lower())


if __name__ == "__main__":
    unittest.main()
