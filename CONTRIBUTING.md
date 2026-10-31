# Contributing

Use Python 3.12+ on macOS/Linux. Install `pip install -e '.[dev]'` in a venv.
Read AGENTS.md and docs/SAFETY.md before changing storage or restore behavior.

```sh
ruff format --check src tests examples scripts
ruff check src tests examples scripts
mypy
pytest --cov=timemachine --cov-report=term-missing
python -m build --no-isolation
python examples/demo.py
python scripts/acceptance.py
```

Tests must only mutate disposable tmp_path/TemporaryDirectory projects, never a
real developer directory. Include fault-injection and conflict tests for changes
to restore, journal, storage or retention. Preserve failing evidence and recovery
artifacts. Do not relax safety checks to make a test pass. Document unsupported
metadata and platforms honestly. No live agent/API/billing required for tests;
installed agent `--help` smoke tests are optional and skip otherwise.

Use cohesive Conventional Commits and explain the behavior, safety impact and
validation in pull requests. Keep core services independent of Typer/Textual.
Unknown storage versions fail closed; format changes need explicit migration
plans. Preserve the MIT license and existing history. Do not publish packages,
tags or releases without maintainer authorization.

Large performance fixtures are opt-in: `python scripts/scale_benchmark.py --files 1000`.
Do not extrapolate small/warm-cache runs into throughput guarantees. Release tooling
is pinned separately in requirements/release.txt; docs/RELEASE.md defines the clean
double-build, installation, publication and Homebrew maintenance gates. CI preserves
candidate build artifacts without publishing. See docs/PLATFORMS.md for real support.
