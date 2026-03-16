#!/usr/bin/env python3
import argparse
import json
import sys
from mclog_parser import LogParser


def main():
    parser = argparse.ArgumentParser(
        prog="mclog",
        description="🎮 Minecraft Log Parser — Analyze your server logs instantly"
    )
    parser.add_argument("logfile", help="Path to latest.log or any MC log file")
    parser.add_argument("--crashes",  action="store_true", help="Show crashes and errors")
    parser.add_argument("--lags",     action="store_true", help="Show lag spikes")
    parser.add_argument("--players",  action="store_true", help="Show player stats")
    parser.add_argument("--player",   metavar="NAME",      help="Sessions for a specific player")
    parser.add_argument("--export",   metavar="FILE",      help="Export full report to JSON")
    parser.add_argument("--summary",  action="store_true", help="Show summary (default)", default=True)

    args = parser.parse_args()

    try:
        log = LogParser(args.logfile)
    except FileNotFoundError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)

    if args.crashes:
        crashes = log.crashes()
        print(f"\n💥 Crashes & Errors ({len(crashes)} total)\n" + "─" * 40)
        for c in crashes:
            print(f"[{c['time']}] {c['level']}: {c['message']}")
            for t in c["trace"][:3]:
                print(f"  {t}")
        return

    if args.lags:
        lags = log.lag_spikes()
        print(f"\n⚠️  Lag Spikes ({len(lags)} total)\n" + "─" * 40)
        for l in lags:
            print(f"[{l['time']}] {l['message']}")
        return

    if args.players:
        stats = log.player_stats()
        print(f"\n👥 Player Stats ({len(stats)} players)\n" + "─" * 40)
        print(f"{'Player':<20} {'Sessions':>8} {'Deaths':>7} {'Chat':>6}")
        print("─" * 44)
        for p in stats:
            print(f"{p['player']:<20} {p['sessions']:>8} {p['deaths']:>7} {p['chat_messages']:>6}")
        return

    if args.player:
        sessions = log.player_sessions(args.player)
        data = sessions.get(args.player, [])
        print(f"\n🎮 Sessions for {args.player} ({len(data)} total)\n" + "─" * 40)
        for s in data:
            left = s["left"] or "still online"
            print(f"  Joined: {s['joined']}  →  Left: {left}")
        return

    if args.export:
        path = log.export_json(args.export)
        print(f"✅ Report exported to: {path}")
        return

    # Default: summary
    s = log.summary()
    print(f"""
🎮 Minecraft Log Summary
{"─" * 40}
📁 File          : {s['file']}
📄 Total Lines   : {s['total_lines']:,}
👥 Players       : {s['unique_players']}
🔗 Sessions      : {s['total_sessions']}
💥 Crashes       : {s['crash_count']}
⚠️  Lag Spikes   : {s['lag_spike_count']}

🏆 Top Players:
""")
    for p in s["top_players"]:
        print(f"  {p['player']:<20} {p['sessions']} sessions  |  {p['deaths']} deaths")

    if s["crashes"]:
        print(f"\n💥 Latest Crash:")
        c = s["crashes"][-1]
        print(f"  [{c['time']}] {c['message']}")


if __name__ == "__main__":
    main()
