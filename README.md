# chlz-parse

Claude Code skill for parsing Charles `.chlz` proxy logs. Built for ad tech debugging — analyzing VAST, OMID/OM SDK, tracking pixels, and DSP request flows.

## Install

```bash
git clone <repo-url>
cd chlz-parse
bash install.sh
```

Then restart Claude Code. The `/chlz-parse` slash command will be available.

## Uninstall

```bash
rm ~/.claude/commands/chlz-parse.md
rm ~/.claude/scripts/chlz_parse.py
```

## Usage

In Claude Code, provide a `.chlz` file and the skill will automatically trigger. Or invoke manually:

```
/chlz-parse
```

### Commands

| Command | What it does |
|---------|-------------|
| `list` | List all requests, filter by `--host` / `--path` |
| `hosts` | Unique hosts with request counts |
| `search` | Find requests by keyword in URL |
| `grep` | Search inside response bodies |
| `show` | Full metadata + response of one request |
| `sequence` | Requests around an index (context window) |
| `omid` | One-shot OMID/OM SDK activity check |

### Standalone CLI

The script also works directly in terminal:

```bash
python3 scripts/chlz_parse.py hosts session.chlz
python3 scripts/chlz_parse.py omid session.chlz
python3 scripts/chlz_parse.py search session.chlz "appier"
```

## Requirements

- Python 3.6+
- No external dependencies (stdlib only)
