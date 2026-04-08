#!/usr/bin/env python3
"""Parse Charles .chlz proxy logs for ad tech debugging."""

import argparse
import glob
import json
import os
import sys
import tempfile
import zipfile


def extract_chlz(chlz_path, dest=None):
    """Extract .chlz to a temp dir (or specified dest). Returns the dir path."""
    if dest is None:
        dest = tempfile.mkdtemp(prefix="chlz_")
    with zipfile.ZipFile(chlz_path, "r") as z:
        z.extractall(dest)
    return dest


def iter_meta(directory):
    """Yield (index, meta_dict, basename) sorted by request index."""
    for f in glob.glob(os.path.join(directory, "*-meta.json")):
        base = os.path.basename(f)
        try:
            idx = int(base.split("-")[0])
        except ValueError:
            continue
        try:
            with open(f) as fh:
                meta = json.load(fh)
        except (json.JSONDecodeError, IOError):
            continue
        yield idx, meta, base
    return


def sorted_meta(directory):
    return sorted(iter_meta(directory), key=lambda x: x[0])


def fmt_req(idx, meta):
    method = meta.get("method", "?")
    scheme = meta.get("scheme", "https")
    host = meta.get("host", "") or ""
    path = meta.get("path", "") or ""
    status = meta.get("status", "")
    return f"{idx:>4}: {method:<6} {scheme}://{host}{path}  [{status}]"


# --- Commands ---


def cmd_list(directory, args):
    """List all requests, optionally filtered by --host or --path."""
    host_filter = (args.host or "").lower()
    path_filter = (args.path or "").lower()
    for idx, meta, _ in sorted_meta(directory):
        host = (meta.get("host", "") or "").lower()
        path = (meta.get("path", "") or "").lower()
        if host_filter and host_filter not in host:
            continue
        if path_filter and path_filter not in path:
            continue
        print(fmt_req(idx, meta))


def cmd_hosts(directory, args):
    """List unique hosts with request counts."""
    hosts = {}
    for idx, meta, _ in sorted_meta(directory):
        host = meta.get("host", "") or "(unknown)"
        hosts.setdefault(host, []).append(idx)
    for host, indices in sorted(hosts.items(), key=lambda x: -len(x[1])):
        print(f"{len(indices):>4}x  {host}")


def cmd_show(directory, args):
    """Show full details of a specific request by index."""
    target = args.index
    for idx, meta, base in sorted_meta(directory):
        if idx != target:
            continue
        print(f"=== Request #{idx} ===")
        print(json.dumps(meta, indent=2, ensure_ascii=False))

        # Show response file if exists
        prefix = f"{idx}-res"
        for f in glob.glob(os.path.join(directory, f"{prefix}.*")):
            ext = os.path.splitext(f)[1]
            size = os.path.getsize(f)
            print(f"\n--- Response ({ext}, {size} bytes) ---")
            if ext in (".json",):
                try:
                    with open(f) as fh:
                        data = json.load(fh)
                    out = json.dumps(data, indent=2, ensure_ascii=False)
                    if len(out) > 5000:
                        print(out[:5000] + "\n... (truncated)")
                    else:
                        print(out)
                except Exception:
                    print(f"(could not parse JSON: {f})")
            elif ext in (".html", ".xml", ".js", ".css", ".txt", ".dat"):
                try:
                    with open(f, "r", errors="replace") as fh:
                        content = fh.read(5000)
                    print(content)
                    if len(content) == 5000:
                        print("... (truncated)")
                except Exception:
                    print(f"(could not read: {f})")
            else:
                print(f"(binary file: {ext})")
        return
    print(f"Request #{target} not found.")


def cmd_search(directory, args):
    """Search requests by host and/or path keyword."""
    keyword = args.keyword.lower()
    for idx, meta, _ in sorted_meta(directory):
        host = (meta.get("host", "") or "").lower()
        path = (meta.get("path", "") or "").lower()
        query = (meta.get("query", "") or "").lower()
        if keyword in host or keyword in path or keyword in query:
            print(fmt_req(idx, meta))


def cmd_grep(directory, args):
    """Search inside response bodies for a keyword."""
    keyword = args.keyword.lower()
    found = False
    for idx, meta, base in sorted_meta(directory):
        prefix = f"{idx}-res"
        for f in glob.glob(os.path.join(directory, f"{prefix}.*")):
            ext = os.path.splitext(f)[1]
            if ext in (".mp4", ".mp3", ".gif", ".png", ".jpg", ".jpeg", ".webp"):
                continue
            try:
                with open(f, "r", errors="replace") as fh:
                    content = fh.read()
                if keyword in content.lower():
                    host = meta.get("host", "") or ""
                    path = meta.get("path", "") or ""
                    print(f"{idx:>4}: {host}{path} ({os.path.basename(f)})")
                    found = True
            except Exception:
                continue
    if not found:
        print(f"No response bodies contain '{args.keyword}'.")


def cmd_sequence(directory, args):
    """Show request sequence around a specific index (context window)."""
    center = args.index
    radius = args.context
    for idx, meta, _ in sorted_meta(directory):
        if center - radius <= idx <= center + radius:
            marker = " >>>" if idx == center else "    "
            print(f"{marker} {fmt_req(idx, meta)}")


def cmd_omid(directory, args):
    """Check for all OMID/OM SDK related activity."""
    omid_keywords = ["omid", "omsdk", "om-viewability", "omweb", "viewability.js",
                     "adverification", "verification"]
    print("=== OMID/OM SDK Script Loads ===")
    script_found = False
    for idx, meta, _ in sorted_meta(directory):
        host = (meta.get("host", "") or "").lower()
        path = (meta.get("path", "") or "").lower()
        for kw in omid_keywords:
            if kw in path or kw in host:
                print(f"  {fmt_req(idx, meta)}")
                script_found = True
                break
    if not script_found:
        print("  (none)")

    print("\n=== OMID References in Response Bodies ===")
    ref_found = False
    for idx, meta, base in sorted_meta(directory):
        prefix = f"{idx}-res"
        for f in glob.glob(os.path.join(directory, f"{prefix}.*")):
            ext = os.path.splitext(f)[1]
            if ext in (".mp4", ".mp3", ".gif", ".png", ".jpg", ".jpeg", ".webp"):
                continue
            try:
                with open(f, "r", errors="replace") as fh:
                    content = fh.read()
                cl = content.lower()
                if "om-viewability" in cl or "adverification" in cl or "omid" in cl:
                    host = meta.get("host", "") or ""
                    path = meta.get("path", "") or ""
                    matches = [kw for kw in ["om-viewability", "AdVerification", "omid"]
                               if kw.lower() in cl]
                    print(f"  {idx:>4}: {host}{path} -> contains: {', '.join(matches)}")
                    ref_found = True
            except Exception:
                continue
    if not ref_found:
        print("  (none)")


def main():
    parser = argparse.ArgumentParser(
        description="Parse Charles .chlz proxy logs for ad tech debugging.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  chlz_parse.py list session.chlz
  chlz_parse.py list session.chlz --host appier
  chlz_parse.py hosts session.chlz
  chlz_parse.py search session.chlz "om-viewability"
  chlz_parse.py grep session.chlz "om-viewability"
  chlz_parse.py show session.chlz 209
  chlz_parse.py sequence session.chlz 209 --context 5
  chlz_parse.py omid session.chlz
        """,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # list
    p_list = sub.add_parser("list", help="List all requests")
    p_list.add_argument("chlz", help="Path to .chlz file or extracted directory")
    p_list.add_argument("--host", help="Filter by host keyword")
    p_list.add_argument("--path", help="Filter by path keyword")

    # hosts
    p_hosts = sub.add_parser("hosts", help="List unique hosts with counts")
    p_hosts.add_argument("chlz", help="Path to .chlz file or extracted directory")

    # search
    p_search = sub.add_parser("search", help="Search requests by keyword in host/path/query")
    p_search.add_argument("chlz", help="Path to .chlz file or extracted directory")
    p_search.add_argument("keyword", help="Keyword to search")

    # grep
    p_grep = sub.add_parser("grep", help="Search inside response bodies")
    p_grep.add_argument("chlz", help="Path to .chlz file or extracted directory")
    p_grep.add_argument("keyword", help="Keyword to search in response content")

    # show
    p_show = sub.add_parser("show", help="Show full details of a request")
    p_show.add_argument("chlz", help="Path to .chlz file or extracted directory")
    p_show.add_argument("index", type=int, help="Request index number")

    # sequence
    p_seq = sub.add_parser("sequence", help="Show requests around an index")
    p_seq.add_argument("chlz", help="Path to .chlz file or extracted directory")
    p_seq.add_argument("index", type=int, help="Center request index")
    p_seq.add_argument("--context", "-c", type=int, default=5, help="Number of requests before/after (default: 5)")

    # omid
    p_omid = sub.add_parser("omid", help="Check for OMID/OM SDK activity")
    p_omid.add_argument("chlz", help="Path to .chlz file or extracted directory")

    args = parser.parse_args()

    # Resolve input: .chlz file or already-extracted directory
    chlz_input = args.chlz
    if os.path.isdir(chlz_input):
        directory = chlz_input
    elif os.path.isfile(chlz_input) and chlz_input.endswith(".chlz"):
        directory = extract_chlz(chlz_input)
        print(f"(extracted to {directory})\n", file=sys.stderr)
    else:
        print(f"Error: {chlz_input} is not a .chlz file or directory.", file=sys.stderr)
        sys.exit(1)

    commands = {
        "list": cmd_list,
        "hosts": cmd_hosts,
        "search": cmd_search,
        "grep": cmd_grep,
        "show": cmd_show,
        "sequence": cmd_sequence,
        "omid": cmd_omid,
    }
    commands[args.command](directory, args)


if __name__ == "__main__":
    main()
