# Verified GitHub Actions matrix

[Workflow 41103386128](https://github.com/muratkareem/timemachine/actions/runs/41103386128) completed with **success** for
commit **639548a73f9694835b5ffd9af84f7ee953a12c3a**. All six job conclusions
were individually confirmed through GitHub's job API, and completed logs were
inspected for pytest, Ruff, mypy and build results. Run-level success was then
confirmed through GitHub's workflow API. Earlier queued/in-progress snapshots
lagged behind available completed logs; this report supersedes those observations.

| Platform | Actual Python | Tests | Coverage | Job conclusion |
| --- | --- | --- | --- | --- |
| macOS | 3.12.10 | 94 passed, 4 skipped | 83% | [success](https://github.com/muratkareem/timemachine/actions/runs/41103386128/job/124225893362) |
| macOS | 3.13.16 | 94 passed, 4 skipped | 83% | [success](https://github.com/muratkareem/timemachine/actions/runs/41103386128/job/124225893293) |
| macOS | 3.14.9 | 94 passed, 4 skipped | 83% | [success](https://github.com/muratkareem/timemachine/actions/runs/41103386128/job/124225893097) |
| Linux | 3.12.15 | 94 passed, 4 skipped | 83% | [success](https://github.com/muratkareem/timemachine/actions/runs/41103386128/job/124225893459) |
| Linux | 3.13.17 | 94 passed, 4 skipped | 83% | [success](https://github.com/muratkareem/timemachine/actions/runs/41103386128/job/124225893789) |
| Linux | 3.14.9 | 94 passed, 4 skipped | 83% | [success](https://github.com/muratkareem/timemachine/actions/runs/41103386128/job/124225893558) |

Each job ran editable development installation, Ruff, format verification, strict
mypy, pytest with coverage, wheel/sdist build, the real recovery demo, and a clean
wheel installation/CLI-help check. No live AI account or billed agent session was
required. Skips are explicit in each linked log; local skips are separately
recorded in DELIVERY.md. These results establish the tested matrix, not universal
filesystem or concurrency safety.

The final commit recording these results changes documentation only; runtime and
test files are identical to the successful 639548a matrix. No package publication,
release or version tag was created. CI emits an upstream action runtime deprecation
notice while automatically using Node 24; this did not fail any step.
