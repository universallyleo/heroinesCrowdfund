"""Render coverage diagnostics in Actions, without publishing them to the SPA."""
import json
import os
import sys
from pathlib import Path

def summary(report):
    lines = [f"## {report['agencyId']} scrape: {report['outcome']}",
             f"New projects staged: {len(report.get('newProjectIds', []))}",
             "Staged changes require a successful apply/push before they are published."]
    if report.get('fatalError'):
        lines.append(f"- Fatal: {report['fatalError']}")
    for id, source in report.get('sources', {}).items():
        lines.append(f"- Source {id}: {source['outcome']}" + (f" — {source['error']}" if source.get('error') else ''))
    for failure in report.get('failures', []):
        lines.append(f"- Project {failure['projectId']}: {failure['error']}")
    lines.extend(f"- Warning: {warning}" for warning in report.get('warnings', []))
    lines.append(f"Pending unfinished: {len(report.get('unfinishedProjectIds', []))}; failed: {len(report.get('failedProjectIds', []))}")
    return '\n'.join(lines) + '\n'

if __name__ == '__main__':
    path = Path(sys.argv[1]) / 'run_report.json'
    if path.exists():
        report = json.loads(path.read_text(encoding='utf-8'))
        text = summary(report)
        print(text)
        if report['outcome'] != 'success' or report.get('warnings'):
            print(f"::warning::{report['agencyId']} scrape outcome: {report['outcome']}. Review source/project coverage in the report artifact.")
        if os.environ.get('GITHUB_STEP_SUMMARY'):
            with Path(os.environ['GITHUB_STEP_SUMMARY']).open('a', encoding='utf-8') as file:
                file.write(text)
