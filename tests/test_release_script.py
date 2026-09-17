"""Contract tests for ``.github/scripts/check_release.py``.

The script's stdout is appended to ``$GITHUB_OUTPUT``, which accepts only
``key=value`` lines and fails the job on anything else. These tests run every
decision path with the index call stubbed and assert that contract, so a stray
informational print can never again turn a push to ``main`` red.
"""

from __future__ import annotations

import importlib.util
import re
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / ".github" / "scripts" / "check_release.py"

# What $GITHUB_OUTPUT will accept: a bare key, "=", then anything.
OUTPUT_LINE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=.*$")


def load_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location("check_release", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    *,
    target: str,
    index: Callable[[str, str], set[str] | None],
) -> tuple[dict[str, str], str]:
    """Run ``main()`` and return parsed stdout outputs plus raw stderr."""
    module = load_script()
    monkeypatch.setenv("TARGET", target)
    monkeypatch.delenv("RELEASE_ENABLED", raising=False)
    monkeypatch.setattr(module, "released_versions", index)
    module.main()
    out, err = capsys.readouterr()

    lines = [line for line in out.splitlines() if line.strip()]
    for line in lines:
        message = f"stdout line is not key=value and would fail $GITHUB_OUTPUT: {line!r}"
        assert OUTPUT_LINE.match(line), message
    return dict(line.split("=", 1) for line in lines), err


def test_no_arming_variable_can_suppress_a_publish(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: The version alone decides; an arming variable cannot veto it."""
    monkeypatch.setenv("RELEASE_ENABLED", "false")
    outputs, _ = run(monkeypatch, capsys, target="pypi", index=lambda *_: None)
    assert outputs["publish"] == "true"
    assert outputs["reason"] == "new-version"
    assert "RELEASE_ENABLED" not in SCRIPT.read_text(encoding="utf-8")


def test_first_release_publishes(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    outputs, _ = run(monkeypatch, capsys, target="pypi", index=lambda *_: None)
    assert outputs["publish"] == "true"
    assert outputs["reason"] == "new-version"


def test_existing_version_publishes_nothing(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: An existing version is reported as already published."""
    from sobres import __version__

    outputs, err = run(monkeypatch, capsys, target="pypi", index=lambda *_: {__version__})
    assert outputs["publish"] == "false"
    assert "already on pypi" in err
    assert outputs["reason"] == "already-published"


def test_testpypi_rehearsal_publishes(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    outputs, _ = run(monkeypatch, capsys, target="testpypi", index=lambda *_: None)
    assert outputs["publish"] == "true"
    assert outputs["reason"] == "new-version"
    assert outputs["target"] == "testpypi"


def test_every_mode_emits_exactly_the_four_outputs(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    for target in ("pypi", "testpypi"):
        outputs, _ = run(monkeypatch, capsys, target=target, index=lambda *_: None)
        assert set(outputs) == {"version", "target", "publish", "reason"}, (target, outputs)


def test_upload_token_is_selected_by_index_without_value_fallback() -> None:
    """A missing test secret cannot select the production credential."""
    import yaml

    workflow = yaml.safe_load(
        (REPO_ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
    )
    job = workflow["jobs"]["publish"]
    assert "id-token" not in job.get("permissions", {})
    upload = next(step for step in job["steps"] if step.get("name") == "Publish")
    assert upload["with"]["password"] == (
        "${{ secrets[needs.decide.outputs.target == 'testpypi' && 'PYPI_TEST' || 'PYPI_PROD'] }}"
    )
    assert upload["with"]["attestations"] is False
