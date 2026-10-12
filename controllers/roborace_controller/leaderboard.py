"""Crash-tolerant local JSON storage for official RoboRace results."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import tempfile


CONFIG_ID = "junior-track-v2-level-1"


def clean_nickname(value: object, fallback: str = "Hrac-001") -> str:
    if not isinstance(value, str):
        return fallback
    value = "".join(ch for ch in value.strip() if ch.isprintable() and ord(ch) >= 32)
    value = re.sub(r"\s+", " ", value)[:20]
    return value or fallback


class Leaderboard:
    def __init__(self, path: str | Path, config_id: str = CONFIG_ID):
        self.path = Path(path)
        self.backup = self.path.with_suffix(self.path.suffix + ".bak")
        self.config_id = config_id
        self.warning: str | None = None
        self.data = self._load()

    def _empty(self) -> dict:
        return {"schema_version": 1, "competition_config_id": self.config_id, "entries": []}

    def _load(self) -> dict:
        if not self.path.exists():
            return self._empty()
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or not isinstance(data.get("entries"), list):
                raise ValueError("neplatná struktura")
            if data.get("competition_config_id") != self.config_id:
                self.warning = "Žebříček patří k jiné konfiguraci tratě; načetl se prázdný žebříček."
                return self._empty()
            return data
        except (OSError, ValueError, json.JSONDecodeError):
            self.warning = "Soubor žebříčku je poškozený; původní soubor zůstal zachován."
            try:
                backup_data = json.loads(self.backup.read_text(encoding="utf-8"))
                if (isinstance(backup_data, dict)
                        and isinstance(backup_data.get("entries"), list)
                        and backup_data.get("competition_config_id") == self.config_id):
                    return backup_data
            except (OSError, ValueError, json.JSONDecodeError):
                pass
            return self._empty()

    def add_result(self, nickname: str, raw_time: float, penalties: int,
                   penalty_seconds: float, source: str) -> dict:
        nickname = clean_nickname(nickname)
        entry = {
            "nickname": nickname,
            "utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "raw_time": round(raw_time, 6),
            "penalties": int(penalties),
            "penalty_seconds": round(penalty_seconds, 2),
            "final_time": round(raw_time + penalty_seconds, 6),
            "source": source,
            "competition_config_id": self.config_id,
        }
        same = next((row for row in self.data["entries"] if row.get("nickname", "").casefold() == nickname.casefold()), None)
        if same is None:
            entry["official_runs"] = [dict(entry)]
            self.data["entries"].append(entry)
        else:
            runs = same.setdefault("official_runs", [dict(same)])
            runs.append(dict(entry))
            if _sort_key(entry) < _sort_key(same):
                history = runs
                same.update(entry)
                same["official_runs"] = history
        self._save()
        return entry

    def top(self, limit: int = 10) -> list[dict]:
        rows = [r for r in self.data["entries"] if r.get("competition_config_id") == self.config_id]
        return sorted(rows, key=_sort_key)[:limit]

    def reset(self) -> None:
        self.data = self._empty()
        self._save()

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            try:
                old = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(old, dict) and isinstance(old.get("entries"), list):
                    fd, backup_temp = tempfile.mkstemp(prefix="leaderboard-backup-", suffix=".tmp", dir=self.path.parent)
                    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as backup_file:
                        json.dump(old, backup_file, ensure_ascii=False, indent=2)
                        backup_file.write("\n")
                        backup_file.flush()
                        os.fsync(backup_file.fileno())
                    os.replace(backup_temp, self.backup)
            except OSError:
                pass
            except (ValueError, json.JSONDecodeError):
                pass
        fd, temp_name = tempfile.mkstemp(prefix="leaderboard-", suffix=".tmp", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as target:
                json.dump(self.data, target, ensure_ascii=False, indent=2)
                target.write("\n")
                target.flush()
                os.fsync(target.fileno())
            os.replace(temp_name, self.path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)


def _sort_key(row: dict) -> tuple:
    return (float(row["final_time"]), float(row["raw_time"]), str(row["utc"]))
