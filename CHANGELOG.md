# Changelog

All notable changes to the `qa` plugin. Versions follow the plugin manifest
(`plugins/qa/.claude-plugin/plugin.json`).

## 0.0.14 — Lark auth/doc-reading: handle every failure with one clear action

Hardens the Lark authentication + document-reading path so a new user reaches a
document without debugging six layers by hand. Every failure now maps to a stable
`error_code` plus a single next action.

- **#1 env parser — inline comments no longer break values.** `_env.py` gained a single
  `parse_env_line`/`strip_inline_comment` (used everywhere): a `# comment` is cut only when
  whitespace precedes it, so a `#` inside a value (secret `ab#cd`, colour `#FF0000`, URL
  fragment) is preserved. The `.plugin.env.example` no longer ships an inline comment on
  `LARK_DOMAIN=` (it was producing `URL can't contain control characters`).
- **#2 read scopes are tested for real, not assumed.** `wiki.read`/`docx.read`/`drive.read`
  now do a harmless GET and report `✅granted`/`❌denied` (only `bitable.write`/`drive.upload`
  stay `📜declared`). A missing `wiki:wiki` scope surfaces at `/qa:auth-lark`, not mid-read.
  New `--probe-doc <url>` / `LARK_PROBE_DOC` tests against the exact document you need.
- **#3 corporate self-signed SSL is actionable.** The TLS context honours `SSL_CERT_FILE`
  and auto-uses `truststore` (OS trust store) when installed; a `CERTIFICATE_VERIFY_FAILED`
  prints a one-step `SSL_CERT_FILE` fix instead of a stacktrace. `SSL_CERT_FILE` is now
  documented in `.plugin.env.example`, and `/qa:doctor` probes HTTPS to Lark.
- **#4 OAuth redirect (error 20029) is self-explaining.** `/qa:auth-lark --login` warns when
  it falls back to the default `:8080/callback`, the 20029 error maps to "set
  `LARK_REDIRECT_URI`", and a successful login persists the redirect that worked.
- **#5 placeholder/disabled credentials caught early.** `cli_xxxx…`/`your_app_secret` or
  `ENABLE_LARK_APP=false` now fail with a precise message instead of Lark's opaque
  `invalid param (code=10003)`.
- **#6 actionable errors everywhere.** Both `lark_auth.py` and `lark_read.py` emit
  `error_code` + `action` for env / SSL / scope / redirect / placeholder / doc-not-shared,
  so the `lark-reader` agent and `/qa:analyze-spec` propose the exact fix.
- Added stdlib unit tests (`plugins/qa/scripts/tests/test_lark.py`): env parsing,
  placeholder detection, read-scope classification, error diagnosis. No secret/token is ever
  printed on any branch.
