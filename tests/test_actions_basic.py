"""Smoke tests por acción que no requieren GUI ni red."""
from __future__ import annotations

import pytest

from actions import filesystem, rules, screen, system, ui


def test_ensure_directory_creates(tmp_path):
    target = tmp_path / "nuevo"
    out = filesystem.ensure_directory(str(target))
    assert out["exists"] and target.is_dir()


def test_list_directory_counts_files(tmp_path):
    (tmp_path / "a.txt").write_text("hola")
    (tmp_path / "b.md").write_text("xy")
    out = filesystem.list_directory(str(tmp_path))
    assert out["total_files"] == 2
    extensions = {item["extension"] for item in out["files"]}
    assert {".txt", ".md"} <= extensions


def test_classify_inventory_aggregates():
    files = [
        {"name": "a.txt", "extension": ".txt", "size_bytes": 100},
        {"name": "b.txt", "extension": ".txt", "size_bytes": 50},
        {"name": "big.bin", "extension": ".bin", "size_bytes": 9999},
    ]
    out = filesystem.classify_file_inventory(files)
    assert out["total_files"] == 3
    assert out["by_extension"][".txt"] == 2
    assert out["largest_file"]["name"] == "big.bin"


def test_write_json_roundtrip(tmp_path):
    target = tmp_path / "out.json"
    filesystem.write_json(str(target), {"a": 1})
    assert target.exists()
    assert '"a": 1' in target.read_text(encoding="utf-8")


def test_rules_evaluate_first_match_wins():
    decision = rules.evaluate_rules(
        input_data={"snapshot": {"memory_percent": 92}},
        rules=[
            {"id": "mem_alta", "path": "snapshot.memory_percent", "operator": "gt", "value": 85, "status": "alerta"},
        ],
        default_status="ok",
    )
    assert decision["status"] == "alerta"
    assert decision["matched_rule"]["id"] == "mem_alta"


def test_rules_evaluate_default_when_no_match():
    decision = rules.evaluate_rules(
        input_data={"snapshot": {"memory_percent": 10}},
        rules=[
            {"id": "mem_alta", "path": "snapshot.memory_percent", "operator": "gt", "value": 85, "status": "alerta"},
        ],
        default_status="ok",
    )
    assert decision["status"] == "ok"


def test_system_wait_zero():
    assert system.wait_seconds(0)["waited_seconds"] == 0


def test_ui_launch_process_dry_run():
    out = ui.launch_process("echo hola", dry_run=True)
    assert out["dry_run"] is True
    assert out["launched"] is False


def test_ui_launch_process_empty_raises():
    with pytest.raises(ValueError):
        ui.launch_process("", dry_run=True)


def test_ui_hotkey_dry_run():
    out = ui.hotkey(["ctrl", "s"], dry_run=True)
    assert out["dry_run"] is True


def test_ui_click_dry_run():
    out = ui.click(10, 20, dry_run=True)
    assert out["dry_run"] is True


def test_ui_click_bbox_centers():
    out = ui.click_bbox({"left": 0, "top": 0, "width": 100, "height": 50}, dry_run=True)
    assert out["x"] == 50 and out["y"] == 25


def test_resolve_bbox_absolute():
    assert screen._resolve_bbox({"left": 10, "top": 20, "width": 100, "height": 50}, 1920, 1080) == (10, 20, 100, 50)


def test_resolve_bbox_negative_anchors_to_opposite_edge():
    # top=-48 sobre monitor 1080 → top=1032
    assert screen._resolve_bbox({"left": 0, "top": -48, "width": 1920, "height": 48}, 1920, 1080) == (0, 1032, 1920, 48)


def test_resolve_bbox_right_bottom_form():
    assert screen._resolve_bbox({"left": 100, "top": 50, "right": 300, "bottom": 200}, 1920, 1080) == (100, 50, 200, 150)


def test_resolve_bbox_clamps_to_screen():
    # width 99999 sobre monitor 1920 → 1920
    assert screen._resolve_bbox({"left": 0, "top": 0, "width": 99999, "height": 99999}, 1920, 1080) == (0, 0, 1920, 1080)


def test_resolve_bbox_rejects_invalid():
    with pytest.raises(ValueError):
        screen._resolve_bbox({"left": 0, "top": 0, "width": 0, "height": 10}, 1920, 1080)


def test_read_clipboard_truncates(monkeypatch):
    import actions.system as sysmod

    fake = type("F", (), {"paste": staticmethod(lambda: "x" * 50)})
    monkeypatch.setitem(__import__("sys").modules, "pyperclip", fake)
    out = sysmod.read_clipboard(max_chars=10)
    assert out["available"] is True
    assert out["length"] == 50
    assert out["truncated"] is True
    assert out["text"] == "x" * 10


def test_run_powershell_rejects_chain_tokens():
    from actions import system as sysmod

    with pytest.raises(ValueError, match="prohibido"):
        sysmod.run_powershell("Get-Date; Remove-Item C:\\foo")


def test_run_powershell_rejects_non_allowlisted():
    from actions import system as sysmod

    with pytest.raises(ValueError, match="allowlist"):
        sysmod.run_powershell("Remove-Item C:\\foo")


def test_run_powershell_accepts_custom_allowlist(monkeypatch):
    from actions import system as sysmod

    calls = {}

    class FakeProc:
        returncode = 0
        stdout = "ok"
        stderr = ""

    def fake_run(args, **kwargs):
        calls["args"] = args
        return FakeProc()

    import subprocess

    monkeypatch.setattr(subprocess, "run", fake_run)
    out = sysmod.run_powershell("Write-Host hola", allowlist=["Write-Host"])
    assert out["exit_code"] == 0 and out["stdout"] == "ok"
    assert "Write-Host" in calls["args"][-1]


def test_read_clipboard_handles_missing_backend(monkeypatch):
    import actions.system as sysmod

    class BoomPyperclip:
        @staticmethod
        def paste():
            raise RuntimeError("no display")

    monkeypatch.setitem(__import__("sys").modules, "pyperclip", BoomPyperclip)
    out = sysmod.read_clipboard()
    assert out["available"] is False
    assert "no display" in out["reason"]


def test_data_dir_equals_root_in_dev_mode():
    from engine.paths import data_dir, root_dir
    # Sin AUTOMA_DATA_ROOT ni _MEIPASS, ambos coinciden con el repo.
    assert data_dir() == root_dir()


def test_data_dir_honors_env_override(tmp_path, monkeypatch):
    from engine import paths

    target = tmp_path / "custom-data"
    monkeypatch.setenv("AUTOMA_DATA_ROOT", str(target))
    out = paths.data_dir()
    assert out == target.resolve()
    assert target.is_dir()


def test_data_dir_frozen_uses_localappdata(monkeypatch, tmp_path):
    from engine import paths

    monkeypatch.delenv("AUTOMA_DATA_ROOT", raising=False)
    monkeypatch.setattr(paths, "_is_frozen", lambda: True)
    monkeypatch.setattr(paths.sys, "platform", "win32")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    out = paths.data_dir()
    assert out == (tmp_path / "Automa").resolve()
    assert (tmp_path / "Automa").is_dir()


def test_desktop_port_open_returns_false_for_closed_port():
    from app import desktop
    assert desktop._port_open("127.0.0.1", 1, timeout=0.1) is False


def test_desktop_wait_for_server_times_out():
    from app import desktop
    assert desktop._wait_for_server("127.0.0.1", 1, timeout_seconds=0.3) is False


def test_desktop_main_missing_webview_returns_exit_code(monkeypatch, capsys):
    import builtins

    from app import desktop

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "webview":
            raise ImportError("forced")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    rc = desktop.launch(host="127.0.0.1", port=1)
    assert rc == 2
    err = capsys.readouterr().err
    assert "pywebview" in err
