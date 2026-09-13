"""Recording metadata and credential handling; all requests here are simulated.

Scenarios: Recording provenance is verifiable; Re-recording is deliberate.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

from scripts import record_fixtures
from sobres import config


def test_manifest_binds_payload_bytes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(record_fixtures, "ROOT", tmp_path)
    out = tmp_path / "fred"
    out.mkdir()
    payload = b'{"observations": []}\r\n'
    (out / "DGS10.json").write_bytes(payload)
    (out / "meta.json").write_text("old metadata", encoding="utf-8")
    meta = json.loads(record_fixtures._meta("fred", source="https://api.stlouisfed.org/fred"))
    assert meta["sha256"] == {"DGS10.json": hashlib.sha256(payload).hexdigest()}
    assert meta["client"] == "httpx" and meta["client_version"] == httpx.__version__
    assert meta["recorded_at"] and meta["provider_version"] == "unversioned"
    (out / "DGS10.json").write_bytes(payload + b" ")
    assert (
        hashlib.sha256((out / "DGS10.json").read_bytes()).hexdigest()
        != meta["sha256"]["DGS10.json"]
    )


def test_recorder_reads_declared_key_without_echo(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    key = "RECORDING-DUMMY-SECRET"
    monkeypatch.setattr(config, "resolve", lambda: SimpleNamespace(get=lambda _: key))
    calls = []
    monkeypatch.setattr(record_fixtures, "record_fred", lambda *args: calls.append(args))
    assert (
        record_fixtures.main(["--only", "fred", "--start", "2020-01-01", "--end", "2020-01-31"])
        == 0
    )
    assert calls == [(date(2020, 1, 1), date(2020, 1, 31), key)]
    captured = capsys.readouterr()
    assert key not in captured.out + captured.err


@pytest.mark.parametrize("status", [403, 500])
def test_recording_http_failure_never_prints_key(
    status: int, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    key = "RECORDING-DUMMY-SECRET"
    monkeypatch.setattr(record_fixtures, "ROOT", tmp_path)
    monkeypatch.setattr(config, "resolve", lambda: SimpleNamespace(get=lambda _: key))
    response = httpx.Response(
        status, request=httpx.Request("GET", f"https://example.test/?api_key={key}")
    )
    monkeypatch.setattr(httpx, "get", lambda *args, **kwargs: response)
    assert record_fixtures.main(["--only", "fred"]) == 1
    captured = capsys.readouterr()
    assert key not in captured.out + captured.err
    assert "FRED recording failed" in captured.err
    assert not (tmp_path / "fred" / "meta.json").exists()
