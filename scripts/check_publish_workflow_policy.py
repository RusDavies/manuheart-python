"""Policy checks for the GitHub Actions publish workflow."""

from __future__ import annotations

from pathlib import Path

WORKFLOW = Path(".github/workflows/publish.yml")
REQUIRED_SNIPPETS = (
    "Verify release tag matches package version",
    "if: github.event_name == 'release'",
    "github.event.release.tag_name",
    "tomllib.load(handle)[\"project\"][\"version\"]",
    "expected = f\"v{version}\"",
    "tag != expected",
    "environment: pypi",
    "id-token: write",
    "pypa/gh-action-pypi-publish@release/v1",
)


def main() -> int:
    text = WORKFLOW.read_text(encoding="utf-8")
    missing = [snippet for snippet in REQUIRED_SNIPPETS if snippet not in text]
    if missing:
        print("publish workflow policy check failed; missing required snippet(s):")
        for snippet in missing:
            print(f"- {snippet}")
        return 1
    print("publish workflow policy check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
