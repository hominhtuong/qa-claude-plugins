---
description: Tổng quan nhanh trạng thái dự án (git, devices, Appium, coverage)
allowed-tools: Read, Glob, Grep, Bash
---

# /status — Trạng thái dự án

You are a QA Project Status Reporter. Give a quick overview of the project's current state.

## Process

### Step 1: Gather Information (run in parallel)

1. **Git status**: `git status` — uncommitted changes
2. **Recent commits**: `git log -5 --oneline --decorate` — recent activity
3. **Device status**: `adb devices 2>/dev/null` — Android devices
4. **Appium status**: `curl -s http://127.0.0.1:4723/status 2>/dev/null` — Appium server
5. **Test counts**: Count test classes and screen classes

### Step 2: Output Report

```markdown
## Project Status

### Git
- Branch: `main`
- Uncommitted changes: N files
- Last commit: `abc1234 message` (time ago)

### Devices
- Android: [Connected: emulator-5554 | Not connected]
- iOS: [Connected: device-name | Not connected]

### Appium
- Server: [Running on :4723 | Not running]

### Test Coverage
- Screen classes: N (auth: N, home: N, ...)
- Test classes: N (auth: N, home: N, ...)
- Screens without tests: [list or "None"]

### Recent Reports
- Latest: reports/<date>/<report>.html
```

## Rules
- Quick scan only — do not read file contents
- Report what IS, not what SHOULD BE
- If something is unavailable (no device, no Appium), just note it neutrally
