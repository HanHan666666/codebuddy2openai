# Contributing

Thanks for considering a change. This document covers the practical steps.

## Before you start

Open an issue for anything larger than a bug fix. A short description of the problem and the approach saves a rewrite. Small fixes can go straight to a pull request.

Check whether an existing issue or pull request already covers the change.

## Setting up

One dependency file covers running the proxy, and a second adds the test tooling.

```
python -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
```

On Windows the interpreter lives at `.venv\Scripts\python.exe`.

`requirements.txt` holds the runtime dependencies. `requirements-dev.txt` includes it and adds pytest.

## Running the tests

```
.venv/bin/python -m pytest
```

Write a test for every behaviour change. A fix that a test cannot observe will regress the next time somebody refactors the surrounding code.

For a change that only restructures existing code, write the test against the current code first, watch it pass, make the change, and confirm it still passes. A restructuring that also alters the wire format is not a restructuring, so split it into two changes.

## Running the proxy

```
./start.sh
```

The launcher loads `.env`, picks the project virtual environment, and installs the runtime dependencies if they are missing. The Windows launchers `start.bat` and `start-if-needed.bat` do the equivalent.

Verify a change end to end rather than only through the test suite. Start the proxy and send it a real completion request:

```
curl -X POST http://127.0.0.1:8787/v1/chat/completions \
  -H "Authorization: Bearer $YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"hy3","messages":[{"role":"user","content":"ping"}]}'
```

A passing unit test confirms the code compiles and the logic holds. It does not confirm the upstream service still answers.

## Code style

- Match the surrounding code. The project has few files and a consistent shape; keep it that way.
- No comments. A comment earns its place only when it records something the code cannot express: a non-obvious runtime behaviour, a deliberate ordering, or a hazard with no visible marker. If the line below already says it, delete the comment.
- Keep functions small and put logic in the module that owns the concept.
- Prefer plain code over indirection. A helper that only forwards its arguments adds a layer without adding clarity, so inline it.

## Commit messages

Use Conventional Commits: `<type>(<optional scope>): <description>`. The types in use are feat, fix, refactor, perf, style, test, docs, build, ops, and chore.

Write the description in the imperative present tense, with no leading capital and no trailing period. For example:

```
feat: add API key mode for WorkBuddy international accounts
fix: read the credential file when the CLI is absent
```

Keep one logical change per commit. Open a separate pull request for unrelated work.

The body explains why the change exists. Two sentences is usually enough, and the diff already shows what changed.

## Pull requests

1. Branch from the default branch.
2. Make the change, with tests.
3. Run the full suite and confirm it passes.
4. Verify the change against a running proxy if it touches request handling, streaming, or credential resolution.
5. Describe the change and its motivation in the pull request body.

Say what you verified and how. A note that you exercised the real endpoint carries more weight than a note that the tests pass.

## Reporting bugs

Include the platform, the Python version, the proxy startup output, and the smallest set of steps that reproduces the problem. If the proxy returned an error, include the response body and the matching lines from the log.

Redact your API key and any token from anything you paste.

## Security issues

Do not open a public issue. Follow [SECURITY.md](SECURITY.md).

## Code of conduct

Participation is covered by [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
