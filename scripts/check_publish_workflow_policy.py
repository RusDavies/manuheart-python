"""Policy checks for the GitHub Actions publish workflow."""

from __future__ import annotations

import re
from pathlib import Path

WORKFLOW_DIR = Path(".github/workflows")
PUBLISH_WORKFLOW = WORKFLOW_DIR / "publish.yml"
FULL_SHA_REF = re.compile(r"^[^\s@]+/[^\s@]+@[0-9a-f]{40}$")
USES_LINE = re.compile(r"^(?P<indent>\s*)uses:\s*(?P<ref>\S+)\s*$")
REQUIRED_SNIPPETS = (
    "Verify release tag matches package version",
    "if: github.event_name == 'release'",
    "github.event.release.tag_name",
    "tomllib.load(handle)[\"project\"][\"version\"]",
    "expected = f\"v{version}\"",
    "tag != expected",
    "Install pinned OSV Scanner",
    "python scripts/install_osv_scanner.py --destination .tools/osv-scanner",
    "Run OSV Scanner dependency and manifest gate",
    "python scripts/check_osv_scanner.py",
    "environment: pypi",
    "id-token: write",
    "pypa/gh-action-pypi-publish@cef221092ed1bacb1cc03d23a2d87d1d172e277b",
)


def workflow_files() -> list[Path]:
    if not WORKFLOW_DIR.exists():
        return []
    return sorted(
        path
        for pattern in ("*.yml", "*.yaml")
        for path in WORKFLOW_DIR.glob(pattern)
        if path.is_file()
    )


def find_moving_uses_refs() -> list[str]:
    failures: list[str] = []
    for path in workflow_files():
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            match = USES_LINE.match(line)
            if not match:
                continue
            ref = match.group("ref")
            if not FULL_SHA_REF.match(ref):
                failures.append(f"{path}:{line_number}: uses: {ref}")
    return failures


def main() -> int:
    text = PUBLISH_WORKFLOW.read_text(encoding="utf-8")
    missing = [snippet for snippet in REQUIRED_SNIPPETS if snippet not in text]
    moving_refs = find_moving_uses_refs()
    if missing or moving_refs:
        print("publish workflow policy check failed")
        if missing:
            print("missing required snippet(s):")
            for snippet in missing:
                print(f"- {snippet}")
        if moving_refs:
            print("workflow uses entries must be pinned to full 40-character SHAs:")
            for failure in moving_refs:
                print(f"- {failure}")
        return 1
    print("publish workflow policy check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
