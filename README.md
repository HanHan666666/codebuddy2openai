# workbuddy2openai

> Turn your **CodeBuddy / WorkBuddy (Tencent coding assistant)** subscription into a standard **OpenAI-compatible API**, so you can reuse it from any OpenAI-protocol client (ZCode, Cherry Studio, NextChat, LobeChat, Open WebUI, and others).

> ⚠️ **Codex CLI note:** newer Codex CLI dropped `wire_api = "chat"` and only supports the `completions` format, so **this tool cannot be used with Codex CLI**. Use any OpenAI-compatible client instead.

[English](README.md) · [中文文档](README.zh-CN.md)

### ✨ Features

- 🔄 **OpenAI-compatible**: standard `/v1/chat/completions` (streaming SSE), `/v1/models`, `/health`.
- 🪶 **Single-file & minimal**: core is one `converter.py`.
- 🔐 **Zero-auth hassle**: calls your locally-logged-in `codebuddy` CLI; reuses the desktop login session.
- 🖥️ **Cross-platform**: auto-locates CLI & auth on macOS / Windows / Linux.
- 🛡️ **Safe**: listens on `127.0.0.1` only; disables all built-in CLI tools for pure chat.

### 🚀 Quick Start

```bash
git clone https://github.com/HanHan666666/codebuddy2openai.git
cd codebuddy2openai
pip install -r requirements.txt
python3 converter.py
```

Then point your OpenAI-compatible client at `http://127.0.0.1:8787/v1` (API base), leave the key blank unless you started the converter with `--api-key`. Note: Codex CLI is **not** supported (it dropped `wire_api = "chat"`); use ZCode, Cherry Studio, or any OpenAI-compatible client instead.

### Running the tests

```bash
pip install -r requirements-dev.txt
pytest
```

### API key mode (`--direct-key`)

WorkBuddy international accounts (Keycloak realm on `www.workbuddy.ai`) get 401s from the desktop-token path: the token shape does not match the backend the converter calls, and refresh fails with `invalid_grant`. If that is your situation, skip the desktop session entirely and use a **CK_\* API key** instead (generate one at [codebuddy.ai/profile/keys](https://www.codebuddy.ai/profile/keys); the CLI documents the same key as `CODEBUDDY_API_KEY`).

```bash
python3 converter.py --direct-key ck_yourkeyhere
# or: export CODEBUDDY_DIRECT_KEY=ck_yourkeyhere
```

What changes in this mode:

- No desktop app or login needed; the key is sent as a plain `Authorization: Bearer` header to `https://www.codebuddy.ai/v2/chat/completions`. Works headless (servers, containers, NAS).
- `/v1/models` lists the international catalog, verified live: `auto`, `hy3`, `glm-5.3/5.2/5.1/5v-turbo`, `minimax-m3`, `kimi-k3/k2.7/k2.6`, `deepseek-v4-pro/flash`, `gpt-5.6-luna`, `gpt-5.6-terra`, `gpt-5.6-sol`, `gemini-3.1-pro`.
- The startup preflight (which expects a desktop session) is skipped.

Backend quirks worth knowing (they produce confusing errors if you meet them blind):

- Requests must use `stream: true`; non-stream calls are rejected with error `11101`. The converter always streams upstream and aggregates when the client asked for non-streaming, so this only matters for raw calls.
- The first message must have role `system` (error `11128`). The converter prepends a system message when the client omits one.
- Model IDs are case-sensitive and reject unknown values with error `11102` (`Hy3` fails, `hy3` works).
- `gpt-5.6-luna` and friends reject very small `max_tokens` values (error `11133`, "integer_below_min_value"); stay above roughly 100.

The key is a live credential: treat it like a password, and expect to rotate it when it expires.

### ⚠️ Disclaimer

For personal learning and research only. Not affiliated with Tencent / CodeBuddy / OpenAI. Use only with a subscription you legally hold, in compliance with the relevant terms of service, at your own risk.

Licence: [GPL-3.0-or-later](./LICENSE)

---

<!-- SEO keywords -->
<sub>
**Keywords / 关键词:** codebuddy to openai · codebuddy2openai · codebuddy openai compatible api · codebuddy api proxy · codebuddy workbuddy openai adapter · tencent codebuddy openai · codebuddy glm-5.2 api · codebuddy kimi deepseek openai · openai compatible proxy local llm gateway · codebuddy function calling · codebuddy tool use tool_calls · codebuddy zcode cherry studio · 腾讯代码助手 openai · codebuddy 转 openai · codebuddy 接入 zcode cherry studio · 本地大模型代理 openai 协议 · codebuddy 订阅 复用 · workbuddy api 转换 · codebuddy 工具调用
</sub>
