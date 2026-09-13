# Changelog

Notable changes to this fork. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

This fork is maintained at https://github.com/leonid-dalin/codebuddy2openai and is not released in step with the upstream project.

## [Unreleased]

### Added

- `SECURITY.md`, with the threat model for a proxy that holds a live account credential and binds to loopback by default.
- `CONTRIBUTING.md`, covering setup, tests, end-to-end verification, and commit conventions.
- `THIRD_PARTY_NOTICES.md`, listing the declared dependencies with their licences.
- `CODE_OF_CONDUCT.md`, adapted from Contributor Covenant 3.0.
- `.env.example`, documenting every environment variable the code reads.
- `.gitattributes`, pinning line endings per file type.
- `.coderabbit.yaml`, configuring automated review with maintainability and credential-safety checks.
- `pyproject.toml`, so the project installs with `pip install .` and exposes a `workbuddy2openai` console command.
- Issue and pull request templates.

### Changed

- The project is licensed under GPL-3.0-or-later. The upstream MIT terms stay in force for the upstream code and are reproduced in `LICENSE`.
- The README is split by language: `README.md` holds the English documentation and `README.zh-CN.md` holds the Chinese documentation, each linking to the other.
- Environment variables accept the `WORKBUDDY_*` names. The `CODEBUDDY_*` names still work, so existing `.env` files keep running.

### Fixed

- `.gitignore` covered only a bare `.env`, leaving `.env.local` and similar files untracked-but-committable. It now ignores `.env.*` and keeps `.env.example`.

## [2.0.0]

### Added

- API key mode (`--direct-key`), which skips the desktop session and calls the international backend with a `CK_*` key. This is the path for WorkBuddy international accounts, where the desktop token path returns 401.
- `/health` endpoint reporting platform, Python version, and mode.

### Notes

- Streaming is always used upstream; non-streaming client requests are aggregated by the proxy.
