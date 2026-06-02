import json
import subprocess
import sys

from manuheart.api import CheckResult, CheckType, load_config, run_check, run_daemon, write_reports
from manuheart.models import (
    ConfigOverrides,
    HostState,
    PreviousStateSnapshot,
    ReportDestinations,
    Status,
)


class FakeChecker:
    def __init__(self, healthy):
        self.healthy = healthy

    def check(self, host, group):
        return CheckResult(self.healthy, "fake")


def test_api_overrides_take_precedence(tmp_path):
    loaded = load_config(
        "examples/localhost/manuheart.json",
        overrides={
            "var_dir": tmp_path / "var",
            "check_period": 42,
            "host_status_file": tmp_path / "hoststatus",
        },
    )
    assert loaded.effective.var_dir == tmp_path / "var"
    assert loaded.effective.check_period == 42
    assert loaded.effective.reports.hosts == tmp_path / "hoststatus"


def test_config_overrides_dataclass_supported(tmp_path):
    loaded = load_config(
        "examples/localhost/manuheart.json",
        overrides=ConfigOverrides(group_status_file=tmp_path / "groupstatus"),
    )
    assert loaded.effective.reports.groups == tmp_path / "groupstatus"


def test_previous_state_is_loaded_for_fail_count(tmp_path):
    loaded = load_config(
        "examples/localhost/manuheart.json",
        overrides={
            "host_status_file": tmp_path / "hoststatus",
            "group_status_file": tmp_path / "groupstatus",
            "system_status_file": tmp_path / "sysstatus",
        },
    )
    first = run_check(loaded, checkers={CheckType.ICMP: FakeChecker(False)}, clock=lambda: "t1")
    write_reports(first)
    second = run_check(loaded, checkers={CheckType.ICMP: FakeChecker(False)}, clock=lambda: "t2")
    assert second.hosts["localhost-icmp/127.0.0.1"].fail_count == 2
    assert second.systems["localhost-system"].failure_count == 2


def test_run_check_can_skip_disk_previous_state(tmp_path):
    loaded = load_config(
        "examples/localhost/manuheart.json",
        overrides={"host_status_file": tmp_path / "hoststatus"},
    )
    loaded.effective.reports.hosts.write_text("not-json")

    result = run_check(
        loaded,
        checkers={CheckType.ICMP: FakeChecker(False)},
        clock=lambda: "t1",
        load_previous=False,
    )

    assert not any("invalid JSON" in warning for warning in result.warnings)
    assert result.hosts["localhost-icmp/127.0.0.1"].fail_count == 1


def test_run_check_accepts_injected_previous_state(tmp_path):
    loaded = load_config(
        "examples/localhost/manuheart.json",
        overrides={"host_status_file": tmp_path / "hoststatus"},
    )
    previous = PreviousStateSnapshot(
        hosts={
            "localhost-icmp/127.0.0.1": HostState(
                name="127.0.0.1",
                group="localhost-icmp",
                url="n/a",
                fail_count=3,
            )
        },
        warnings=("injected previous warning",),
    )

    result = run_check(
        loaded,
        checkers={CheckType.ICMP: FakeChecker(False)},
        clock=lambda: "t1",
        previous_state=previous,
    )

    assert result.hosts["localhost-icmp/127.0.0.1"].fail_count == 4
    assert "injected previous warning" in result.warnings


def test_log_file_records_check_and_report_events(tmp_path):
    log_file = tmp_path / "manuheart.log"
    loaded = load_config(
        "examples/localhost/manuheart.json",
        overrides={
            "log_file": log_file,
            "log_level": 2,
            "host_status_file": tmp_path / "hoststatus",
            "group_status_file": tmp_path / "groupstatus",
            "system_status_file": tmp_path / "sysstatus",
        },
    )

    result = run_check(loaded, checkers={CheckType.ICMP: FakeChecker(True)}, clock=lambda: "t1")
    write_reports(result)

    log_text = log_file.read_text()
    assert f"check run {result.run_id} completed" in log_text
    assert f"check run {result.run_id} reports written" in log_text


def test_cli_writes_reports_with_overrides(tmp_path):
    hoststatus = tmp_path / "hoststatus"
    groupstatus = tmp_path / "groupstatus"
    sysstatus = tmp_path / "sysstatus"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "manuheart",
            "check",
            "--config",
            "examples/localhost/manuheart.json",
            "--host-status-file",
            str(hoststatus),
            "--group-status-file",
            str(groupstatus),
            "--sys-status-file",
            str(sysstatus),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert json.loads(hoststatus.read_text())["hosts"]
    assert json.loads(groupstatus.read_text())["groups"]
    assert json.loads(sysstatus.read_text())["systems"]


def test_cli_validate_config_uses_api():
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "manuheart",
            "validate-config",
            "--config",
            "examples/localhost/manuheart.json",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0


def test_daemon_max_cycles_for_bounded_smoke(tmp_path):
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "manuheart",
            "daemon",
            "--config",
            "examples/localhost/manuheart.json",
            "--max-cycles",
            "1",
            "--host-status-file",
            str(tmp_path / "hoststatus"),
            "--group-status-file",
            str(tmp_path / "groupstatus"),
            "--sys-status-file",
            str(tmp_path / "sysstatus"),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert "daemon cycle 1 completed" in completed.stderr
    assert "daemon stopped after 1 cycle" in completed.stderr


def test_run_daemon_emits_events_and_stops_cleanly_on_keyboard_interrupt(tmp_path):
    loaded = load_config(
        "examples/localhost/manuheart.json",
        overrides={
            "host_status_file": tmp_path / "hoststatus",
            "group_status_file": tmp_path / "groupstatus",
            "system_status_file": tmp_path / "sysstatus",
        },
    )
    events = []

    def interrupt(_seconds):
        raise KeyboardInterrupt

    cycles = run_daemon(
        loaded,
        checkers={CheckType.ICMP: FakeChecker(True)},
        clock=lambda: "t1",
        sleep=interrupt,
        on_event=events.append,
    )

    assert cycles == 1
    assert events == [
        "daemon starting",
        "daemon cycle 1 completed",
        "daemon stopped after 1 cycle",
    ]


def test_cli_check_reports_operational_errors_without_traceback(tmp_path):
    hoststatus_dir = tmp_path / "hoststatus"
    hoststatus_dir.mkdir()
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "manuheart",
            "check",
            "--config",
            "examples/localhost/manuheart.json",
            "--host-status-file",
            str(hoststatus_dir),
            "--group-status-file",
            str(tmp_path / "groupstatus"),
            "--sys-status-file",
            str(tmp_path / "sysstatus"),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 1
    assert "ERROR:" in completed.stderr
    assert "Traceback" not in completed.stderr


def test_cli_check_prints_previous_state_warnings(tmp_path):
    hoststatus = tmp_path / "hoststatus"
    groupstatus = tmp_path / "groupstatus"
    sysstatus = tmp_path / "sysstatus"
    hoststatus.write_text("not-json")
    groupstatus.write_text(json.dumps({"groups": []}))
    sysstatus.write_text(json.dumps({"systems": []}))

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "manuheart",
            "check",
            "--config",
            "examples/localhost/manuheart.json",
            "--host-status-file",
            str(hoststatus),
            "--group-status-file",
            str(groupstatus),
            "--sys-status-file",
            str(sysstatus),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert "WARNING:" in completed.stderr
    assert "invalid JSON; ignoring" in completed.stderr
    assert "Traceback" not in completed.stderr


def test_cli_daemon_reports_config_errors_without_traceback():
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "manuheart",
            "daemon",
            "--config",
            "does-not-exist.json",
            "--max-cycles",
            "1",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 1
    assert "ERROR:" in completed.stderr
    assert "does-not-exist.json" in completed.stderr
    assert "Traceback" not in completed.stderr


def test_status_type_from_previous_state_preserves_up_during_grace(tmp_path):
    destinations = ReportDestinations(
        hosts=tmp_path / "hoststatus",
        groups=tmp_path / "groupstatus",
        systems=tmp_path / "sysstatus",
    )
    loaded = load_config(
        "examples/localhost/manuheart.json",
        overrides={
            "host_status_file": destinations.hosts,
            "group_status_file": destinations.groups,
            "system_status_file": destinations.systems,
        },
    )
    first = run_check(loaded, checkers={CheckType.ICMP: FakeChecker(True)}, clock=lambda: "t1")
    write_reports(first, destinations)
    second = run_check(loaded, checkers={CheckType.ICMP: FakeChecker(False)}, clock=lambda: "t2")
    assert second.hosts["localhost-icmp/127.0.0.1"].status == Status.UP
    assert second.hosts["localhost-icmp/127.0.0.1"].fail_count == 1
