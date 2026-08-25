#!/usr/bin/env python3
"""
Check the JIRA status of all @pytest.mark.skip and @pytest.mark.xfail tickets
found in a given path.  Local usage only (macOS Keychain auth).

Usage:
    python3 scripts/check_skip_xfail_tickets_status.py <path> [--html <output.html>]

Example:
    python3 scripts/check_skip_xfail_tickets_status.py tests/iceberg/asqs/pushdown_filters
    python3 scripts/check_skip_xfail_tickets_status.py tests/iceberg/asqs --html report/skip_report.html
"""

import re
import sys
import json
import subprocess
import datetime
import threading
import concurrent.futures
from pathlib import Path
from collections import defaultdict

JIRA_BASE_URL = "https://track-api.company_name.com/jira/rest/api/2/issue"
TICKET_PATTERN = re.compile(r"([A-Z]+-[0-9]+)")

STATUS_COLORS = {
    "Closed":      "\033[92m",  # green
    "Done":        "\033[92m",  # green
    "Resolved":    "\033[92m",  # green
    "Open":        "\033[91m",  # red
    "In Progress": "\033[93m",  # yellow
    "To Do":       "\033[91m",  # red
    "Reopened":    "\033[91m",  # red
}
RESET = "\033[0m"
BOLD  = "\033[1m"


def colorize(text, color):
    return f"{color}{text}{RESET}"


REASON_PATTERN = re.compile(r'reason\s*=\s*["\'](.*?)["\']')
DEF_PATTERN    = re.compile(r'^\s*(?:async\s+)?def\s+(\w+)\s*\(')
CLASS_PATTERN  = re.compile(r'^\s*class\s+(\w+)')


def _find_test_name(lines: list, lineno: int) -> str:
    """Scan forward from lineno (1-based) to find the nearest def/class name."""
    for i in range(lineno - 1, min(lineno + 15, len(lines))):
        m = DEF_PATTERN.match(lines[i]) or CLASS_PATTERN.match(lines[i])
        if m:
            return m.group(1)
    return None


def find_markers(search_path: Path) -> tuple:
    """
    Scan Python files under search_path for skip/xfail markers.
    Returns:
        locations: ticket_id -> [(rel_file, lineno, marker_type), ...]
        no_ticket_markers: [(rel_file, lineno, marker_type, reason), ...]
    """
    locations = defaultdict(list)
    no_ticket_markers = []
    if search_path.is_file():
        files = [search_path]
    else:
        files = search_path.rglob("*.py")

    for py_file in files:
        with open(py_file, encoding="utf-8", errors="ignore") as f:
            all_lines = f.readlines()
        for lineno, line in enumerate(all_lines, start=1):
            stripped = line.strip()
            if not stripped.startswith("@"):
                continue
            if "mark.skip" in stripped or "mark.xfail" in stripped:
                marker_type = "skip" if "mark.skip" in stripped else "xfail"
                tickets = TICKET_PATTERN.findall(stripped)
                try:
                    rel = py_file.relative_to(search_path)
                except Exception:
                    rel = py_file.name
                test_name = _find_test_name(all_lines, lineno)
                if tickets:
                    for ticket in tickets:
                        locations[ticket].append((str(rel), lineno, marker_type, test_name))
                elif re.search(r'mark\.(?:skip|xfail)\s*\(', stripped):
                    # Only capture explicit skip(...)/xfail(...) calls, not custom marks like skip_jdbc
                    reason_match = REASON_PATTERN.search(stripped)
                    reason = reason_match.group(1) if reason_match else stripped
                    no_ticket_markers.append((str(rel), lineno, marker_type, reason, test_name))
    return locations, no_ticket_markers


def fetch_all_statuses(ticket_ids: list) -> dict:
    """
    Fetch all JIRA tickets in parallel using macOS Keychain auth (-E $USER).
    Returns: ticket_id -> status_dict
    """
    total   = len(ticket_ids)
    done    = 0
    lock    = threading.Lock()

    def _fetch(tid):
        nonlocal done
        raw = ""
        for attempt in range(2):
            result = subprocess.run(
                f"export CURL_SSL_BACKEND=secure-transport\ncurl -s -E $USER {JIRA_BASE_URL}/{tid}",
                shell=True, capture_output=True, text=True,
            )
            raw = result.stdout.strip()
            if raw:
                break
        with lock:
            done += 1
            print(f"  [{done}/{total}] {tid}", flush=True)
        return tid, raw

    def _parse(tid, raw):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            preview = raw[:200].replace("\n", " ") if raw else "<empty response>"
            return {"error": f"Invalid JSON — raw: {preview}"}
        if "fields" not in data:
            return {"error": str(data.get("errorMessages", ["Unknown"]))}
        fields     = data["fields"]
        resolution = fields.get("resolution")
        return {
            "summary":    fields.get("summary", "N/A"),
            "status":     fields["status"]["name"],
            "resolution": resolution["name"] if resolution else "Unresolved",
            "assignee":   (fields.get("assignee") or {}).get("displayName", "Unassigned"),
        }

    statuses = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        for tid, raw in executor.map(_fetch, ticket_ids):
            statuses[tid] = _parse(tid, raw)

    for tid in ticket_ids:
        if tid not in statuses:
            statuses[tid] = {"error": "No response from JIRA"}
    return statuses


def write_html_report(locations: dict, statuses: dict, output_path: str, no_ticket_markers: list = None):
    """Write a self-contained HTML report to output_path."""
    rows = []
    for ticket_id, occurrences in sorted(locations.items()):
        info   = statuses.get(ticket_id, {})
        status = info.get("status", "UNKNOWN")
        error  = info.get("error")

        if status in ("Closed", "Done", "Resolved"):
            row_class = "closed"
            badge     = f'<span class="badge green">{status}</span>'
            action    = '<span class="action">&#x26A0; Remove marker</span>'
        elif error:
            row_class = "error"
            badge     = '<span class="badge grey">ERROR</span>'
            action    = f'<span class="action-err">{error}</span>'
        else:
            row_class = "open"
            badge     = f'<span class="badge yellow">{status}</span>'
            action    = '<span class="ok">&#x2713; Keep marker</span>'

        marker_lines = "".join(
            f'<div class="marker"><code>[{mt}]</code> {f}::{tn if tn else ln}</div>'
            for f, ln, mt, tn in occurrences
        )
        jira_url = f"https://track.company_name.com/jira/browse/{ticket_id}"
        rows.append(f"""
        <tr class="{row_class}">
          <td><a href="{jira_url}" target="_blank">{ticket_id}</a></td>
          <td>{badge}</td>
          <td>{info.get('resolution', error or '')}</td>
          <td>{info.get('summary', '')}</td>
          <td>{info.get('assignee', '')}</td>
          <td>{marker_lines}</td>
          <td>{action}</td>
        </tr>""")

    no_ticket_markers = no_ticket_markers or []
    for rel_file, lineno, marker_type, reason, test_name in no_ticket_markers:
        label = f"{rel_file}::{test_name}" if test_name else f"{rel_file}:{lineno}"
        rows.append(f"""
        <tr class="no-ticket">
          <td><span class="no-ticket-label">NO TICKET</span></td>
          <td><span class="badge grey">—</span></td>
          <td>—</td>
          <td>{reason}</td>
          <td>—</td>
          <td><div class="marker"><code>[{marker_type}]</code> {label}</div></td>
          <td><span class="action-err">&#x26A0; Add ticket or remove</span></td>
        </tr>""")

    total  = len(locations)
    closed = sum(1 for t in locations if statuses.get(t, {}).get("status") in ("Closed", "Done", "Resolved"))
    open_  = total - closed
    no_ticket_count = len(no_ticket_markers)
    ts     = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <title>Skip/XFail Ticket Status Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; background: #f5f5f5; }}
    h1   {{ color: #333; }}
    .summary {{ display:flex; gap:24px; margin-bottom:20px; }}
    .card {{ background:#fff; border-radius:8px; padding:16px 24px; box-shadow:0 1px 4px rgba(0,0,0,.1); }}
    .card .num {{ font-size:2em; font-weight:bold; }}
    .card.c-total    .num {{ color:#333; }}
    .card.c-closed   .num {{ color:#2a9d2a; }}
    .card.c-open     .num {{ color:#c0392b; }}
    .card.c-noticket .num {{ color:#7b5ea7; }}
    tr.no-ticket td:first-child {{ border-left:4px solid #7b5ea7; }}
    .no-ticket-label {{ color:#7b5ea7; font-weight:bold; font-size:.9em; }}
    table  {{ border-collapse:collapse; width:100%; background:#fff;
              box-shadow:0 1px 4px rgba(0,0,0,.1); border-radius:8px; overflow:hidden; }}
    th     {{ background:#333; color:#fff; padding:10px 14px; text-align:left; }}
    td     {{ padding:10px 14px; border-bottom:1px solid #eee; vertical-align:top; }}
    tr.closed td:first-child {{ border-left:4px solid #2a9d2a; }}
    tr.open   td:first-child {{ border-left:4px solid #e67e22; }}
    tr.error  td:first-child {{ border-left:4px solid #aaa; }}
    .badge {{ padding:3px 10px; border-radius:12px; font-size:.85em; font-weight:bold; }}
    .badge.green  {{ background:#d4edda; color:#155724; }}
    .badge.yellow {{ background:#fff3cd; color:#856404; }}
    .badge.grey   {{ background:#e2e3e5; color:#383d41; }}
    .action     {{ color:#c0392b; font-weight:bold; }}
    .action-err {{ color:#888; font-style:italic; }}
    .ok         {{ color:#2a9d2a; font-weight:bold; }}
    .marker     {{ font-size:.85em; color:#555; margin:2px 0; }}
    a {{ color:#0066cc; }}
    .ts {{ color:#888; font-size:.85em; margin-top:12px; }}
  </style>
</head>
<body>
  <h1>Skip / XFail Ticket Status Report</h1>
  <div class="summary">
    <div class="card c-total" ><div class="num">{total}</div> <div>Total tickets</div></div>
    <div class="card c-closed"><div class="num">{closed}</div><div>Closed &#x2014; remove markers</div></div>
    <div class="card c-open"  ><div class="num">{open_}</div> <div>Still open &#x2014; keep markers</div></div>
    <div class="card c-noticket"><div class="num">{no_ticket_count}</div><div>No ticket &#x2014; needs triage</div></div>
  </div>
  <table>
    <tr>
      <th>Ticket</th><th>Status</th><th>Resolution</th>
      <th>Summary</th><th>Assignee</th><th>Markers</th><th>Action</th>
    </tr>
    {"".join(rows)}
  </table>
  <p class="ts">Generated: {ts}</p>
</body>
</html>"""

    abs_path = Path(output_path).resolve()
    abs_path.parent.mkdir(parents=True, exist_ok=True)
    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML report written to: {abs_path}")
    print(f"Open in browser:        file://{abs_path}")


def print_results(locations: dict, statuses: dict, no_ticket_markers: list = None):
    print()
    print(f"{BOLD}{'='*70}{RESET}")
    print(f"{BOLD}  JIRA Ticket Status Report for Skip/XFail Markers{RESET}")
    print(f"{BOLD}{'='*70}{RESET}\n")

    closed, open_ = [], []

    for ticket_id, occurrences in sorted(locations.items()):
        info   = statuses.get(ticket_id, {})
        status = info.get("status", "UNKNOWN")
        color  = STATUS_COLORS.get(status, "\033[37m")
        error  = info.get("error")

        (closed if status in ("Closed", "Done", "Resolved") else open_).append(ticket_id)

        print(f"  {BOLD}{ticket_id}{RESET}  [{colorize(status, color)}]  {info.get('resolution', '')}")
        if error:
            print(f"    Error   : {error}")
        else:
            print(f"    Summary : {info['summary']}")
            print(f"    Assignee: {info['assignee']}")
        print(f"    Markers ({len(occurrences)} occurrence(s)):")
        for rel_file, lineno, marker_type, test_name in occurrences:
            label = f"{rel_file}::{test_name}" if test_name else f"{rel_file}:{lineno}"
            print(f"      [{marker_type:4s}] {label}")
        print()

    print(f"{BOLD}{'='*70}{RESET}")
    print(f"{BOLD}  Summary{RESET}")
    print(f"{BOLD}{'='*70}{RESET}")
    print(f"  Total unique tickets : {len(locations)}")
    if closed:
        print(f"  {colorize('Closed (can unskip)', STATUS_COLORS['Closed'])} : {', '.join(closed)}")
    if open_:
        print(f"  {colorize('Still open          ', STATUS_COLORS['Open'])} : {', '.join(open_)}")

    no_ticket_markers = no_ticket_markers or []
    if no_ticket_markers:
        print(f"  {colorize('No ticket (needs triage)', chr(27) + '[95m')} : {len(no_ticket_markers)} marker(s)")
        print()
        print(f"{BOLD}  Markers without JIRA tickets:{RESET}")
        for rel_file, lineno, marker_type, reason, test_name in no_ticket_markers:
            label = f"{rel_file}::{test_name}" if test_name else f"{rel_file}:{lineno}"
            print(f"    [{marker_type:4s}] {label}")
            print(f"           reason: {reason}")
    print()


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 check_xfail_skip_tickets_local.py <path> [--html <output.html>]")
        print("Example: python3 check_xfail_skip_tickets_local.py tests/iceberg/asqs/pushdown_filters")
        sys.exit(1)

    args = sys.argv[1:]
    html_output = None
    if "--html" in args:
        idx = args.index("--html")
        if idx + 1 >= len(args):
            print("Error: --html requires a file path argument")
            sys.exit(1)
        html_output = args[idx + 1]
        args = args[:idx] + args[idx + 2:]

    search_path = Path(args[0])

    if not search_path.exists():
        repo_root = Path(__file__).resolve().parent.parent
        search_path = repo_root / search_path

    if not search_path.exists():
        print(f"Error: path does not exist: {search_path}")
        sys.exit(1)

    print(f"\nScanning: {search_path}")
    locations, no_ticket_markers = find_markers(search_path)

    if not locations and not no_ticket_markers:
        print("No skip/xfail markers found.")
        sys.exit(0)

    unique_tickets = sorted(locations.keys())

    # Total marker occurrences
    total_issues = sum(len(v) for v in locations.values())

    # Skip / xfail counts (with tickets)
    total_skip = sum(
        1
        for occurrences in locations.values()
        for _, _, marker_type, _ in occurrences
        if marker_type == "skip"
    )

    total_xfail = sum(
        1
        for occurrences in locations.values()
        for _, _, marker_type, _ in occurrences
        if marker_type == "xfail"
    )

    # Skip / xfail counts (without tickets)
    no_ticket_skip = sum(
        1 for _, _, marker_type, _, _ in no_ticket_markers
        if marker_type == "skip"
    )

    no_ticket_xfail = sum(
        1 for _, _, marker_type, _, _ in no_ticket_markers
        if marker_type == "xfail"
    )

    total_markers_with_ticket = sum(len(v) for v in locations.values())
    total_markers = total_markers_with_ticket + len(no_ticket_markers)

    print(f"Found {len(unique_tickets)} unique ticket(s)")
    print(f"Total marker occurrences : {total_markers}")
    print(f"Total markers with ticket: {total_markers_with_ticket}")
    print(f"Total skip markers   : {total_skip + no_ticket_skip}")
    print(f"Total xfail markers  : {total_xfail + no_ticket_xfail}")
    print(f"Skip without ticket  : {no_ticket_skip}")
    print(f"XFail without ticket : {no_ticket_xfail}")
    print(f"Total without ticket : {len(no_ticket_markers)}")
    print()
    print(", ".join(unique_tickets))
    print()

    statuses = {}
    if unique_tickets:
        print(f"Fetching JIRA statuses (up to 10 in parallel)...\n")
        statuses = fetch_all_statuses(unique_tickets)

    print_results(locations, statuses, no_ticket_markers)

    if html_output:
        write_html_report(locations, statuses, html_output, no_ticket_markers)


if __name__ == "__main__":
    main()


'''
What This Script Does
This script scans Python test files for @pytest.mark.skip and @pytest.mark.xfail markers, 
extracts JIRA ticket IDs from them, checks each ticket's current status in JIRA, 
and tells you which skipped/xfailed tests can now be re-enabled (because their ticket is closed).

How It Connects to JIRA
The connection happens in fetch_all_statuses(). It uses macOS Keychain-based client certificate auth via curl:
bashcurl -s -E $USER https://track-api.company_name.com/jira/rest/api/2/issue/<TICKET_ID>
Breaking that down:

-s — silent mode (no progress output)
-E $USER — this is the key part: it tells curl to use a client SSL certificate from the macOS Keychain where the certificate name matches your $USER (your macOS username). This is how it authenticates to company_name's internal JIRA without a username/password.
It hits the standard JIRA REST API v2 endpoint: /jira/rest/api/2/issue/{TICKET_ID}
It also sets CURL_SSL_BACKEND=secure-transport to force macOS's native TLS stack (required for Keychain cert access)

It batches all tickets into a single shell script with multiple curl calls
separated by a custom separator string (===TICKET_SEP===), runs the whole thing in one subprocess.run(), 
then splits the output on that separator to parse each ticket's JSON response individually.

Step-by-Step Flow
1. SCAN  →  find_markers(path)
            - Walks all .py files under the given path
            - Looks for lines containing "mark.skip" or "mark.xfail"
            - Extracts JIRA-style ticket IDs (regex: [A-Z]+-[0-9]+)
            - Records: ticket → [(file, line_number, marker_type)]

2. FETCH →  fetch_all_statuses(ticket_ids)
            - Builds one big shell script with one curl per ticket
            - Runs it via subprocess
            - Splits output by separator, parses each JSON blob
            - Extracts: status, resolution, summary, assignee

3. OUTPUT → print_results()  and/or  write_html_report()
            - Closed/Done/Resolved → "Remove this marker" (test can be unskipped)
            - Open/In Progress/To Do → "Keep marker" (bug still open)
            - Errors → shown in grey

What the HTML Report Adds
If you pass --html report/output.html, it generates a self-contained HTML page with a summary dashboard (total / closed / open counts), a color-coded table for every ticket, and clickable links directly to each JIRA ticket.
'''