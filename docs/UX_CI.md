# UX overhaul — verified CI

[Workflow 41125851544](https://github.com/muratkareem/timemachine/actions/runs/41125851544) completed with **success** for
**8d1b47946a8952aa7dbbba3e52f789c64f18ce89**. All six job conclusions and
completed logs were inspected. Each passed lint/format/type checks, full pytest,
wheel/sdist build, real CLI demo, isolated wheel installation with the TUI extra,
and the installed wheel's CLI demo and actual Textual screenshot export.

| Platform | Actual Python | Pytest | Statement coverage | Job |
| --- | --- | --- | --- | --- |
| macOS | 3.12.10 | 110 passed, 4 skipped | 84% | [success](https://github.com/muratkareem/timemachine/actions/runs/41125851544/job/124304048663) |
| macOS | 3.13.16 | 110 passed, 4 skipped | 84% | [success](https://github.com/muratkareem/timemachine/actions/runs/41125851544/job/124304048752) |
| macOS | 3.14.8 | 110 passed, 4 skipped | 84% | [success](https://github.com/muratkareem/timemachine/actions/runs/41125851544/job/124304048325) |
| Linux | 3.12.15 | 110 passed, 4 skipped | 84% | [success](https://github.com/muratkareem/timemachine/actions/runs/41125851544/job/124304048792) |
| Linux | 3.13.17 | 110 passed, 4 skipped | 84% | [success](https://github.com/muratkareem/timemachine/actions/runs/41125851544/job/124304048627) |
| Linux | 3.14.9 | 110 passed, 4 skipped | 84% | [success](https://github.com/muratkareem/timemachine/actions/runs/41125851544/job/124304048797) |

An intermediate run at ece12c5 failed the formatter check before tests because of
one dialog-copy line wrap. 8d1b479 corrected it; the final workflow is fully green.
No tests were suppressed or removed. The final evidence commit changes docs only;
source, tests, dependencies and workflow remain identical to the successful run.

Local results: 110 passed, 4 skipped, 84% coverage (2094 statements, 330 missed),
18.59 s; 44 files format-clean, 24 source files type-clean. The local skips are
three absent optional agents and the sandbox-stripped setuid case; direct mode
validation passes. CI skip details are explicit in each job log.

No release, version tag or PyPI publication was created. Original storage/recovery
and Git guarantees remain unchanged. See UX_DELIVERY.md for compatibility,
installation, benchmark conditions, screenshots, commit ledger and limitations.
