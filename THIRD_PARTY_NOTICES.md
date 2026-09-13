# Third-party notices

This project depends on the packages below. They are not vendored: install the project's dependency file and your package manager resolves each one under its own licence.

## Runtime dependencies

### FastAPI

- Licence: MIT
- Use: HTTP routing, request validation, and the ASGI application.
- Source: https://github.com/fastapi/fastapi

### Uvicorn

- Licence: BSD 3-Clause
- Use: ASGI server that runs the application.
- Source: https://github.com/encode/uvicorn

The `uvicorn[standard]` extra pulls in further packages, including `httptools` (MIT), `uvloop` (MIT, not installed on Windows), `watchfiles` (MIT), `websockets` (BSD 3-Clause), `python-dotenv` (BSD 3-Clause), `PyYAML` (MIT), and `colorama` (BSD 3-Clause, Windows only). Each carries its own licence, and the `uvicorn[standard]` dependency list is the authoritative source.

### HTTPX

- Licence: BSD 3-Clause
- Use: HTTP client for requests to the upstream service.
- Source: https://github.com/encode/httpx

HTTPX depends on `httpcore` (BSD 3-Clause), `h11` (MIT), `certifi` (MPL 2.0), and `idna` (BSD 3-Clause).

## Development dependencies

### pytest

- Licence: MIT
- Use: test runner.
- Source: https://github.com/pytest-dev/pytest

pytest depends on `iniconfig` (MIT), `packaging` (Apache 2.0 or BSD 2-Clause), and `pluggy` (MIT).

### Starlette TestClient

- Licence: BSD 3-Clause
- Use: exercised through FastAPI, which re-exports it. It requires HTTPX.
- Source: https://github.com/encode/starlette

## Standard library

Several modules from the Python standard library are used, including `argparse`, `json`, `os`, `pathlib`, `re`, `sys`, `threading`, and `time`. They ship with Python under the Python Software Foundation Licence, version 2.

## Documents

### Contributor Covenant 3.0

`CODE_OF_CONDUCT.md` is adapted from the Contributor Covenant, version 3.0, available at https://www.contributor-covenant.org/version/3/0/

The Contributor Covenant is stewarded by the Organization for Ethical Source and licensed under Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0). The document's own attribution section reproduces this notice.

## Upstream project

This repository is a fork of https://github.com/HanHan666666/codebuddy2openai, which is licensed under the MIT Licence, copyright (c) 2026 HanHan666666.

The original MIT terms are preserved in [LICENSE](LICENSE) alongside this fork's own licence. See that file for the split.

## Keeping this list current

This list covers the declared dependencies. It does not enumerate every transitive package with the exact resolved version, because those versions depend on when you install.

To generate a complete inventory including transitive dependencies and their resolved versions, install the development requirements and run a licence report, for example:

```
.venv/bin/python -m pip install pip-licenses
.venv/bin/python -m pip-licenses --format=markdown --with-urls --with-license-file --with-description
```

Regenerate that report when a dependency is added, removed, or upgraded.
