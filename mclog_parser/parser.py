import re
import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from typing import Optional


# ─── Regex Patterns ───────────────────────────────────────────────
_LINE_RE = re.compile(
    r"^\[(?P<time>\d{2}:\d{2}:\d{2})\] \[(?P<thread>[^\]]+)/(?P<level>[A-Z]+)\]: (?P<msg>.+)$"
)
_JOIN_RE     = re.compile(r"^(?P<player>\w+) joined the game$")
_LEAVE_RE    = re.compile(r"^(?P<player>\w+) left the game$")
_DEATH_RE    = re.compile(r"^(?P<player>\w+) (?:was|died|fell|drowned|burned|blew|hit|tried|walked|withered|starved|suffocated|kinetic).+$")
_CHAT_RE     = re.compile(r"^<(?P<player>\w+)> (?P<message>.+)$")
_LAG_RE      = re.compile(r"Can't keep up!")
_CRASH_RE    = re.compile(r"(?:java\.\w+Exception|java\.\w+Error|RuntimeException|Caused by:|FATAL)")


class LogParser:
    """
    Parse Minecraft server log files and extract structured data.

    Usage:
        log = LogParser("latest.log")
        print(log.summary())
        log.export_json("report.json")
    """

    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        if not self.filepath.exists():
            raise FileNotFoundError(f"Log file not found: {filepath}")

        self._lines: list[dict] = []
        self._parse()

    # ─── Internal ──────────────────────────────────────────────────

    def _parse(self):
        with open(self.filepath, "r", encoding="utf-8", errors="replace") as f:
            for raw in f:
                raw = raw.rstrip("\n")
                m = _LINE_RE.match(raw)
                if m:
                    self._lines.append({
                        "time":   m.group("time"),
                        "thread": m.group("thread"),
                        "level":  m.group("level"),
                        "msg":    m.group("msg"),
                        "raw":    raw,
                    })
                else:
                    # continuation lines (stack traces etc.)
                    if self._lines:
                        self._lines[-1].setdefault("extra", []).append(raw)

    # ─── Public API ────────────────────────────────────────────────

    def crashes(self) -> list[dict]:
        """Return all crash/error events with context."""
        results = []
        for i, line in enumerate(self._lines):
            if _CRASH_RE.search(line["msg"]):
                results.append({
                    "time":    line["time"],
                    "level":   line["level"],
                    "message": line["msg"],
                    "trace":   line.get("extra", []),
                })
        return results

    def lag_spikes(self) -> list[dict]:
        """Return all lag spike warnings."""
        return [
            {"time": l["time"], "message": l["msg"]}
            for l in self._lines if _LAG_RE.search(l["msg"])
        ]

    def player_sessions(self, player: Optional[str] = None) -> dict:
        """
        Return join/leave sessions per player.
        If player is given, filter to that player only.
        """
        sessions: dict[str, list] = defaultdict(list)
        last_join: dict[str, str] = {}

        for line in self._lines:
            jm = _JOIN_RE.match(line["msg"])
            lm = _LEAVE_RE.match(line["msg"])

            if jm:
                p = jm.group("player")
                last_join[p] = line["time"]

            elif lm:
                p = lm.group("player")
                sessions[p].append({
                    "joined": last_join.pop(p, None),
                    "left":   line["time"],
                })

        # players still online (no leave event)
        for p, t in last_join.items():
            sessions[p].append({"joined": t, "left": None})

        if player:
            return {player: sessions.get(player, [])}
        return dict(sessions)

    def player_stats(self) -> list[dict]:
        """Return per-player statistics sorted by session count."""
        sessions = self.player_sessions()
        deaths = defaultdict(int)
        messages = defaultdict(int)

        for line in self._lines:
            dm = _DEATH_RE.match(line["msg"])
            cm = _CHAT_RE.match(line["msg"])
            if dm:
                deaths[dm.group("player")] += 1
            if cm:
                messages[cm.group("player")] += 1

        stats = []
        all_players = set(sessions) | set(deaths) | set(messages)
        for p in all_players:
            s = sessions.get(p, [])
            stats.append({
                "player":       p,
                "sessions":     len(s),
                "deaths":       deaths[p],
                "chat_messages": messages[p],
            })

        return sorted(stats, key=lambda x: x["sessions"], reverse=True)

    def top_players(self, n: int = 10) -> list[dict]:
        """Return top N players by sessions."""
        return self.player_stats()[:n]

    def summary(self) -> dict:
        """Return a full summary of the log file."""
        stats   = self.player_stats()
        crashes = self.crashes()
        lags    = self.lag_spikes()

        unique_players = len(stats)
        total_sessions = sum(p["sessions"] for p in stats)

        return {
            "file":            str(self.filepath),
            "total_lines":     len(self._lines),
            "unique_players":  unique_players,
            "total_sessions":  total_sessions,
            "crash_count":     len(crashes),
            "lag_spike_count": len(lags),
            "top_players":     self.top_players(5),
            "crashes":         crashes[:5],  # first 5 only in summary
        }

    def export_json(self, output_path: str = "mc_report.json") -> str:
        """Export full analysis to a JSON file."""
        report = {
            "summary":        self.summary(),
            "player_stats":   self.player_stats(),
            "all_crashes":    self.crashes(),
            "all_lag_spikes": self.lag_spikes(),
            "player_sessions": self.player_sessions(),
        }
        path = Path(output_path)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        return str(path)
