#!/usr/bin/env python3
"""
ArtMap — Met Museum ingestion script
Fetches artworks from the Met Collection API and normalises them
to the ArtMap unified schema.

Usage:
    python ingest_met.py                        # full ingestion (all public domain objects)
    python ingest_met.py --limit 500            # cap at N objects (dev/test)
    python ingest_met.py --department 11        # single department only
    python ingest_met.py --resume               # skip already-fetched object IDs

Output:
    output/met/objects/        raw JSON per object (one file per ID)
    output/met/artworks.json   all normalised artworks as JSON array
    output/met/artworks.ndjson normalised artworks as newline-delimited JSON
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BASE_URL = "https://collectionapi.metmuseum.org/public/collection/v1"
INSTITUTION = {
    "id": "met",
    "name": "The Metropolitan Museum of Art",
    "city": "New York",
    "country": "United States",
    "lat": 40.7794,
    "lng": -73.9632,
}

# Rate limit: Met allows 80 req/s. We stay well under.
REQUEST_DELAY = 0.05  # seconds between requests

OUTPUT_DIR = Path(__file__).parent.parent / "output" / "met"
RAW_DIR = OUTPUT_DIR / "objects"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

session = requests.Session()
session.headers.update({"User-Agent": "ArtMap/0.1 (github.com/your-org/artmap-data)"})


def get(endpoint: str, params: dict = None) -> dict:
    url = f"{BASE_URL}/{endpoint}"
    resp = session.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_object_ids(department_id: int = None) -> list[int]:
    """Return all object IDs with public domain images."""
    params = {"hasImages": "true"}
    if department_id:
        params["departmentIds"] = department_id
    # The /objects endpoint returns all valid IDs
    data = get("objects", params)
    return data.get("objectIDs") or []


def fetch_object(object_id: int) -> dict:
    return get(f"objects/{object_id}")


# ---------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------

def parse_year(s: str) -> int | None:
    """Extract the first 4-digit year from a string."""
    if not s:
        return None
    import re
    m = re.search(r"\b(\d{4})\b", s)
    return int(m.group(1)) if m else None


def normalise(raw: dict) -> dict | None:
    """Map a raw Met API object to the ArtMap unified schema.

    Returns None if the object should be skipped (e.g. not public domain,
    no image, or missing required fields).
    """
    # Only keep public domain works with at least a primary image
    if not raw.get("isPublicDomain"):
        return None
    if not raw.get("primaryImage"):
        return None
    if not raw.get("title"):
        return None

    object_id = raw["objectID"]
    date_str = raw.get("objectDate", "")

    # Resolve geo_origin from Met's granular geo fields
    geo_fields = {
        "country": raw.get("country") or raw.get("culture"),
        "region": raw.get("region") or raw.get("subregion"),
        "city": raw.get("city"),
        "lat": None,
        "lng": None,
    }
    # Blank strings → None
    geo_origin = {k: v if v else None for k, v in geo_fields.items()}

    tags = [
        {
            "term": t.get("term"),
            "aat_url": t.get("AAT_URL"),
            "wikidata_url": t.get("Wikidata_URL"),
        }
        for t in (raw.get("tags") or [])
    ]

    return {
        "id": f"met:{object_id}",
        "source": "met",
        "source_id": object_id,
        "source_url": raw.get("objectURL"),
        "title": raw["title"],
        "title_alt": raw.get("title") if raw.get("titleAlt") else None,
        "artist": {
            "name": raw.get("artistDisplayName") or None,
            "display_name": raw.get("artistDisplayName") or None,
            "birth_year": parse_year(raw.get("artistBeginDate", "")),
            "death_year": parse_year(raw.get("artistEndDate", "")),
            "nationality": raw.get("artistNationality") or None,
            "wikidata_url": raw.get("artistWikidata_URL") or None,
            "ulan_url": raw.get("artistULAN_URL") or None,
        },
        "date": {
            "display": date_str or None,
            "year_start": parse_year(str(raw.get("objectBeginDate") or "")),
            "year_end": parse_year(str(raw.get("objectEndDate") or "")),
        },
        "classification": {
            "department": raw.get("department") or None,
            "type": raw.get("objectName") or None,
            "medium": raw.get("medium") or None,
            "culture": raw.get("culture") or None,
            "period": raw.get("period") or None,
            "tags": tags,
        },
        "institution": {
            **INSTITUTION,
            "gallery_number": raw.get("GalleryNumber") or None,
            "is_on_view": bool(raw.get("GalleryNumber")),
        },
        "geo_origin": geo_origin,
        "images": {
            "primary": raw.get("primaryImage") or None,
            "primary_small": raw.get("primaryImageSmall") or None,
            "additional": raw.get("additionalImages") or [],
        },
        "dimensions": raw.get("dimensions") or None,
        "is_public_domain": True,
        "license": "CC0",
        "wikidata_url": raw.get("objectWikidata_URL") or None,
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "source_updated_at": raw.get("metadataDate") or None,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Ingest Met Museum artworks into ArtMap schema")
    parser.add_argument("--limit", type=int, default=None, help="Max objects to process")
    parser.add_argument("--department", type=int, default=None, help="Filter by department ID")
    parser.add_argument("--resume", action="store_true", help="Skip already-fetched raw objects")
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Fetch object IDs
    log.info("Fetching object IDs from Met API...")
    object_ids = fetch_object_ids(department_id=args.department)
    log.info(f"Total object IDs returned: {len(object_ids)}")

    if args.limit:
        object_ids = object_ids[: args.limit]
        log.info(f"Limiting to {args.limit} objects")

    # 2. Fetch + normalise
    artworks = []
    skipped = 0
    errors = 0

    for i, oid in enumerate(object_ids):
        raw_path = RAW_DIR / f"{oid}.json"

        # Resume: use cached raw file if present
        if args.resume and raw_path.exists():
            with open(raw_path) as f:
                raw = json.load(f)
        else:
            try:
                raw = fetch_object(oid)
                with open(raw_path, "w") as f:
                    json.dump(raw, f)
                time.sleep(REQUEST_DELAY)
            except Exception as e:
                log.warning(f"[{i+1}/{len(object_ids)}] Error fetching {oid}: {e}")
                errors += 1
                continue

        normalised = normalise(raw)
        if normalised is None:
            skipped += 1
        else:
            artworks.append(normalised)

        if (i + 1) % 500 == 0:
            log.info(f"Progress: {i+1}/{len(object_ids)} — {len(artworks)} kept, {skipped} skipped, {errors} errors")

    # 3. Write outputs
    artworks_path = OUTPUT_DIR / "artworks.json"
    with open(artworks_path, "w") as f:
        json.dump(artworks, f, indent=2)

    ndjson_path = OUTPUT_DIR / "artworks.ndjson"
    with open(ndjson_path, "w") as f:
        for artwork in artworks:
            f.write(json.dumps(artwork) + "\n")

    log.info(
        f"\nDone. {len(artworks)} artworks written to {artworks_path}\n"
        f"Skipped: {skipped} | Errors: {errors}"
    )


if __name__ == "__main__":
    main()
