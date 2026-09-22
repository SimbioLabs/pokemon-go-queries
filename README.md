# pokemon-go-queries

Search queries for Pokémon GO inventory (copy-paste), plus auto-synced PvPoke top 100 lists.

**Site:** https://simbiolabs.github.io/pokemon-go-queries/

## Files

- `index.html` — copy buttons for house search queries (bulk keep auto-rebuilt from top 100)
- `top100-gl.md` / `top100-ul.md` — Great / Ultra League overall top 100 (score, **R1 IV**, level, moves)
- `data/top100-*.json` — same rankings as JSON (`r1Iv`, `r1Level`, `r1Cp`)
- `data/bulk-keep.json` — GL∪UL family tokens used in the bulk keep query

## Auto sync

GitHub Action [Sync PvPoke top 100](.github/workflows/sync-pvpoke-top100.yml) runs **Mondays 12:00 UTC** (and on manual dispatch). It fetches PvPoke overall rankings + gamemaster, computes true rank-1 IVs (best stat product under the league CP cap at level 50), rebuilds the GL+UL useful bulk query in `index.html`, and commits when outputs change.

**R1 IV** is calculated from base stats — not PvPoke’s `defaultIVs` heuristic.

Bulk keep = house IVs `0-1attack&2-4defense&2-4hp` plus family search tokens from the GL∪UL top 100 (`+species` for evo lines; never `+eevee`).

Source: [PvPoke](https://pvpoke.com/) rankings + gamemaster.
