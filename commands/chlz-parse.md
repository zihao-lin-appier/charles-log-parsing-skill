---
name: chlz-parse
description: Parse and analyze Charles .chlz proxy logs for ad tech debugging. Use when the user asks to analyze Charles logs, check network requests, search for specific ad SDK activity (OMID, VAST, tracking pixels), or debug ad serving flows. Trigger on mentions of ".chlz", "charles log", "proxy log", "check requests", "network trace".
allowed-tools: Bash, Read, Glob
---

# Charles .chlz Log Parser

Parse Charles proxy log archives (.chlz) to analyze ad tech network requests.

## Tool

```
python3 ~/.claude/scripts/chlz_parse.py <command> <chlz_path> [options]
```

## Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `list` | List all requests (filterable by `--host` / `--path`) | `list session.chlz --host appier` |
| `hosts` | List unique hosts with request counts | `hosts session.chlz` |
| `search` | Search requests by keyword in host/path/query | `search session.chlz "om-viewability"` |
| `grep` | Search inside response bodies for a keyword | `grep session.chlz "AdVerification"` |
| `show` | Show full details + response of a specific request | `show session.chlz 209` |
| `sequence` | Show requests around an index (`-c` for context) | `sequence session.chlz 209 -c 10` |
| `omid` | Check for all OMID/OM SDK related activity | `omid session.chlz` |

Input can be a `.chlz` file (auto-extracted to temp dir) or an already-extracted directory.

## Workflow

When the user provides a .chlz file or asks to analyze Charles logs:

1. **Start with `hosts`** to get an overview of all network activity.
2. **Use `omid`** if investigating Open Measurement / viewability issues.
3. **Use `search`** to find requests from a specific DSP, SDK, or domain.
4. **Use `grep`** to find keywords inside response bodies (e.g., VAST XML content, bid responses).
5. **Use `show`** to inspect a specific request's full metadata and response.
6. **Use `sequence`** to understand the request flow around a specific event.
7. **Use `list --host`** for a filtered chronological view of one domain.

## Batch Analysis

To analyze multiple .chlz files at once, loop over them:

```bash
for f in /path/to/*.chlz; do
  echo "=== $(basename $f) ==="
  python3 ~/.claude/scripts/chlz_parse.py omid "$f"
  echo
done
```

## Notes

- The script auto-extracts .chlz files to a temp directory. For repeated analysis, pass the extracted directory directly to avoid re-extraction.
- Binary response files (.mp4, .gif, .png, etc.) are skipped by `grep`.
- Request indices come from Charles's internal numbering and are chronologically ordered.
