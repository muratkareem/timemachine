"""Build clean committed source twice and reject non-reproducible artifacts. No upload."""

import argparse
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from importlib.metadata import version
from pathlib import Path


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("release-artifacts"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]

    def git(*arguments):
        return subprocess.check_output(["git", *arguments], cwd=root).decode().strip()

    if git("status", "--porcelain"):
        parser.error("Commit verified changes first; release source must be clean")
    if args.output.exists():
        parser.error("Output must be a new directory")
    commit = git("rev-parse", "HEAD")
    epoch = git("show", "-s", "--format=%ct", "HEAD")
    source = subprocess.check_output(["git", "archive", "HEAD"], cwd=root)
    env = {**os.environ, "SOURCE_DATE_EPOCH": epoch, "PYTHONHASHSEED": "0"}
    with tempfile.TemporaryDirectory(prefix="timemachine-build-") as temporary:
        outputs = []
        for index in range(2):
            stage = Path(temporary) / str(index)
            stage.mkdir()
            with tarfile.open(fileobj=io.BytesIO(source)) as archive:
                archive.extractall(stage, filter="data")
            destination = stage / "dist"
            subprocess.run(
                [sys.executable, "-m", "build", "--no-isolation", "--outdir", str(destination)],
                cwd=stage,
                env=env,
                check=True,
            )
            outputs.append({p.name: digest(p) for p in sorted(destination.iterdir())})
        if outputs[0] != outputs[1] or len(outputs[0]) != 2:
            raise SystemExit("Builds differ or artifacts are missing; nothing released")
        args.output.mkdir(parents=True)
        for name in outputs[0]:
            shutil.copyfile(Path(temporary) / "0" / "dist" / name, args.output / name)
        (args.output / "SHA256SUMS").write_text(
            "".join(f"{sha}  {name}\n" for name, sha in outputs[0].items())
        )
        (args.output / "BUILD.json").write_text(
            json.dumps(
                {
                    "commit": commit,
                    "source_date_epoch": int(epoch),
                    "python": sys.version.split()[0],
                    "build_tools": {p: version(p) for p in ("build", "hatchling")},
                    "artifacts": outputs[0],
                    "reproduced": True,
                    "publication": "not performed by this script",
                },
                indent=2,
            )
            + "\n"
        )
    print(json.dumps({"output": str(args.output.resolve()), "commit": commit, "reproduced": True}))


if __name__ == "__main__":
    main()
