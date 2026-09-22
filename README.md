# pokemon-go-queries

Search queries for Pokémon GO inventory (copy-paste), plus auto-synced PvPoke top 100 lists.

**Site:** https://simbiolabs.github.io/pokemon-go-queries/

## Files

- `index.html` — copy buttons for house search queries
- `top100-gl.md` / `top100-ul.md` — Great / Ultra League overall top 100
- `data/top100-*.json` — same rankings as JSON

## Auto sync

GitHub Action [Sync PvPoke top 100](.github/workflows/sync-pvpoke-top100.yml) runs **Mondays 12:00 UTC** (and on manual dispatch). It fetches PvPoke overall rankings and commits when the lists change.

Source: [PvPoke](https://pvpoke.com/) rankings JSON.
