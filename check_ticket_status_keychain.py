#!/usr/bin/env python3

import re
import sys
import json
import subprocess
import datetime
from pathlib import Path
from collections import defaultdict

JIRA_BASE_URL = "https://track-api.company.com/jira/rest/api/2/issue"
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


def find_markers(search_path: Path) -> dict:
    """
    Scan Python files under search_path for skip/xfail markers.
    Returns: ticket_id -> [(rel_file, lineno, marker_type), ...]
    """
    locations = defaultdict(list)
    if search_path.is_file():
        files = [search_path]
    else:
        files = search_path.rglob("*.py")

    for py_file in files:
        with open(py_file, encoding="utf-8", errors="ignore") as f:
            for lineno, line in enumerate(f, start=1):
                stripped = line.strip()
                if "mark.skip" in stripped or "mark.xfail" in stripped:
                    marker_type = "skip" if "mark.skip" in stripped else "xfail"
                    for ticket in TICKET_PATTERN.findall(stripped):
                        try:
                            rel = py_file.relative_to(search_path)
                        except Exception:
                            rel = py_file.name
                        locations[ticket].append((str(rel), lineno, marker_type))
    return locations


def fetch_all_statuses(ticket_ids: list) -> dict:
    """
    Fetch all JIRA tickets using macOS Keychain auth (-E $USER).
    Returns: ticket_id -> status_dict
    """
    separator = "===TICKET_SEP==="
    curls = "\n".join(
        f'echo "{separator}{tid}"\ncurl -s -E $USER {JIRA_BASE_URL}/{tid}'
        for tid in ticket_ids
    )
    script = f"export CURL_SSL_BACKEND=secure-transport\n{curls}"

    result = subprocess.run(script, shell=True, capture_output=True, text=True)

    statuses = {}
    for section in result.stdout.split(separator)[1:]:
        lines = section.strip().splitlines()
        if not lines:
            continue
        ticket_id = lines[0].strip()
        try:
            data = json.loads("\n".join(lines[1:]))
        except json.JSONDecodeError:
            statuses[ticket_id] = {"error": "Invalid JSON"}
            continue

        if "fields" not in data:
            statuses[ticket_id] = {"error": str(data.get("errorMessages", ["Unknown"]))}
            continue

        fields = data["fields"]
        resolution = fields.get("resolution")
        statuses[ticket_id] = {
            "summary":    fields.get("summary", "N/A"),
            "status":     fields["status"]["name"],
            "resolution": resolution["name"] if resolution else "Unresolved",
            "assignee":   (fields.get("assignee") or {}).get("displayName", "Unassigned"),
        }

    for tid in ticket_ids:
        if tid not in statuses:
            statuses[tid] = {"error": "No response from JIRA"}
    return statuses


def write_html_report(locations: dict, statuses: dict, output_path: str):
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
            f'<div class="marker"><code>[{mt}]</code> {f}:{ln}</div>'
            for f, ln, mt in occurrences
        )
        jira_url = f"https://track-api.company.com/jira/browse/{ticket_id}"
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

    total  = len(locations)
    closed = sum(1 for t in locations if statuses.get(t, {}).get("status") in ("Closed", "Done", "Resolved"))
    open_  = total - closed
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
    .card.c-total  .num {{ color:#333; }}
    .card.c-closed .num {{ color:#2a9d2a; }}
    .card.c-open   .num {{ color:#c0392b; }}
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


def print_results(locations: dict, statuses: dict):
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
        for rel_file, lineno, marker_type in occurrences:
            print(f"      [{marker_type:4s}] {rel_file}:{lineno}")
        print()

    print(f"{BOLD}{'='*70}{RESET}")
    print(f"{BOLD}  Summary{RESET}")
    print(f"{BOLD}{'='*70}{RESET}")
    print(f"  Total unique tickets : {len(locations)}")
    if closed:
        print(f"  {colorize('Closed (can unskip)', STATUS_COLORS['Closed'])} : {', '.join(closed)}")
    if open_:
        print(f"  {colorize('Still open          ', STATUS_COLORS['Open'])} : {', '.join(open_)}")
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
        repo_root = Path(__file__).resolve().parent.parent.parent
        search_path = repo_root / search_path

    if not search_path.exists():
        print(f"Error: path does not exist: {search_path}")
        sys.exit(1)

    print(f"\nScanning: {search_path}")
    locations = find_markers(search_path)

    if not locations:
        print("No skip/xfail markers with JIRA tickets found.")
        sys.exit(0)

    unique_tickets = sorted(locations.keys())
    print(f"Found {len(unique_tickets)} unique ticket(s): {', '.join(unique_tickets)}\n")
    print("Fetching JIRA statuses...\n")

    statuses = fetch_all_statuses(unique_tickets)
    for tid in unique_tickets:
        info   = statuses.get(tid, {})
        status = info.get("status", info.get("error", "?"))
        print(f"  {tid}: {status}")

    print_results(locations, statuses)

    if html_output:
        write_html_report(locations, statuses, html_output)


if __name__ == "__main__":
    main()


'''
What This Script Does
This script scans Python test files for @pytest.mark.skip and @pytest.mark.xfail markers, 
extracts JIRA ticket IDs from them, checks each ticket's current status in JIRA, 
and tells you which skipped/xfailed tests can now be re-enabled (because their ticket is closed).

How It Connects to JIRA
The connection happens in fetch_all_statuses(). It uses macOS Keychain-based client certificate auth via curl:
bashcurl -s -E $USER https://track-api.company.com/jira/rest/api/2/issue/<TICKET_ID>
Breaking that down:

-s — silent mode (no progress output)
-E $USER — this is the key part: it tells curl to use a client SSL certificate from the macOS Keychain where the certificate name matches your $USER (your macOS username). This is how it authenticates to the company's internal JIRA without a username/password.
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