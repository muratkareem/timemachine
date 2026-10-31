# Dependency inventory

TimeMachine remains MIT licensed. Runtime dependencies are declared in
pyproject.toml, with Textual optional. The following versions/licenses were read
from installed package metadata in the isolated Homebrew/release resolution
on 2026-10-31. They describe this tested resolution; broad package constraints may
resolve differently later. Original dependency notices remain in their installed
wheel `.dist-info/licenses` or equivalent metadata directories.

| Dependency | Tested version | Declared license |
| --- | --- | --- |
| annotated-doc | 0.0.5 | MIT |
| linkify-it-py | 2.2.0 | MIT |
| markdown-it-py | 4.2.0 | MIT |
| mdit-py-plugins | 0.6.1 | MIT |
| mdurl | 0.1.2 | MIT |
| platformdirs | 4.14.0 | MIT |
| Pygments | 2.21.0 | BSD-2-Clause |
| rich | 14.3.4 | MIT |
| shellingham | 1.5.4 | ISC |
| textual | 6.12.0 | MIT |
| typer | 0.27.3 | MIT |
| typing_extensions | 4.16.0 | PSF-2.0 |

Build tools, included in the Homebrew build environment but not required by wheel
end users: build 1.6.1 (MIT), hatchling 1.33.0 (MIT), packaging 26.3
(Apache-2.0 OR BSD-2-Clause), pathspec 1.1.1 (MPL-2.0), pluggy 1.7.0 (MIT),
pyproject_hooks 1.3.3 (MIT), tomlkit 0.15.2 (MIT), trove-classifiers
2026.9.21.13 (Apache). Homebrew's Python and its system dependencies retain their
own notices. No dependency source was relicensed or copied into TimeMachine source.

`requirements/release.txt` pins build tools. `requirements/homebrew-resources.json`
pins exact public wheel URLs and SHA-256 for the formula. The project's wheel and
sdist use normal dependency declarations; they do not vendor these wheels or
require test/type/lint tools at runtime. Pipx and Twine are external validation
tools, not product dependencies. This is an inventory, not a vulnerability scan
or legal certification.
