"""
pipeline_status.py — パイプライン進捗ステータス書き込みモジュール

各パイプラインが `~/.pipeline_status/{name}.json` に進捗を書き込む。
pipeline_monitor.command がこのファイルを読んで表示する。
"""

import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

STATUS_DIR = Path.home() / ".pipeline_status"
JST = timezone(timedelta(hours=9))


def _now_iso() -> str:
    return datetime.now(JST).isoformat(timespec="seconds")


class PipelineStatus:
    def __init__(self, name: str):
        self.name = name
        STATUS_DIR.mkdir(exist_ok=True)
        self._path = STATUS_DIR / f"{name}.json"

    def _write(self, data: dict):
        data["updated_at"] = _now_iso()
        self._path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def start(self, total_steps: int, description: str = ""):
        """パイプライン開始"""
        prev = self._read()
        self._write({
            "name": self.name,
            "status": "running",
            "step": 0,
            "total_steps": total_steps,
            "step_label": "起動中",
            "description": description,
            "started_at": _now_iso(),
            "last_result": prev.get("last_result", "unknown"),
            "last_run_at": prev.get("last_run_at"),
        })

    def update(self, step: int, label: str):
        """ステップ進捗更新"""
        prev = self._read()
        self._write({
            "name": self.name,
            "status": "running",
            "step": step,
            "total_steps": prev.get("total_steps", 3),
            "step_label": label,
            "description": prev.get("description", ""),
            "started_at": prev.get("started_at", _now_iso()),
            "last_result": prev.get("last_result", "unknown"),
            "last_run_at": prev.get("last_run_at"),
        })

    def done(self, success: bool = True, message: str = ""):
        """パイプライン完了"""
        prev = self._read()
        self._write({
            "name": self.name,
            "status": "idle",
            "step": prev.get("total_steps", 0),
            "total_steps": prev.get("total_steps", 0),
            "step_label": "完了" if success else "失敗",
            "description": prev.get("description", ""),
            "started_at": prev.get("started_at"),
            "last_result": "success" if success else "failed",
            "last_run_at": _now_iso(),
            "last_message": message,
        })

    def _read(self) -> dict:
        if self._path.exists():
            try:
                return json.loads(self._path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}
