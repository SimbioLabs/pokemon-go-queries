#!/usr/bin/env python3
"""Fetch PvPoke overall top 100 for Great (1500) and Ultra (2500) leagues."""

from __future__ import annotations

import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

# Prefer site JSON; fall back to GitHub mirror of pvpoke/pvpoke.
SOURCES = {
    "gl": {
        "cp": 1500,
        "label": "Great League",
        "slug": "1500",
        "urls": [
            "https://pvpoke.com/data/rankings/all/overall/rankings-1500.json",
            "https://raw.githubusercontent.com/pvpoke/pvpoke/master/src/data/rankings/all/overall/rankings-1500.json",
        ],
        "rankings_page": "https://pvpoke.com/rankings/all/1500/overall/",
    },
    "ul": {
        "cp": 2500,
        "label": "Ultra League",
        "slug": "2500",
        "urls": [
            "https://pvpoke.com/data/rankings/all/overall/rankings-2500.json",
            "https://raw.githubusercontent.com/pvpoke/pvpoke/master/src/data/rankings/all/overall/rankings-2500.json",
        ],
        "rankings_page": "https://pvpoke.com/rankings/all/2500/overall/",
    },
}

UA = "SimbioLabs-pokemon-go-queries/1.0 (+https://github.com/SimbioLabs/pokemon-go-queries)"


def fetch_json(urls: list[str]) -> list[dict]:
    last_err: Exception | None = None
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001 — try next mirror
            last_err = e
    raise RuntimeError(f"Failed to fetch rankings: {last_err}")


def format_move_id(move_id: str) -> str:
    return str(move_id).replace("_", " ").title()


def move_id_from(item) -> str | None:
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        return item.get("moveId") or item.get("moveid") or item.get("MoveId")
    return None


def moves_label(entry: dict) -> str:
    # Preferred: explicit recommended moveset ids
    ms = entry.get("moveset") or []
    parts = [format_move_id(m) for m in ms if isinstance(m, str)]
    if parts:
        return " / ".join(parts)

    moves = entry.get("moves") or {}
    fast = moves.get("fastMoves") or []
    charged = moves.get("chargedMoves") or []
    out: list[str] = []
    if fast:
        mid = move_id_from(fast[0])
        if mid:
            out.append(format_move_id(mid))
    for c in charged[:2]:
        mid = move_id_from(c)
        if mid:
            out.append(format_move_id(mid))
    return " / ".join(out) if out else "—"


def top100(entries: list[dict]) -> list[dict]:
    out = []
    for i, e in enumerate(entries[:100], start=1):
        out.append(
            {
                "rank": i,
                "speciesId": e.get("speciesId"),
                "speciesName": e.get("speciesName") or e.get("speciesId"),
                "score": e.get("score"),
                "moves": moves_label(e),
            }
        )
    return out


def write_markdown(league_key: str, meta: dict, rows: list[dict], fetched_at: str) -> Path:
    path = ROOT / f"top100-{league_key}.md"
    lines = [
        f"# {meta['label']} top 100",
        "",
        f"PvPoke Open **{meta['label']}** overall top 100.",
        "",
        f"Source: [PvPoke]({meta['rankings_page']})",
        "",
        f"Auto-synced **{fetched_at}** (UTC) via GitHub Action.",
        "",
        "Scores and moves from PvPoke overall rankings (best movesets).",
        "",
        "| # | Pokémon | Score | Moves (PvPoke) |",
        "|--:|---------|------:|----------------|",
    ]
    for r in rows:
        score = r["score"]
        score_s = f"{score:g}" if isinstance(score, (int, float)) else "—"
        name = str(r["speciesName"]).replace("|", "/")
        moves = str(r["moves"]).replace("|", "/")
        lines.append(f"| {r['rank']} | {name} | {score_s} | {moves} |")
    lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_json(league_key: str, meta: dict, rows: list[dict], fetched_at: str) -> Path:
    DATA.mkdir(parents=True, exist_ok=True)
    path = DATA / f"top100-{league_key}.json"
    payload = {
        "league": meta["label"],
        "cp": meta["cp"],
        "source": meta["rankings_page"],
        "fetchedAt": fetched_at,
        "count": len(rows),
        "rankings": rows,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def main() -> None:
    fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    changed: list[str] = []
    for key, meta in SOURCES.items():
        entries = fetch_json(meta["urls"])
        rows = top100(entries)
        md = write_markdown(key, meta, rows, fetched_at)
        js = write_json(key, meta, rows, fetched_at)
        print(f"{key}: wrote {md.name} and {js.name} ({len(rows)} rows)")
        changed.extend([str(md.relative_to(ROOT)), str(js.relative_to(ROOT))])
    print("files:", " ".join(changed))


if __name__ == "__main__":
    main()
