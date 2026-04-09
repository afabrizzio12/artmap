# artmap-data

Data pipeline for [ArtMap](https://github.com/your-org/artmap) — a global cultural atlas.

Ingests artwork metadata from public museum APIs, normalises it to a unified schema, and stores outputs in this repository for consumption by the ArtMap app.

---

## Sources

| Source | API | License | Status |
|---|---|---|---|
| Metropolitan Museum of Art | [metmuseum.github.io](https://metmuseum.github.io) | CC0 | ✅ Active |
| Rijksmuseum | [data.rijksmuseum.nl](https://data.rijksmuseum.nl/object-metadata/api/) | CC0 | 🔜 Planned |
| Art Institute of Chicago | [api.artic.edu](https://api.artic.edu/docs/) | CC0 | 🔜 Planned |
| Harvard Art Museums | [github.com/harvardartmuseums](https://github.com/harvardartmuseums/api-docs) | CC BY | 🔜 Planned |

---

## Repo structure

```
artmap-data/
  schema/
    artwork.schema.json     # Unified ArtMap artwork schema
  scripts/
    ingest_met.py           # Met Museum ingestion script
    requirements.txt
  sources/
    met/                    # Reserved for source-specific config / mapping notes
  output/
    met/
      objects/              # Raw API responses (one JSON per object ID)
      artworks.json         # Normalised artworks array
      artworks.ndjson       # Normalised artworks, newline-delimited
  .github/
    workflows/
      ingest_met.yml        # Weekly scheduled ingestion
```

---

## Unified schema

See [`schema/artwork.schema.json`](schema/artwork.schema.json) for the full JSON Schema definition.

Key fields:

| Field | Description |
|---|---|
| `id` | Global ID: `{source}:{source_id}` (e.g. `met:436535`) |
| `title` | Artwork title |
| `artist.display_name` | Artist name as shown to users |
| `date.display` | Human-readable date string |
| `date.year_start / year_end` | Parsed integers for filtering |
| `classification.period` | Era/period (e.g. Renaissance, Baroque) |
| `classification.medium` | e.g. Oil on canvas |
| `institution` | Institution name, city, country, lat/lng |
| `geo_origin` | Geographic origin of the artwork itself |
| `images.primary` | Full-res image URL |
| `images.primary_small` | Thumbnail URL |
| `is_public_domain` | Always true in output (filter applied at ingestion) |
| `license` | e.g. CC0 |

---

## Running locally

```bash
# Install deps
pip install -r scripts/requirements.txt

# Dev run: 200 objects from Paintings department (dept 11)
python scripts/ingest_met.py --limit 200 --department 11

# Full run (slow — ~470k objects, ~90% will be skipped as non-public-domain)
python scripts/ingest_met.py --resume

# Resume after interruption
python scripts/ingest_met.py --resume
```

Output lands in `output/met/`.

---

## Automated ingestion

GitHub Actions runs [`ingest_met.yml`](.github/workflows/ingest_met.yml) every Sunday at 02:00 UTC. It uses `--resume` so only new or changed objects are re-fetched. Results are committed back to the repo automatically.

You can also trigger a manual run from the Actions tab, optionally with `--limit` or `--department` filters.

---

## Adding a new source

1. Create `scripts/ingest_{source}.py` following the same pattern as `ingest_met.py`
2. Add a `normalise()` function that maps source fields → `artwork.schema.json`
3. Add a workflow in `.github/workflows/`
4. Document the source in this README
