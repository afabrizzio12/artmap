#!/usr/bin/env python3
"""
ArtMap — Met Museum ingestion script
Fetches artworks from the Met Collection API and normalises them
to the ArtMap unified schema.

Usage:
    python ingest_met.py                        # full ingestion (all departments)
    python ingest_met.py --limit 500            # cap at N objects (dev/test)
    python ingest_met.py --department 11        # single department only
    python ingest_met.py --daily-limit 10000    # incremental daily run (reads/writes state file)
    python ingest_met.py --resume               # skip already-fetched object IDs

Output:
    output/met/objects/           raw JSON per object (one file per ID)
    output/met/artworks.ndjson    normalised artworks, newline-delimited (append across daily runs)
    output/met/artworks.json      normalised artworks as JSON array (written on first run only)
    output/met/ingest_state.json  progress state for incremental daily runs
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

# Rate limit: Met enforces ~80 req/min in practice despite docs stating 80 req/s.
REQUEST_DELAY = 1.0  # seconds between requests

OUTPUT_DIR = Path(__file__).parent.parent / "output" / "met"
RAW_DIR = OUTPUT_DIR / "objects"
STATE_FILE = OUTPUT_DIR / "ingest_state.json"

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
session.headers.update({"User-Agent": "ArtMap/0.1 (github.com/afabrizzio12/artmap)"})


def get(endpoint: str, params: dict = None) -> dict:
    url = f"{BASE_URL}/{endpoint}"
    resp = session.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_object_ids(department_id: int = None) -> list[int]:
    """Return object IDs by department.

    The /objects endpoint ignores isPublicDomain/hasImages filters and always
    returns all 500k+ IDs, most of which 403 when fetched individually.
    Fetching per department returns clean, accessible IDs.
    """
    if department_id:
        data = get("objects", {"departmentIds": department_id, "hasImages": "true"})
        return data.get("objectIDs") or []

    # Collect IDs across all departments
    r = session.get(f"{BASE_URL}/departments", timeout=30)
    r.raise_for_status()
    departments = r.json().get("departments", [])
    all_ids: list[int] = []
    seen: set[int] = set()
    for dept in departments:
        data = get("objects", {"departmentIds": dept["departmentId"], "hasImages": "true"})
        for oid in (data.get("objectIDs") or []):
            if oid not in seen:
                seen.add(oid)
                all_ids.append(oid)
        time.sleep(REQUEST_DELAY)
    return all_ids


def fetch_object(object_id: int) -> dict:
    return get(f"objects/{object_id}")


# ---------------------------------------------------------------------------
# State helpers (for incremental daily runs)
# ---------------------------------------------------------------------------

def load_state() -> dict:
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}


def save_state(state: dict) -> None:
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


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
    if not raw.get("isPublicDomain"):
        return None
    if not raw.get("primaryImage"):
        return None
    if not raw.get("title"):
        return None

    object_id = raw["objectID"]
    date_str = raw.get("objectDate", "")

    geo_fields = {
        "country": raw.get("country") or raw.get("culture"),
        "region": raw.get("region") or raw.get("subregion"),
        "city": raw.get("city"),
        "lat": None,
        "lng": None,
    }
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
    parser.add_argument("--limit", type=int, default=None, help="Max objects to process (dev/test)")
    parser.add_argument("--daily-limit", type=int, default=None, help="IDs to process per run; reads/writes ingest_state.json to continue from last offset")
    parser.add_argument("--department", type=int, default=None, help="Filter by department ID")
    parser.add_argument("--resume", action="store_true", help="Skip already-fetched raw objects")
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Fetch all object IDs for this source
    log.info("Fetching object IDs from Met API...")
    all_ids = fetch_object_ids(department_id=args.department)
    total_available = len(all_ids)
    log.info(f"Total IDs available: {total_available}")

    # 2. Determine offset and slice for this run
    state = {}
    offset = 0

    if args.daily_limit:
        state = load_state()
        offset = state.get("offset", 0)
        if offset >= total_available:
            log.info("✅ All IDs have already been processed. Nothing to do.")
            return
        log.info(f"Incremental mode: resuming from offset {offset} / {total_available}")

    object_ids = all_ids[offset:]

    effective_limit = args.daily_limit or args.limit
    if effective_limit:
        object_ids = object_ids[:effective_limit]

    log.info(f"Processing {len(object_ids)} IDs this run")

    # 3. Fetch + normalise
    artworks = []
    skipped = 0
    errors = 0

    for i, oid in enumerate(object_ids):
        raw_path = RAW_DIR / f"{oid}.json"

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

    # 4. Write outputs
    ndjson_path = OUTPUT_DIR / "artworks.ndjson"
    is_first_run = (offset == 0)

    if is_first_run:
        # First run: write fresh files
        artworks_path = OUTPUT_DIR / "artworks.json"
        with open(artworks_path, "w") as f:
            json.dump(artworks, f, indent=2)
        with open(ndjson_path, "w") as f:
            for artwork in artworks:
                f.write(json.dumps(artwork) + "\n")
        log.info(f"Written {len(artworks)} artworks to {artworks_path}")
    else:
        # Subsequent runs: append to ndjson
        with open(ndjson_path, "a") as f:
            for artwork in artworks:
                f.write(json.dumps(artwork) + "\n")
        log.info(f"Appended {len(artworks)} artworks to {ndjson_path}")

    # 5. Update state for incremental runs
    if args.daily_limit:
        new_offset = offset + len(object_ids)
        completed = new_offset >= total_available
        new_total = state.get("total_artworks", 0) + len(artworks)

        save_state({
            "offset": new_offset,
            "total_available": total_available,
            "total_artworks": new_total,
            "completed": completed,
            "last_run": datetime.now(timezone.utc).isoformat(),
        })

        log.info(f"\nState saved: {new_total} total artworks | offset {new_offset}/{total_available}")
        if completed:
            log.info("🎉 All Met Museum IDs have been processed. Ingestion COMPLETE.")
        else:
            remaining_days = -(-( total_available - new_offset) // args.daily_limit)  # ceiling div
            log.info(f"Estimated {remaining_days} more daily run(s) to complete.")
    else:
        log.info(f"\nDone. {len(artworks)} artworks | Skipped: {skipped} | Errors: {errors}")


if __name__ == "__main__":
    main()
