#!/usr/bin/env python3
"""
ArtMap — Wikidata enrichment script
Takes normalised artworks (output of ingest_met.py) and enriches them
with precise location data from Wikidata.

Strategy:
  1. For artworks with a wikidata_url → direct SPARQL lookup (accurate)
  2. For artworks without → geocode the Met's `culture` field as fallback

Usage:
    python enrich_wikidata.py                        # enrich all Met artworks
    python enrich_wikidata.py --limit 200            # dev/test
    python enrich_wikidata.py --input path/to/artworks.ndjson

Output:
    output/met/artworks_enriched.ndjson
    output/met/enrichment_stats.json
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
# Wikidata asks for a descriptive User-Agent
USER_AGENT = "ArtMap/0.1 (github.com/your-org/artmap-data; artmap@example.com)"

# Wikidata rate: be polite, ~1 req/s for individual lookups
SPARQL_DELAY = 1.1

OUTPUT_DIR = Path(__file__).parent.parent / "output" / "met"


# ---------------------------------------------------------------------------
# Wikidata SPARQL helpers
# ---------------------------------------------------------------------------

session = requests.Session()
session.headers.update({
    "User-Agent": USER_AGENT,
    "Accept": "application/sparql-results+json",
})


def sparql_query(query: str) -> list[dict]:
    """Execute a SPARQL query and return bindings."""
    resp = session.get(
        SPARQL_ENDPOINT,
        params={"query": query, "format": "json"},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("results", {}).get("bindings", [])


def val(binding: dict, key: str) -> str | None:
    """Safely extract a value from a SPARQL binding."""
    return binding.get(key, {}).get("value") or None


# ---------------------------------------------------------------------------
# Individual artwork lookup (via objectWikidata_URL)
# ---------------------------------------------------------------------------

ARTWORK_QUERY = """
SELECT ?item
       ?locationLabel ?locationCoordLat ?locationCoordLng
       ?collectionLabel
       ?creatorLabel ?creatorBirthPlaceLabel ?creatorBirthPlaceLat ?creatorBirthPlaceLng
       ?genre ?genreLabel
       ?movement ?movementLabel
       ?inception
WHERE {{
  BIND(<{wikidata_uri}> AS ?item)

  # Current location (P276) with coordinates (P625)
  OPTIONAL {{
    ?item wdt:P276 ?location .
    ?location wdt:P625 ?locationCoord .
    BIND(xsd:decimal(REPLACE(STR(?locationCoord), "Point\\\\(([^ ]+) ([^ ]+)\\\\)", "$2")) AS ?locationCoordLat)
    BIND(xsd:decimal(REPLACE(STR(?locationCoord), "Point\\\\(([^ ]+) ([^ ]+)\\\\)", "$1")) AS ?locationCoordLng)
  }}

  # Collection (P195) — sometimes more specific than location
  OPTIONAL {{ ?item wdt:P195 ?collection }}

  # Creator (P170) + their birthplace (P19) with coordinates
  OPTIONAL {{
    ?item wdt:P170 ?creator .
    OPTIONAL {{
      ?creator wdt:P19 ?creatorBirthPlace .
      OPTIONAL {{ ?creatorBirthPlace wdt:P625 ?creatorBirthPlaceCoord }}
      BIND(xsd:decimal(REPLACE(STR(?creatorBirthPlaceCoord), "Point\\\\(([^ ]+) ([^ ]+)\\\\)", "$2")) AS ?creatorBirthPlaceLat)
      BIND(xsd:decimal(REPLACE(STR(?creatorBirthPlaceCoord), "Point\\\\(([^ ]+) ([^ ]+)\\\\)", "$1")) AS ?creatorBirthPlaceLng)
    }}
  }}

  # Genre (P136) and movement (P135)
  OPTIONAL {{ ?item wdt:P136 ?genre }}
  OPTIONAL {{ ?item wdt:P135 ?movement }}

  # Inception date (P571)
  OPTIONAL {{ ?item wdt:P571 ?inception }}

  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
}}
LIMIT 1
"""


def enrich_from_wikidata(artwork: dict) -> dict:
    """Enrich a single artwork using its Wikidata URI."""
    wikidata_url = artwork.get("wikidata_url")
    if not wikidata_url:
        return artwork

    try:
        query = ARTWORK_QUERY.format(wikidata_uri=wikidata_url)
        bindings = sparql_query(query)
        time.sleep(SPARQL_DELAY)

        if not bindings:
            log.debug(f"No Wikidata results for {wikidata_url}")
            return artwork

        b = bindings[0]

        # --- Physical location (where it's on display) ---
        location_label = val(b, "locationLabel")
        location_lat = val(b, "locationCoordLat")
        location_lng = val(b, "locationCoordLng")

        if location_label or location_lat:
            artwork["institution"]["wikidata_location"] = location_label
            if location_lat and location_lng:
                try:
                    artwork["institution"]["lat"] = float(location_lat)
                    artwork["institution"]["lng"] = float(location_lng)
                    artwork["institution"]["geo_source"] = "wikidata_P276"
                except ValueError:
                    pass

        # --- Artist birthplace ---
        bp_label = val(b, "creatorBirthPlaceLabel")
        bp_lat = val(b, "creatorBirthPlaceLat")
        bp_lng = val(b, "creatorBirthPlaceLng")

        if bp_label or bp_lat:
            artwork.setdefault("artist", {})["birthplace"] = bp_label
            if bp_lat and bp_lng:
                try:
                    artwork["artist"]["birthplace_lat"] = float(bp_lat)
                    artwork["artist"]["birthplace_lng"] = float(bp_lng)
                except ValueError:
                    pass

        # --- Genre and movement (richer than Met's period field) ---
        genre = val(b, "genreLabel")
        movement = val(b, "movementLabel")

        if genre and not artwork.get("classification", {}).get("type"):
            artwork.setdefault("classification", {})["type"] = genre
        if movement and not artwork.get("classification", {}).get("period"):
            artwork.setdefault("classification", {})["period"] = movement

        # --- Inception date (more precise than Met's objectDate string) ---
        inception = val(b, "inception")
        if inception and not artwork.get("date", {}).get("year_start"):
            try:
                year = int(inception[:4])
                artwork.setdefault("date", {})["year_start"] = year
                artwork["date"]["year_end"] = year
            except (ValueError, TypeError):
                pass

        artwork["wikidata_enriched"] = True
        artwork["wikidata_enriched_at"] = datetime.now(timezone.utc).isoformat()

    except Exception as e:
        log.warning(f"Wikidata enrichment failed for {wikidata_url}: {e}")
        artwork["wikidata_enriched"] = False

    return artwork


# ---------------------------------------------------------------------------
# Batch SPARQL for artworks without a Wikidata URL
# (geocode culture field via Wikidata label search)
# ---------------------------------------------------------------------------

CULTURE_GEOCODE_CACHE: dict[str, dict | None] = {}

CULTURE_QUERY = """
SELECT ?place ?placeLabel ?lat ?lng WHERE {{
  ?place wdt:P31/wdt:P279* wd:Q6256 .  # is a country
  ?place rdfs:label "{culture_label}"@en .
  ?place wdt:P625 ?coord .
  BIND(xsd:decimal(REPLACE(STR(?coord), "Point\\\\(([^ ]+) ([^ ]+)\\\\)", "$2")) AS ?lat)
  BIND(xsd:decimal(REPLACE(STR(?coord), "Point\\\\(([^ ]+) ([^ ]+)\\\\)", "$1")) AS ?lng)
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
}}
LIMIT 1
"""


def geocode_culture(culture: str) -> dict | None:
    """Return lat/lng for a culture/country label. Cached."""
    if culture in CULTURE_GEOCODE_CACHE:
        return CULTURE_GEOCODE_CACHE[culture]

    try:
        bindings = sparql_query(CULTURE_QUERY.format(culture_label=culture.replace('"', "")))
        time.sleep(SPARQL_DELAY)
        if bindings:
            b = bindings[0]
            result = {
                "label": val(b, "placeLabel"),
                "lat": float(val(b, "lat") or 0),
                "lng": float(val(b, "lng") or 0),
            }
            CULTURE_GEOCODE_CACHE[culture] = result
            return result
    except Exception as e:
        log.debug(f"Culture geocode failed for '{culture}': {e}")

    CULTURE_GEOCODE_CACHE[culture] = None
    return None


def enrich_fallback(artwork: dict) -> dict:
    """Fallback enrichment: geocode the culture field."""
    culture = artwork.get("classification", {}).get("culture")
    if not culture:
        return artwork

    geo = geocode_culture(culture)
    if geo:
        artwork.setdefault("geo_origin", {}).update({
            "country": geo["label"],
            "lat": geo["lat"],
            "lng": geo["lng"],
            "geo_source": "wikidata_culture_geocode",
        })

    return artwork


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Enrich ArtMap artworks with Wikidata")
    parser.add_argument("--input", default=str(OUTPUT_DIR / "artworks.ndjson"))
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        log.error(f"Input not found: {input_path}. Run ingest_met.py first.")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / "artworks_enriched.ndjson"

    stats = {
        "total": 0,
        "wikidata_direct": 0,
        "wikidata_fallback": 0,
        "no_enrichment": 0,
        "errors": 0,
        "with_display_coordinates": 0,
    }

    with open(input_path) as fin, open(out_path, "w") as fout:
        for i, line in enumerate(fin):
            if args.limit and i >= args.limit:
                break

            artwork = json.loads(line.strip())
            stats["total"] += 1

            if artwork.get("wikidata_url"):
                artwork = enrich_from_wikidata(artwork)
                if artwork.get("wikidata_enriched"):
                    stats["wikidata_direct"] += 1
                else:
                    stats["errors"] += 1
            else:
                artwork = enrich_fallback(artwork)
                if artwork.get("geo_origin", {}).get("lat"):
                    stats["wikidata_fallback"] += 1
                else:
                    stats["no_enrichment"] += 1

            # Track how many have display coordinates
            if artwork.get("institution", {}).get("lat"):
                stats["with_display_coordinates"] += 1

            fout.write(json.dumps(artwork) + "\n")

            if (i + 1) % 100 == 0:
                log.info(
                    f"[{i+1}] direct={stats['wikidata_direct']} "
                    f"fallback={stats['wikidata_fallback']} "
                    f"errors={stats['errors']}"
                )

    # Write stats
    stats_path = OUTPUT_DIR / "enrichment_stats.json"
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)

    log.info(f"\n{'='*50}")
    log.info(f"Total processed : {stats['total']}")
    log.info(f"Wikidata direct : {stats['wikidata_direct']}")
    log.info(f"Culture geocode : {stats['wikidata_fallback']}")
    log.info(f"No enrichment   : {stats['no_enrichment']}")
    log.info(f"With display coords: {stats['with_display_coordinates']}")
    log.info(f"Output: {out_path}")


if __name__ == "__main__":
    main()
