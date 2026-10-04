"""Install a wheel into fresh environments outside checkout and smoke-test it."""

import argparse
import os
import subprocess
import tempfile
import venv
from pathlib import Path

SMOKE = '''
import importlib.metadata as metadata
import importlib.resources as resources
import pathlib
import subprocess
import sys
import iddqueue
from iddqueue.schema import generate_init_sql, generate_upgrade_sql

root = pathlib.Path(sys.prefix).resolve()
assert root in pathlib.Path(iddqueue.__file__).resolve().parents, iddqueue.__file__
assert metadata.metadata("iddqueue")["License-Expression"] == "PostgreSQL"
version = metadata.version("iddqueue")
if sys.argv[2]:
    assert version == sys.argv[2], (version, sys.argv[2])
cli = root / "bin" / "iddqueue"
assert subprocess.check_output([str(cli), "--version"], text=True).strip() == version
subprocess.run([str(cli), "--help"], check=True, stdout=subprocess.DEVNULL)
for name in ("schema", "coordination", "deduplication", "control", "cancellation", "history", "scheduler"):
    assert resources.files("iddqueue").joinpath(name + ".sql").read_text().strip(), name
assert generate_init_sql("smoke", "test_").strip()
assert generate_upgrade_sql("smoke", "test_").strip()
if sys.argv[1] == "monitoring":
    import prometheus_client
    from iddqueue.metrics import PostgresQueueCollector
else:
    assert metadata.packages_distributions().get("prometheus_client") is None
print("Installed wheel verified:", version, sys.argv[1], iddqueue.__file__)
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheel", type=Path)
    parser.add_argument("--expected-version", default="", help="Require this installed metadata/CLI version")
    parser.add_argument("--quickstart", action="store_true", help="Run docs example on dedicated PostgreSQL")
    args = parser.parse_args()
    wheel = args.wheel.resolve(strict=True)
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    for profile in ("base", "monitoring"):
        with tempfile.TemporaryDirectory(prefix="iddqueue-package-") as directory:
            root = Path(directory)
            venv.create(root / "venv", with_pip=True)
            python = root / "venv/bin/python"
            target = str(wheel) + ("[monitoring]" if profile == "monitoring" else "")
            subprocess.run([str(python), "-m", "pip", "install", target], cwd=root, env=env, check=True)
            subprocess.run([str(python), "-I", "-c", SMOKE, profile, args.expected_version], cwd=root, env=env, check=True)
            if args.quickstart and profile == "base":
                example = Path(__file__).resolve().parents[1] / "docs/quickstart.py"
                subprocess.run([str(python), "-I", str(example)], cwd=root, env=env, check=True)


if __name__ == "__main__":
    main()
