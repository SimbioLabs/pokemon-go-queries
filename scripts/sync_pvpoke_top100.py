#!/usr/bin/env python3
"""Fetch PvPoke overall top 100 for Great (1500) and Ultra (2500) leagues.

Also computes true rank-1 IVs (best stat product under the CP cap) from
PvPoke gamemaster baseStats + official CP multipliers.
"""

from __future__ import annotations

import json
import math
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

# CPMs indexed as (level - 1) * 2 — from PvPoke Battle.js
CPMS = [
    0.0939999967813491, 0.135137430784308, 0.166397869586944, 0.192650914456886,
    0.215732470154762, 0.236572655026622, 0.255720049142837, 0.273530381100769,
    0.290249884128570, 0.306057381335773, 0.321087598800659, 0.335445032295077,
    0.349212676286697, 0.362457748778790, 0.375235587358474, 0.387592411085168,
    0.399567276239395, 0.411193549517250, 0.422500014305114, 0.432926413410414,
    0.443107545375824, 0.453059953871985, 0.462798386812210, 0.472336077786704,
    0.481684952974319, 0.490855810259008, 0.499858438968658, 0.508701756943992,
    0.517393946647644, 0.525942508771329, 0.534354329109191, 0.542635762230353,
    0.550792694091796, 0.558830599438087, 0.566754519939422, 0.574569148039264,
    0.582278907299041, 0.589887911977272, 0.597400009632110, 0.604823657502073,
    0.612157285213470, 0.619404110566050, 0.626567125320434, 0.633649181622743,
    0.640652954578399, 0.647580963301656, 0.654435634613037, 0.661219263506722,
    0.667934000492096, 0.674581899290818, 0.681164920330047, 0.687684905887771,
    0.694143652915954, 0.700542893277978, 0.706884205341339, 0.713169102333341,
    0.719399094581604, 0.725575616972598, 0.731700003147125, 0.734741011137376,
    0.737769484519958, 0.740785574597326, 0.743789434432983, 0.746781208702482,
    0.749761044979095, 0.752729105305821, 0.755685508251190, 0.758630366519684,
    0.761563837528228, 0.764486065255226, 0.767397165298461, 0.770297273971590,
    0.773186504840850, 0.776064945942412, 0.778932750225067, 0.781790064808426,
    0.784636974334716, 0.787473583646825, 0.790300011634826, 0.792803950958807,
    0.795300006866455, 0.797803921486970, 0.800300002098083, 0.802803892322847,
    0.805299997329711, 0.807803863460723, 0.810299992561340, 0.812803834895026,
    0.815299987792968, 0.817803806620319, 0.820299983024597, 0.822803778631297,
    0.825299978256225, 0.827803750922782, 0.830299973487854, 0.832803753381377,
    0.835300028324127, 0.837803755931569, 0.840300023555755, 0.842803729034748,
    0.845300018787384, 0.847803702398935, 0.850300014019012, 0.852803676019539,
    0.855300009250640, 0.857803649892077, 0.860300004482269, 0.862803624012168,
    0.865299999713897,
]

SOURCES = {
    "gl": {
        "cp": 1500,
        "label": "Great League",
        "urls": [
            "https://pvpoke.com/data/rankings/all/overall/rankings-1500.json",
            "https://raw.githubusercontent.com/pvpoke/pvpoke/master/src/data/rankings/all/overall/rankings-1500.json",
        ],
        "rankings_page": "https://pvpoke.com/rankings/all/1500/overall/",
        "iv_key": "cp1500",
    },
    "ul": {
        "cp": 2500,
        "label": "Ultra League",
        "urls": [
            "https://pvpoke.com/data/rankings/all/overall/rankings-2500.json",
            "https://raw.githubusercontent.com/pvpoke/pvpoke/master/src/data/rankings/all/overall/rankings-2500.json",
        ],
        "rankings_page": "https://pvpoke.com/rankings/all/2500/overall/",
        "iv_key": "cp2500",
    },
}

GAMEMASTER_URLS = [
    "https://pvpoke.com/data/gamemaster.min.json",
    "https://raw.githubusercontent.com/pvpoke/pvpoke/master/src/data/gamemaster.min.json",
]

UA = "SimbioLabs-pokemon-go-queries/1.1 (+https://github.com/SimbioLabs/pokemon-go-queries)"
LEVEL_CAP = 50.0


def fetch_json(urls: list[str]):
    last_err: Exception | None = None
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=90) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001
            last_err = e
    raise RuntimeError(f"Failed to fetch: {last_err}")


def cpm_for(level: float) -> float:
    return CPMS[int(round((level - 1) * 2))]


def calc_cp(ba: int, bd: int, bh: int, atk: int, df: int, sta: int, level: float) -> int:
    c = cpm_for(level)
    return max(
        10,
        math.floor(((ba + atk) * ((bd + df) ** 0.5) * ((bh + sta) ** 0.5) * (c**2)) / 10),
    )


def rank1_iv(base: dict, league_cp: int, level_cap: float = LEVEL_CAP) -> dict | None:
    """Best stat-product IV under league CP (true R1), level cap 50."""
    ba, bd, bh = int(base["atk"]), int(base["def"]), int(base["hp"])
    levels = [1 + i * 0.5 for i in range(int((level_cap - 1) * 2) + 1)]
    best = None
    for atk in range(16):
        for df in range(16):
            for sta in range(16):
                level = None
                for lv in reversed(levels):
                    if calc_cp(ba, bd, bh, atk, df, sta, lv) <= league_cp:
                        level = lv
                        break
                if level is None:
                    continue
                c = cpm_for(level)
                attack = c * (ba + atk)
                defense = c * (bd + df)
                hp = max(math.floor(c * (bh + sta)), 10)
                product = attack * defense * hp
                key = (product, hp, defense, -attack)
                cand = {
                    "key": key,
                    "level": level,
                    "atk": atk,
                    "def": df,
                    "sta": sta,
                    "cp": calc_cp(ba, bd, bh, atk, df, sta, level),
                    "product": product,
                }
                if best is None or cand["key"] > best["key"]:
                    best = cand
    if not best:
        return None
    return {
        "iv": f"{best['atk']}/{best['def']}/{best['sta']}",
        "level": best["level"],
        "cp": best["cp"],
        "product": round(best["product"], 1),
    }


def format_move_id(move_id: str) -> str:
    return str(move_id).replace("_", " ").title()


def moves_label(entry: dict) -> str:
    ms = entry.get("moveset") or []
    parts = [format_move_id(m) for m in ms if isinstance(m, str)]
    if parts:
        return " / ".join(parts)
    moves = entry.get("moves") or {}
    out: list[str] = []
    fast = moves.get("fastMoves") or []
    charged = moves.get("chargedMoves") or []
    if fast and isinstance(fast[0], dict) and fast[0].get("moveId"):
        out.append(format_move_id(fast[0]["moveId"]))
    for c in charged[:2]:
        if isinstance(c, dict) and c.get("moveId"):
            out.append(format_move_id(c["moveId"]))
    return " / ".join(out) if out else "—"


def resolve_species(gm_by_id: dict, species_id: str) -> dict | None:
    if species_id in gm_by_id:
        return gm_by_id[species_id]
    # rankings sometimes use forms not in min set; try stripping suffixes
    for suffix in ("_shadow", "_busted", "_disguised"):
        if species_id.endswith(suffix):
            base = species_id[: -len(suffix)]
            # shadow keeps own entry usually; busted may map to mimikyu
            if species_id in gm_by_id:
                return gm_by_id[species_id]
            if base in gm_by_id:
                return gm_by_id[base]
    return None


def top100(entries: list[dict], gm_by_id: dict, league_cp: int) -> list[dict]:
    out = []
    for i, e in enumerate(entries[:100], start=1):
        sid = e.get("speciesId")
        species = resolve_species(gm_by_id, sid) if sid else None
        r1 = rank1_iv(species["baseStats"], league_cp) if species and species.get("baseStats") else None
        out.append(
            {
                "rank": i,
                "speciesId": sid,
                "speciesName": e.get("speciesName") or sid,
                "score": e.get("score"),
                "moves": moves_label(e),
                "r1Iv": r1["iv"] if r1 else None,
                "r1Level": r1["level"] if r1 else None,
                "r1Cp": r1["cp"] if r1 else None,
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
        "Scores/moves from PvPoke rankings. **R1 IV** = best stat-product IV under the league CP cap (level 50), computed from PvPoke gamemaster base stats — not the site's defaultIVs.",
        "",
        "| # | Pokémon | Score | R1 IV | Lvl | Moves (PvPoke) |",
        "|--:|---------|------:|------:|----:|----------------|",
    ]
    for r in rows:
        score = r["score"]
        score_s = f"{score:g}" if isinstance(score, (int, float)) else "—"
        name = str(r["speciesName"]).replace("|", "/")
        moves = str(r["moves"]).replace("|", "/")
        iv = r.get("r1Iv") or "—"
        lvl = r.get("r1Level")
        lvl_s = f"{lvl:g}" if isinstance(lvl, (int, float)) else "—"
        lines.append(f"| {r['rank']} | {name} | {score_s} | {iv} | {lvl_s} | {moves} |")
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
        "r1Note": "Stat-product rank-1 IV at level cap 50 under league CP; from gamemaster baseStats.",
        "rankings": [{k: v for k, v in r.items() if k != "key"} for r in rows],
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def main() -> None:
    fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    gm = fetch_json(GAMEMASTER_URLS)
    gm_by_id = {p["speciesId"]: p for p in gm.get("pokemon", [])}
    print(f"gamemaster species: {len(gm_by_id)}")

    for key, meta in SOURCES.items():
        entries = fetch_json(meta["urls"])
        rows = top100(entries, gm_by_id, meta["cp"])
        missing = sum(1 for r in rows if not r.get("r1Iv"))
        md = write_markdown(key, meta, rows, fetched_at)
        js = write_json(key, meta, rows, fetched_at)
        print(f"{key}: wrote {md.name} / {js.name} ({len(rows)} rows, {missing} missing R1)")


if __name__ == "__main__":
    main()
