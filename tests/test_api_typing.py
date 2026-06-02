from __future__ import annotations

from typing import get_type_hints

import manuheart.api as api
from manuheart.api import (
    CheckerMap,
    ClockSource,
    ConfigOverrides,
    ConfigOverridesInput,
    DaemonEventCallback,
    SleepFunction,
)


def test_public_api_exports_extension_point_types():
    assert CheckerMap is not None
    assert ClockSource is not None
    assert ConfigOverrides is not None
    assert ConfigOverridesInput is not None
    assert DaemonEventCallback is not None
    assert SleepFunction is not None


def test_public_api_signatures_use_named_extension_types():
    run_check_hints = get_type_hints(api.run_check)
    run_from_config_hints = get_type_hints(api.run_check_from_config)
    daemon_hints = get_type_hints(api.run_daemon)
    load_hints = get_type_hints(api.load_config)

    assert run_check_hints["checkers"] == CheckerMap | None
    assert run_check_hints["clock"] == ClockSource | None
    assert run_from_config_hints["overrides"] == ConfigOverridesInput | None
    assert daemon_hints["checkers"] == CheckerMap | None
    assert daemon_hints["clock"] == ClockSource | None
    assert daemon_hints["sleep"] == SleepFunction | None
    assert daemon_hints["on_event"] == DaemonEventCallback | None
    assert load_hints["overrides"] == ConfigOverridesInput | None
