# mclog-parser 🎮

**Analyze Minecraft server logs instantly — turn raw log files into structured data.**

```bash
pip install mclog-parser
```

---

## Why?

Every Minecraft server generates thousands of log lines. Finding crashes, tracking players, or spotting lag spikes means scrolling through walls of text manually.

`mclog-parser` does it in one line.

---

## Quickstart

```python
from mclog_parser import LogParser

log = LogParser("latest.log")

log.summary()        # full overview
log.crashes()        # all errors & crashes
log.lag_spikes()     # lag warnings
log.player_stats()   # per-player stats
log.export_json()    # save report as JSON
```

### Example Output

```json
{
  "unique_players": 3,
  "total_sessions": 5,
  "crash_count": 1,
  "lag_spike_count": 2,
  "top_players": [
    { "player": "Ahmed99", "sessions": 2, "deaths": 1 }
  ]
}
```

---

## CLI

No Python needed — run directly from your terminal:

```bash
mclog latest.log                        # summary
mclog latest.log --crashes              # errors only
mclog latest.log --players              # player stats table
mclog latest.log --player Ahmed99       # one player's sessions
mclog latest.log --export report.json   # export to JSON
```

---

## Supported Servers

| Server | Status |
|--------|--------|
| Paper  | ✅ |
| Spigot | ✅ |
| Vanilla | ✅ |
| Fabric | ✅ |
| Forge  | 🔜 |

---

## Install

```bash
pip install mclog-parser
```

Requires Python 3.10+

---

## Roadmap

- [x] Core parser (crashes, lag, sessions)
- [x] Player stats
- [x] JSON export
- [x] CLI
- [ ] Web dashboard
- [ ] Discord bot integration
- [ ] Real-time log watching

---

## License

MIT — free to use, modify, and distribute.
