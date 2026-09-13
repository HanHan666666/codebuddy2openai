# Security policy

## What this project handles

This is a local proxy. It reads the credentials that the CodeBuddy / WorkBuddy desktop client already stored on your machine, then re-exposes that account as an OpenAI-compatible HTTP API. Two consequences shape this policy:

- The proxy holds a live session credential for a paid account. Anyone who can reach the listening port can spend that account's quota.
- The default bind address is `127.0.0.1`. Changing it to a routable address exposes the account to your network, and this project has no user database, no roles, and no per-client rate limit.

## Supported versions

Only the latest commit on the default branch is supported. This is a small project without long-lived release branches, so fixes land on the default branch and nowhere else.

## Reporting a vulnerability

Email **infoleonid@protonmail.com**. Do not open a public issue for a security problem.

Include what you have: the version or commit you tested, the platform, a description of the impact, and the smallest reproduction you can manage. A proof of concept helps but is not required to file.

You can expect an acknowledgement within a few days. This is a hobby project maintained by one person, so please allow reasonable time before chasing a reply.

## In scope

- Credential leakage: the session token or API key reaching process listings, log files, error responses, or crash output.
- Authentication bypass on the local API, including any route that answers before the key check.
- Path traversal or arbitrary file read through the credential-loading code.
- Request smuggling or header injection in the translation between the OpenAI request shape and the upstream one.
- Denial of service that the default configuration does not already accept as a local-only tradeoff.

## Out of scope

- Anything that requires the attacker to already read files as your user. Local filesystem access to the credential store is the threat model's starting point, not a finding.
- Exposure caused by rebinding to a routable address, or by putting the proxy behind a reverse proxy without authentication. The README warns about the default bind; changing it moves the risk onto your own network.
- Account suspension or quota exhaustion caused by your own use of the upstream service.
- Vulnerabilities in the upstream desktop client or the upstream API, reported to the wrong project.
- Missing rate limits, request size caps, or TLS on the local listener. A loopback-only listener serves one user.

## Hardening checklist

If you run this beyond your own machine:

1. Keep the bind address on `127.0.0.1` unless you have a specific reason.
2. Set a strong `--api-key` value. An empty key disables the check, and the proxy logs a warning when it starts that way.
3. Keep the key out of the command line, where process listings expose it. Read it from the environment or from `.env` instead.
4. Keep `.env` out of version control. The repository's ignore rules already cover it; check before you commit.
5. Terminate TLS and add authentication in front of the proxy if you reach it over a network.
