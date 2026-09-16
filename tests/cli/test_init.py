"""``sobres init`` — the guided wizard.

Scenarios: Guided, in the terminal; Idempotent and re-runnable; Optional
settings can be skipped; Live validation with consent; Storage is set up;
Non-interactive mode; Ends with proof; Time to first result; The three-command
path is a test.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from sobres.cli.commands.init import InitParams, init
from sobres.cli.context import Context
from sobres.core.errors import ConfigurationError
from sobres.settings import LiveResult, Setting, all_settings, get_setting


def test_non_interactive_writes_config_sets_up_storage_and_runs_doctor(
    cli: Callable[..., Any], env: dict[str, str]
) -> None:
    result = cli("init", "--non-interactive", "--offline", "--format", "json")
    assert result.exit_code == 0, result.stderr
    doc = json.loads(result.stdout)
    assert doc["config_path"] == env["SOBRES_CONFIG_FILE"]
    assert doc["db_location"].endswith("sobres.db")
    assert Path(doc["config_path"]).exists() and Path(doc["db_location"]).exists()
    assert doc["first_command"].startswith("sobres data prices")
    assert {c["name"] for c in doc["checks"]} >= {"python-version", "db-schema", "config-file"}
    assert not any(c["status"] == "fail" for c in doc["checks"])
    table = cli("init", "--non-interactive", "--offline", "--format", "table")
    assert "try next: sobres data prices" in table.stdout and "database:" in table.stdout


def test_rerun_without_changes_is_byte_identical(
    cli: Callable[..., Any], env: dict[str, str]
) -> None:
    cli("init", "--non-interactive", "--offline", "--set", "fred_api_key=ABCD1234")
    path = Path(env["SOBRES_CONFIG_FILE"])
    before = path.read_bytes()
    result = cli("init", "--non-interactive", "--offline", "--format", "json")
    assert result.exit_code == 0
    assert path.read_bytes() == before
    doc = json.loads(result.stdout)
    assert doc["changed"] == [] and doc["first_command"].startswith("sobres data macro")


def test_non_interactive_takes_values_from_environment(
    cli: Callable[..., Any], env: dict[str, str]
) -> None:
    result = cli(
        "init",
        "--non-interactive",
        "--offline",
        "--format",
        "json",
        env_extra={"SOBRES_LOG_LEVEL": "INFO"},
    )
    assert "log_level" in json.loads(result.stdout)["changed"]
    assert 'log_level = "INFO"' in Path(env["SOBRES_CONFIG_FILE"]).read_text(encoding="utf-8")


def test_non_interactive_missing_required_exits_3_naming_it(
    make_context: Callable[..., Context],
) -> None:
    from sobres import settings as reg

    required = Setting(key="zz_required", env="SOBRES_ZZ_REQUIRED", description="d", required=True)
    reg._REGISTRY[required.key] = required
    try:
        with pytest.raises(ConfigurationError) as exc:
            init(InitParams(non_interactive=True, offline=True), make_context())
        assert exc.value.exit_code == 3
        assert "zz_required" in str(exc.value) and "SOBRES_ZZ_REQUIRED" in str(exc.value)
    finally:
        del reg._REGISTRY[required.key]


def test_bad_set_syntax_and_value(cli: Callable[..., Any]) -> None:
    assert cli("init", "--non-interactive", "--offline", "--set", "nonsense").exit_code == 3
    assert cli("init", "--non-interactive", "--offline", "--set", "log_level=LOUD").exit_code == 3


class _Wizard:
    """Scripted answers for the interactive path: prompts and confirmations in order."""

    def __init__(self, answers: dict[str, list[str]], confirms: dict[str, list[bool]]) -> None:
        self.answers, self.confirms = answers, confirms
        self.seen: list[str] = []

    def prompt(self, question: str, secret: bool) -> str:
        self.seen.append(question)
        for key, values in self.answers.items():
            if key in question and values:
                return values.pop(0)
        return ""

    def confirm(self, question: str) -> bool:
        self.seen.append(question)
        for key, values in self.confirms.items():
            if key in question and values:
                return values.pop(0)
        return False


def _interactive(make_context: Callable[..., Context], wizard: _Wizard, **kw: Any) -> Context:
    ctx = make_context(prompt=wizard.prompt, confirm=wizard.confirm, **kw)
    ctx.interactive = True
    return ctx


def test_guided_wizard_asks_only_essential_settings(
    make_context: Callable[..., Context], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: Guided, in the terminal (0014) — advanced settings are not asked."""
    fred = get_setting("fred_api_key")
    monkeypatch.setattr(fred, "validate_live", lambda v: LiveResult(True, "FRED accepted the key"))
    wizard = _Wizard({"fred_api_key": ["K1"], "log_level": ["INFO"]}, {"verify it": [True]})
    ctx = _interactive(make_context, wizard)
    err = __import__("io").StringIO()
    ctx.stderr = err
    report = init(InitParams(offline=True), ctx)
    assert report.exit_code == 0
    assert report.changed == ["fred_api_key"]  # log_level was never asked
    walked = [q for q in wizard.seen if any(q.strip().startswith(s.key) for s in all_settings())]
    assert [q.strip().split(" ")[0] for q in walked] == ["fred_api_key"]
    advanced = sum(1 for s in all_settings() if s.advanced)
    assert f"{advanced} advanced settings were not asked" in err.getvalue()
    assert "sobres init --advanced" in err.getvalue()


def test_advanced_setting_survives_a_default_run(
    make_context: Callable[..., Context], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: Advanced settings survive a default run (0014)."""
    fred = get_setting("fred_api_key")
    monkeypatch.setattr(fred, "validate_live", lambda v: LiveResult(True, "ok"))
    first = _interactive(
        make_context,
        _Wizard({"fred_api_key": ["K1"], "log_level": ["DEBUG"]}, {"verify it": [True]}),
    )
    init(InitParams(offline=True, advanced=True), first)
    assert 'log_level = "DEBUG"' in first.config.path.read_text(encoding="utf-8")
    again = _interactive(make_context, _Wizard({}, {"replace it": [False]}))
    report = init(InitParams(offline=True), again)
    assert report.changed == []
    assert 'log_level = "DEBUG"' in again.config.path.read_text(encoding="utf-8")


@pytest.mark.parametrize("secret_value", ["Z9!", "Q7$!", "SECRET9999"])
def test_advanced_flag_walks_every_setting_and_masks_secrets(
    make_context: Callable[..., Context], monkeypatch: pytest.MonkeyPatch, secret_value: str
) -> None:
    """Scenario: Advanced settings on request (0014); Secret displays (0012)."""
    fred = get_setting("fred_api_key")
    monkeypatch.setattr(fred, "validate_live", lambda v: LiveResult(True, "FRED accepted the key"))
    wizard = _Wizard({"fred_api_key": [secret_value], "log_level": ["INFO"]}, {"verify it": [True]})
    ctx = _interactive(make_context, wizard)
    report = init(InitParams(offline=True, advanced=True), ctx)
    assert "fred_api_key" in report.changed and "log_level" in report.changed
    assert report.exit_code == 0
    assert (
        len([q for q in wizard.seen if "(enter to skip)" in q or q.strip().startswith("fred")]) >= 1
    )
    # every declared setting was walked, in order
    walked = [q for q in wizard.seen if any(q.strip().startswith(s.key) for s in all_settings())]
    assert [q.strip().split(" ")[0] for q in walked] == [s.key for s in all_settings()]
    text = ctx.config.path.read_text(encoding="utf-8")
    assert f'fred_api_key = "{secret_value}"' in text
    # re-run: current values are shown masked and kept when not replaced
    wizard2 = _Wizard({}, {"replace it": [False]})
    ctx2 = _interactive(make_context, wizard2)
    err = __import__("io").StringIO()
    ctx2.stderr = err
    report2 = init(InitParams(offline=True, advanced=True), ctx2)
    assert report2.changed == []
    assert "current: ****" in err.getvalue()
    assert secret_value not in err.getvalue()


def test_failed_live_validation_never_stores_silently(
    make_context: Callable[..., Context], monkeypatch: pytest.MonkeyPatch
) -> None:
    fred = get_setting("fred_api_key")
    monkeypatch.setattr(fred, "validate_live", lambda v: LiveResult(v == "GOOD", f"{v} checked"))
    # retry once with a bad key, then a good one
    wizard = _Wizard(
        {"fred_api_key": ["BAD", "GOOD"], "[r]etry": ["r"]}, {"verify it": [True, True]}
    )
    ctx = _interactive(make_context, wizard)
    init(InitParams(offline=True), ctx)
    assert 'fred_api_key = "GOOD"' in ctx.config.path.read_text(encoding="utf-8")
    # skip after a failure: nothing stored
    ctx.config.path.unlink()
    wizard = _Wizard({"fred_api_key": ["BAD"], "[r]etry": ["s"]}, {"verify it": [True]})
    ctx = _interactive(make_context, wizard)
    init(InitParams(offline=True), ctx)
    assert "fred_api_key" not in ctx.config.path.read_text(encoding="utf-8")
    # keep anyway is an explicit choice
    ctx.config.path.unlink()
    wizard = _Wizard({"fred_api_key": ["BAD"], "[r]etry": ["k"]}, {"verify it": [True]})
    ctx = _interactive(make_context, wizard)
    init(InitParams(offline=True), ctx)
    assert 'fred_api_key = "BAD"' in ctx.config.path.read_text(encoding="utf-8")


def test_optional_setting_skipped_names_affected_commands(
    make_context: Callable[..., Context],
) -> None:
    wizard = _Wizard({}, {})
    ctx = _interactive(make_context, wizard)
    err = __import__("io").StringIO()
    ctx.stderr = err
    report = init(InitParams(offline=True), ctx)
    assert report.changed == []
    assert "without it: data.macro" in err.getvalue()
    assert "obtain: https://fred.stlouisfed.org" in err.getvalue()


def test_invalid_interactive_value_is_re_prompted(make_context: Callable[..., Context]) -> None:
    wizard = _Wizard({"log_level": ["LOUD", "ERROR"]}, {})
    ctx = _interactive(make_context, wizard)
    init(InitParams(offline=True, advanced=True), ctx)  # log_level is an advanced setting
    assert 'log_level = "ERROR"' in ctx.config.path.read_text(encoding="utf-8")


def test_ends_by_running_doctor(cli: Callable[..., Any]) -> None:
    result = cli("init", "--non-interactive", "--offline", "--format", "table")
    assert "python-version" in result.stdout and " ok," in result.stdout


def test_real_prompt_accepts_empty_input(
    cli: Callable[..., Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: Empty optional wizard input (0012): exercise real Typer prompts."""
    original_build = Context.build

    def interactive_build(*args: Any, **kwargs: Any) -> Context:
        context = original_build(*args, **kwargs)
        context.interactive = True  # CliRunner's input stream is not a physical terminal.
        return context

    monkeypatch.setattr(Context, "build", interactive_build)
    result = cli("init", "--offline", input="\n" * len(all_settings()))
    assert result.exit_code == 0, result.output
    assert result.stdout.count("fred_api_key (enter to skip):") == 1
    assert "try next: sobres data prices" in result.stdout
    assert "skipped; without it: data.macro" in result.stderr


def test_init_propagates_failed_doctor(
    cli: Callable[..., Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: Init health status propagation (0012)."""
    from sobres import doctor as doc

    failing = doc.Check(
        "test-failure", "runtime", lambda _: doc.CheckResult("fail", "failed", "repair it")
    )
    monkeypatch.setattr(doc, "_CHECKS", [*doc.all_checks(), failing])
    result = cli("init", "--non-interactive", "--offline", "--format", "json")
    report = json.loads(result.stdout)
    assert report["summary"]["fail"] == 1
    assert report["exit_code"] == result.exit_code == 1


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX file modes")
def test_unchanged_init_repairs_permissions(cli: Callable[..., Any], env: dict[str, str]) -> None:
    cli("init", "--non-interactive", "--offline")
    path = Path(env["SOBRES_CONFIG_FILE"])
    original = path.read_bytes()
    path.chmod(0o644)
    result = cli("init", "--non-interactive", "--offline", "--format", "json")
    assert result.exit_code == 0, result.stderr
    assert path.stat().st_mode & 0o777 == 0o600
    assert path.read_bytes() == original
    assert json.loads(result.stdout)["summary"]["fail"] == 0


def test_no_verify_option(cli: Callable[..., Any]) -> None:
    """Scenario: Negative boolean options (0012)."""
    result = cli("init", "--non-interactive", "--no-verify", "--offline", "--format", "json")
    assert result.exit_code == 0, result.stderr


@pytest.mark.parametrize(
    "option, expected", [(None, True), ("--verify", True), ("--no-verify", False)]
)
def test_verification_boolean_reaches_handler(
    cli: Callable[..., Any], monkeypatch: pytest.MonkeyPatch, option: str | None, expected: bool
) -> None:
    actual: list[bool] = []
    original = InitParams.model_validate

    def capture(*args: Any, **kwargs: Any) -> InitParams:
        params = original(*args, **kwargs)
        actual.append(params.verify)
        return params

    monkeypatch.setattr(InitParams, "model_validate", staticmethod(capture))
    result = cli("init", "--non-interactive", "--offline", *([option] if option else []))
    assert result.exit_code == 0, result.stderr
    assert actual == [expected]
