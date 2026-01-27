import json
import subprocess
import tempfile
import unittest
from pathlib import Path


class RunBatteryCliTest(unittest.TestCase):
    def test_cli_writes_run_manifest(self) -> None:
        spec = {
            "logic": "equational",
            "operations": [],
            "max_vars": 1,
            "max_term_size": 1,
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            spec_path = Path(tmpdir) / "spec.json"
            spec_path.write_text(json.dumps(spec), encoding="utf-8")
            output_dir = Path(tmpdir) / "run"
            result = subprocess.run(
                [
                    "python3",
                    "-m",
                    "axlab.cli.run_battery",
                    "--spec",
                    str(spec_path),
                    "--output",
                    str(output_dir),
                    "--limit",
                    "1",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0)
            self.assertTrue((output_dir / "run.json").exists())


if __name__ == "__main__":
    unittest.main()
