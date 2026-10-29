"""Portable pytest entry point and factual test report (stdlib only)."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def pytest_sessionfinish(session, exitstatus):
    if session.config.option.collectonly:
        return  # Collection must not overwrite the last execution report.
    reporter = session.config.pluginmanager.get_plugin('terminalreporter')
    stats = reporter.stats if reporter else {}
    passed = len(stats.get('passed', []))
    failed = len(stats.get('failed', [])) + len(stats.get('error', []))
    skipped = len(stats.get('skipped', []))
    checks_path = ROOT / 'delivery/data/verification_results.json'
    checks = json.loads(checks_path.read_text(encoding='utf-8')) if checks_path.exists() else {}
    report = {
        'tests_passed': passed, 'tests_total': session.testscollected,
        'tests_failed': failed, 'tests_skipped': skipped,
        'checks_total': checks.get('requiredChecks'),
        'checks_failed': checks.get('failedRequiredChecks'),
        'checks_source': 'delivery/data/verification_results.json (last delivery verification, NOT rerun by pytest)',
        'status': 'passed' if exitstatus == 0 else 'failed',
        'passed': passed, 'failed': failed, 'skipped': skipped,
        'total_tests': session.testscollected,
        'total_checks': checks.get('requiredChecks'),
        'failed_checks': checks.get('failedRequiredChecks'),
    }
    target = ROOT / 'delivery/linux-stand/test_report.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
