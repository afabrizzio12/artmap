#!/usr/bin/env python3
"""
ArtMap — Wikidata ingestion script  (institution-first strategy)
================================================================

Why institution-first?
  SPARQL global queries (type=painting, ORDER BY, OFFSET N) time out beyond
  OFFSET ~500 because Wikidata must scan the entire preceding result set.

  Instead we:
    1. Build an institution index: all art museums worldwide with coordinates.
       (One fast query per page, ~2000 museums per page, no heavy joins.)
    2. For each institution, fetch its artworks.
       (Bounded per-institution queries — fast, resumable, naturally diverse.)

  This gives us 50,000+ institutions across every country, which is exactly
  the geographic diversity ArtMap needs.

Why Wikidata:
  - Only *notable* artworks get a Wikidata entry → built-in quality filter
  - 50,000+ institutions worldwide → maximum geographic diversity
  - Knowledge graph: artist teacher/student, movements, periods
  - Coordinates on every institution → every artwork gets a map pin
  - Free, no API key, CC0 data

Usage:
    # Step 1 (first time only): build the institution index
    python ingest_wikidata.py --build-index

    # Step 2 (daily): ingest artworks, iterating through institutions
    python ingest_wikidata.py
    python ingest_wikidata.py --daily-limit 5000
    python ingest_wikidata.py --reset   # clear state and restart

Output:
    output/wikidata/institutions.json         index of all art museums (built once)
    output/wikidata/artworks/{qid}.ndjson     normalised artworks, one file per institution
    output/wikidata/ingest_state.json         progress state

Migration (run once after upgrading from monolithic artworks.ndjson):
    python ingest_wikidata.py --migrate
"""

import argparse
import json
import logging
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

# Supabase — optional; enabled when env vars are present
_sb = None
def _get_supabase():
    global _sb
    if _sb is None:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_KEY")
        if url and key:
            from supabase import create_client
            _sb = create_client(url, key)
    return _sb

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "ArtMap/0.1 (https://github.com/afabrizzio12/artmap; contact via GitHub)"

# Wikidata rate limit: be polite
REQUEST_DELAY = 2.0          # seconds between SPARQL requests
INST_PAGE_SIZE = 2000        # institutions per SPARQL page
ARTWORK_PAGE_SIZE = 1000     # artworks per institution (most have <500)

OUTPUT_DIR = Path(__file__).parent.parent / "output" / "wikidata"
ARTWORKS_DIR = OUTPUT_DIR / "artworks"          # per-institution ndjson files
INSTITUTIONS_FILE = OUTPUT_DIR / "institutions.json"
STATE_FILE = OUTPUT_DIR / "ingest_state.json"
LEGACY_NDJSON = OUTPUT_DIR / "artworks.ndjson"  # pre-migration monolithic file

# Institution types to include — art museums + art galleries + similar
INSTITUTION_TYPE_QIDS = [
    "wd:Q207694",   # art museum
    "wd:Q1007870",  # art gallery
    "wd:Q856234",   # art museum (alt)
    "wd:Q33506",    # museum (broader, captures smaller local museums)
]

# Artwork types that indicate fine art
ARTWORK_TYPE_QIDS = [
    "wd:Q3305213",   # painting
    "wd:Q860861",    # sculpture
    "wd:Q93184",     # drawing
    "wd:Q11835431",  # print (artwork)
    "wd:Q125191",    # photograph
    "wd:Q15123870",  # work of art (generic fallback)
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SPARQL helpers
# ---------------------------------------------------------------------------

session = requests.Session()
session.headers.update({
    "User-Agent": USER_AGENT,
    "Accept": "application/sparql-results+json",
})


def sparql(query: str, timeout: int = 50) -> list[dict]:
    resp = session.get(
        SPARQL_ENDPOINT,
        params={"query": query, "format": "json"},
        timeout=timeout,
    )
    if resp.status_code == 429:
        retry_after = int(resp.headers.get("Retry-After", 60))
        log.warning(f"429 Too Many Requests — sleeping {retry_after}s")
        time.sleep(retry_after)
        # Retry once after back-off
        resp = session.get(
            SPARQL_ENDPOINT,
            params={"query": query, "format": "json"},
            timeout=timeout,
        )
    resp.raise_for_status()
    return resp.json().get("results", {}).get("bindings", [])


def val(b: dict, key: str) -> str | None:
    return b.get(key, {}).get("value") or None


def parse_point(wkt: str | None) -> tuple[float | None, float | None]:
    """Extract (lat, lng) from WKT like 'Point(2.3522 48.8566)'."""
    if not wkt:
        return None, None
    m = re.search(r"Point\(([^\s]+)\s+([^\)]+)\)", wkt)
    if not m:
        return None, None
    try:
        return float(m.group(2)), float(m.group(1))   # lat, lng
    except ValueError:
        return None, None


# ---------------------------------------------------------------------------
# Phase 1 — build institution index
# ---------------------------------------------------------------------------

INSTITUTION_INDEX_QUERY = """
SELECT ?inst ?instLabel ?coords ?country ?countryLabel ?city ?cityLabel
WHERE {{
  ?inst wdt:P31/wdt:P279* {type_qid} .
  ?inst wdt:P625 ?coords .
  OPTIONAL {{ ?inst wdt:P17 ?country }}
  OPTIONAL {{ ?inst wdt:P131 ?city }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,fr,de,es,it,nl,pt,ru" . }}
}}
LIMIT {limit}
OFFSET {offset}
"""


def fetch_institution_page(type_qid: str, offset: int) -> list[dict]:
    """Fetch one page of institutions of the given type."""
    query = INSTITUTION_INDEX_QUERY.format(
        type_qid=type_qid,
        limit=INST_PAGE_SIZE,
        offset=offset,
    )
    return sparql(query)


def build_institution_index() -> list[dict]:
    """Fetch all art museums with coordinates from Wikidata.

    Queries one institution type at a time (single-type queries are fast;
    multi-type VALUES + DISTINCT times out on large result sets).
    """
    seen_qids: set[str] = set()
    all_institutions: list[dict] = []

    log.info("Building institution index from Wikidata...")

    for type_qid in INSTITUTION_TYPE_QIDS:
        log.info(f"  Type: {type_qid}")
        offset = 0
        consecutive_errors = 0

        while True:
            log.info(f"    offset={offset}")
            try:
                bindings = fetch_institution_page(type_qid, offset)
                consecutive_errors = 0
            except Exception as e:
                log.warning(f"    Page failed: {e}")
                consecutive_errors += 1
                if consecutive_errors >= 3:
                    log.warning("    Too many errors — moving to next type")
                    break
                time.sleep(10)
                continue

            if not bindings:
                break

            for b in bindings:
                inst_uri = val(b, "inst")
                if not inst_uri:
                    continue
                qid = inst_uri.split("/")[-1]
                if qid in seen_qids:
                    continue
                seen_qids.add(qid)

                coords = val(b, "coords")
                lat, lng = parse_point(coords)
                if lat is None:
                    continue    # skip institutions without coordinates

                all_institutions.append({
                    "qid": qid,
                    "name": val(b, "instLabel") or qid,
                    "wikidata_url": inst_uri,
                    "country": val(b, "countryLabel"),
                    "city": val(b, "cityLabel"),
                    "lat": lat,
                    "lng": lng,
                })

            log.info(f"    Page done: {len(bindings)} rows | {len(all_institutions)} total so far")

            if len(bindings) < INST_PAGE_SIZE:
                break

            offset += INST_PAGE_SIZE
            time.sleep(REQUEST_DELAY)

        time.sleep(REQUEST_DELAY)

    # Deduplicate and sort by QID
    all_institutions.sort(key=lambda x: int(x["qid"].lstrip("Q")))
    countries = {i["country"] for i in all_institutions if i["country"]}
    log.info(f"Institution index complete: {len(all_institutions)} museums in {len(countries)} countries")
    return all_institutions


# ---------------------------------------------------------------------------
# Phase 2 — fetch artworks per institution
# ---------------------------------------------------------------------------

ARTWORKS_FOR_INST_QUERY = """
SELECT ?artwork ?artworkLabel ?image ?type ?typeLabel ?artist ?artistLabel ?inception
WHERE {{
  ?artwork wdt:P195 wd:{inst_qid} .
  ?artwork wdt:P18 ?image .
  OPTIONAL {{ ?artwork wdt:P31 ?type }}
  OPTIONAL {{ ?artwork wdt:P170 ?artist }}
  OPTIONAL {{ ?artwork wdt:P571 ?inception }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,fr,de,es,it,nl,pt,ru" . }}
}}
LIMIT {limit}
OFFSET {offset}
"""


def fetch_artworks_for_institution(inst: dict) -> list[dict]:
    """Fetch all artworks held by a given institution."""
    artworks = []
    seen_qids: set[str] = set()
    offset = 0

    while True:
        query = ARTWORKS_FOR_INST_QUERY.format(
            inst_qid=inst["qid"],
            limit=ARTWORK_PAGE_SIZE,
            offset=offset,
        )
        try:
            bindings = sparql(query)
        except Exception as e:
            log.warning(f"    [{inst['qid']}] artwork page failed: {e}")
            break

        if not bindings:
            break

        for b in bindings:
            artwork = normalise_artwork(b, inst)
            if artwork and artwork["source_id"] not in seen_qids:
                seen_qids.add(artwork["source_id"])
                artworks.append(artwork)

        if len(bindings) < ARTWORK_PAGE_SIZE:
            break

        offset += ARTWORK_PAGE_SIZE
        time.sleep(REQUEST_DELAY)

    return artworks


# ---------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------

def normalise_artwork(b: dict, inst: dict) -> dict | None:
    artwork_uri = val(b, "artwork")
    if not artwork_uri:
        return None

    qid = artwork_uri.split("/")[-1]
    image_url = val(b, "image")
    title = val(b, "artworkLabel")

    if not image_url or not title:
        return None
    # Skip if title is just the QID (no English/multilingual label resolved)
    if title == qid:
        return None

    # Artist — filter out blank nodes (anonymous artists with no Wikidata entity)
    artist_uri = val(b, "artist")
    if artist_uri and ".well-known/genid" in artist_uri:
        artist_uri = None
    artist_qid = artist_uri.split("/")[-1] if artist_uri else None

    # Artist label — label service falls back to bare QID if unresolved
    artist_label = val(b, "artistLabel")
    if artist_label and re.match(r"^Q\d+$", artist_label):
        artist_label = None

    # Inception year
    inception_raw = val(b, "inception")
    inception_year = None
    if inception_raw:
        try:
            inception_year = int(inception_raw[:4])
        except (ValueError, TypeError):
            pass

    # Commons thumbnail (800px)
    thumbnail = image_url
    if "Special:FilePath/" in image_url:
        filename = image_url.split("Special:FilePath/")[-1]
        thumbnail = f"https://commons.wikimedia.org/wiki/Special:FilePath/{filename}?width=800"

    # Artwork type label — also filter bare QIDs
    type_label = val(b, "typeLabel")
    if type_label and re.match(r"^Q\d+$", type_label):
        type_label = None

    return {
        "id": f"wikidata:{qid}",
        "source": "wikidata",
        "source_id": qid,
        "source_url": f"https://www.wikidata.org/wiki/{qid}",
        "title": title,
        "artist": {
            "name": artist_label,
            "display_name": artist_label,
            "wikidata_qid": artist_qid,
            "wikidata_url": artist_uri,
            # enriched later by enrich_wikidata.py
            "nationality": None,
            "student_of_qid": None,
            "student_of_name": None,
        },
        "date": {
            "display": str(inception_year) if inception_year else None,
            "year_start": inception_year,
            "year_end": inception_year,
        },
        "classification": {
            "type": type_label,
            "period": None,   # enriched later
            "genre": None,    # enriched later
            "tags": [],
        },
        "institution": {
            "id": inst["qid"],
            "name": inst["name"],
            "wikidata_qid": inst["qid"],
            "wikidata_url": inst["wikidata_url"],
            "country": inst["country"],
            "city": inst["city"],
            "lat": inst["lat"],
            "lng": inst["lng"],
        },
        "geo_origin": {
            "country": None,   # enriched later
        },
        "images": {
            "primary": image_url,
            "primary_small": thumbnail,
            "additional": [],
        },
        "is_public_domain": True,
        "license": "CC0",
        "wikidata_url": artwork_uri,
        "ingested_at": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------

def load_state() -> dict:
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}


def save_state(state: dict) -> None:
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def load_institutions() -> list[dict]:
    if not INSTITUTIONS_FILE.exists():
        return []
    with open(INSTITUTIONS_FILE) as f:
        return json.load(f)


def save_institutions(institutions: list[dict]) -> None:
    with open(INSTITUTIONS_FILE, "w") as f:
        json.dump(institutions, f, indent=2)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _is_valid_qid(qid: str | None) -> bool:
    return bool(qid and qid.startswith("Q") and not qid.startswith("http"))


def _to_artwork_row(a: dict) -> dict:
    inst = a.get("institution") or {}
    artist = a.get("artist") or {}
    date = a.get("date") or {}
    cls = a.get("classification") or {}
    images = a.get("images") or {}
    artist_qid = artist.get("wikidata_qid")
    artist_name = artist.get("display_name") or artist.get("name")
    return {
        "id": a["id"],
        "source": a.get("source", "wikidata"),
        "source_id": a.get("source_id", ""),
        "title": (a.get("title") or "")[:500],
        "artist_qid": artist_qid if _is_valid_qid(artist_qid) else None,
        "artist_name": artist_name if artist_name and not artist_name.startswith("http") else None,
        "institution_id": inst.get("id") or inst.get("wikidata_qid"),
        "year_start": date.get("year_start"),
        "year_end": date.get("year_end"),
        "date_display": date.get("display"),
        "classification": cls.get("type"),
        "genre": cls.get("genre"),
        "movement": cls.get("period"),
        "image_url": images.get("primary"),
        "image_thumb_url": images.get("primary_small"),
        "source_url": a.get("source_url"),
        "is_public_domain": a.get("is_public_domain", True),
        "license": a.get("license", "CC0"),
    }


_SB_BATCH = 500


def _sb_upsert(table: str, rows: list, conflict_col: str = "id") -> None:
    sb = _get_supabase()
    if not sb or not rows:
        return
    for i in range(0, len(rows), _SB_BATCH):
        chunk = rows[i : i + _SB_BATCH]
        try:
            sb.table(table).upsert(chunk, on_conflict=conflict_col).execute()
        except Exception as e:
            log.warning(f"  Supabase upsert failed on {table}: {e}")


def _upsert_institution(inst: dict) -> None:
    _sb_upsert("institutions", [{
        "id": inst["qid"],
        "name": inst["name"],
        "wikidata_qid": inst["qid"],
        "country": inst.get("country"),
        "city": inst.get("city"),
        "lat": inst.get("lat"),
        "lng": inst.get("lng"),
    }])


def write_institution_artworks(qid: str, artworks: list[dict], mode: str = "a") -> None:
    """Write artworks for one institution to its own ndjson file and upsert to Supabase."""
    if not artworks:
        return
    ARTWORKS_DIR.mkdir(parents=True, exist_ok=True)
    path = ARTWORKS_DIR / f"{qid}.ndjson"
    with open(path, mode) as f:
        for aw in artworks:
            f.write(json.dumps(aw) + "\n")

    # Supabase: upsert artists first (avoids FK violation on artworks.artist_qid)
    artists: dict[str, dict] = {}
    for a in artworks:
        artist = a.get("artist") or {}
        aqid = artist.get("wikidata_qid")
        aname = artist.get("display_name") or artist.get("name")
        if _is_valid_qid(aqid) and aqid not in artists and aname and not aname.startswith("http"):
            artists[aqid] = {
                "wikidata_qid": aqid,
                "name": aname,
                "display_name": aname,
                "nationality": artist.get("nationality"),
                "student_of_qid": artist.get("student_of_qid")
                    if _is_valid_qid(artist.get("student_of_qid")) else None,
            }
    if artists:
        _sb_upsert("artists", list(artists.values()), conflict_col="wikidata_qid")

    # Upsert artworks
    rows = [_to_artwork_row(a) for a in artworks]
    _sb_upsert("artworks", rows)


def migrate_legacy_ndjson() -> None:
    """One-time migration: split artworks.ndjson into per-institution files.

    Reads the old monolithic artworks.ndjson (if it exists), groups records
    by institution QID, and writes each group to artworks/{qid}.ndjson.
    Safe to re-run — existing per-institution files are overwritten.
    """
    if not LEGACY_NDJSON.exists():
        log.info("No legacy artworks.ndjson found — nothing to migrate.")
        return

    log.info(f"Migrating {LEGACY_NDJSON} → per-institution files in {ARTWORKS_DIR}/")
    ARTWORKS_DIR.mkdir(parents=True, exist_ok=True)

    buckets: dict[str, list[str]] = {}
    total = 0
    with open(LEGACY_NDJSON) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                qid = record.get("institution", {}).get("id") or "unknown"
                buckets.setdefault(qid, []).append(line)
                total += 1
            except json.JSONDecodeError:
                continue

    for qid, lines in buckets.items():
        path = ARTWORKS_DIR / f"{qid}.ndjson"
        with open(path, "w") as f:
            f.write("\n".join(lines) + "\n")

    log.info(f"Migration complete: {total} records → {len(buckets)} institution files")
    log.info(f"You can now delete {LEGACY_NDJSON} and remove it from git tracking:")
    log.info(f"  git rm --cached output/wikidata/artworks.ndjson")
    log.info(f"  echo 'output/wikidata/artworks.ndjson' >> .gitignore")


def main():
    parser = argparse.ArgumentParser(description="Ingest artworks from Wikidata (institution-first)")
    parser.add_argument("--build-index", action="store_true",
                        help="(Re-)build the institution index and exit")
    parser.add_argument("--daily-limit", type=int, default=5000,
                        help="Max artworks to collect per run (default: 5000)")
    parser.add_argument("--reset", action="store_true",
                        help="Clear artwork state and restart from first institution")
    parser.add_argument("--migrate", action="store_true",
                        help="One-time: split legacy artworks.ndjson into per-institution files")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ARTWORKS_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Migration helper
    # ------------------------------------------------------------------
    if args.migrate:
        migrate_legacy_ndjson()
        return

    # ------------------------------------------------------------------
    # Step 1: build institution index (or refresh)
    # ------------------------------------------------------------------
    if args.build_index:
        institutions = build_institution_index()
        save_institutions(institutions)
        log.info(f"Saved {len(institutions)} institutions to {INSTITUTIONS_FILE}")
        # Mirror to Supabase
        inst_rows = [
            {"id": i["qid"], "name": i["name"], "wikidata_qid": i["qid"],
             "country": i.get("country"), "city": i.get("city"),
             "lat": i.get("lat"), "lng": i.get("lng")}
            for i in institutions
        ]
        _sb_upsert("institutions", inst_rows)
        if _get_supabase():
            log.info(f"Upserted {len(inst_rows)} institutions to Supabase")
        return

    # ------------------------------------------------------------------
    # Step 2: incremental artwork ingestion
    # ------------------------------------------------------------------

    institutions = load_institutions()
    if not institutions:
        log.error("No institution index found. Run with --build-index first.")
        sys.exit(1)

    # Load or reset state
    if args.reset:
        if STATE_FILE.exists():
            STATE_FILE.unlink()
        if ARTWORKS_DIR.exists():
            import shutil
            shutil.rmtree(ARTWORKS_DIR)
        ARTWORKS_DIR.mkdir(parents=True, exist_ok=True)
        log.info("State reset.")
    state = load_state()

    completed = state.get("completed", False)
    if completed:
        log.info("✅ Wikidata ingestion already complete. Use --reset to restart.")
        return

    # Resume from last institution index
    inst_offset = state.get("inst_offset", 0)
    total_so_far = state.get("total_artworks", 0)
    seen_artwork_qids: set[str] = set(state.get("seen_qids", []))

    log.info(f"Wikidata ingestion | institutions={len(institutions)} | resuming from #{inst_offset} | "
             f"artworks so far={total_so_far} | daily_limit={args.daily_limit}")

    artworks_this_run = 0
    errors = 0

    i = inst_offset
    while i < len(institutions) and artworks_this_run < args.daily_limit:
        inst = institutions[i]
        log.info(f"[{i+1}/{len(institutions)}] {inst['name']} ({inst.get('country','?')}) — {inst['qid']}")

        try:
            artworks = fetch_artworks_for_institution(inst)
        except Exception as e:
            log.warning(f"  Failed: {e}")
            errors += 1
            i += 1
            time.sleep(REQUEST_DELAY)
            continue

        new_artworks = [a for a in artworks if a["source_id"] not in seen_artwork_qids]
        for a in new_artworks:
            seen_artwork_qids.add(a["source_id"])

        # Write this institution's artworks to its own file
        write_institution_artworks(inst["qid"], new_artworks)
        artworks_this_run += len(new_artworks)
        log.info(f"  → {len(new_artworks)} new artworks (total this run: {artworks_this_run})")

        i += 1

        # Checkpoint state after each institution
        save_state({
            "inst_offset": i,
            "total_artworks": total_so_far + artworks_this_run,
            "completed": False,
            "last_run": datetime.now(timezone.utc).isoformat(),
        })

        time.sleep(REQUEST_DELAY)

    completed = (i >= len(institutions))
    new_total = total_so_far + artworks_this_run
    save_state({
        "inst_offset": i,
        "total_artworks": new_total,
        "completed": completed,
        "last_run": datetime.now(timezone.utc).isoformat(),
    })

    log.info(f"\n{'='*60}")
    log.info(f"This run   : {artworks_this_run} new artworks")
    log.info(f"Total      : {new_total} artworks")
    log.info(f"Institutions processed: {i}/{len(institutions)}")
    log.info(f"Errors     : {errors}")
    if completed:
        log.info("🎉 Wikidata ingestion COMPLETE — all institutions processed")
    else:
        remaining = len(institutions) - i
        log.info(f"~{remaining} institutions remaining")


if __name__ == "__main__":
    main()
