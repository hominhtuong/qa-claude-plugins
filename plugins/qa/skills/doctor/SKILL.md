---
name: doctor
description: Check the toolchain for the qa plugin (python/node/wrangler/java/mvn + optional adb/appium) and print the correct install command per OS; optionally auto-install wrangler. Cross-platform. Use when a script reports a missing tool, or to confirm the machine is ready to run tests / push reports / Lark notify.
---

# Skill: doctor

Check the tools required on the current machine. The logic lives in `scripts/doctor.py` (cross-platform) — this skill just runs it and interprets the output.

## Procedure
1. **Run doctor**:
   - macOS/Linux: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/doctor.py` (add `--fix` to auto-install wrangler if npm is present)
   - Windows: `python ${CLAUDE_PLUGIN_ROOT}/scripts/doctor.py --fix`

2. **Read the result table**:
   - `[ok]` = present; `[MISSING]` = required but absent; `[absent]` = optional (adb/appium only needed for mobile).
   - Required tools: `python3`, `node`, `npm`, `wrangler`, `java`, `mvn`.

3. **For a missing tool**: the script already prints the **correct install command per OS** (brew / winget / apt). `wrangler` can be auto-installed via `--fix` (needs npm); for `python/node/java/mvn` hand the command to the user to run — do not auto-install system toolchains.

4. **TLS line**: `[ok] TLS … can reach Lark over HTTPS` means HTTPS works (with `--fix`, doctor installs `truststore` so a corporate proxy's CA is trusted via the OS trust store — `(via OS trust store)` is appended). A `[warn] TLS` only appears when truststore couldn't be installed AND the proxy still blocks Lark; doctor then prints the one-line fallback (retry `pip install truststore`, or set `SSL_CERT_FILE`).

## Principles
- You can't use python to install python/node/java itself → only detect + guide.
- `wrangler` is only needed when `ENABLE_CF_PUSH=true`; `java`/`mvn` are needed for Appium/Playwright Java test projects.
- `truststore` (auto-installed by `--fix`) is the default fix for corporate-proxy TLS: it routes verification through the OS trust store (Keychain/Windows store/ca-certificates), which already holds the company root CA — so no hand-built PEM and no `SSL_CERT_FILE` needed in the common case. Needs Python 3.10+.
