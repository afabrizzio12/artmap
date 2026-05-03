#!/usr/bin/env python3
"""
One-shot migration: NDJSON files → Supabase Postgres.

Reads:
  - output/wikidata/institutions.json
  - output/wikidata/artworks/*.ndjson
  - output/met/artworks.ndjson  (if present)

Writes to Supabase tables: institutions, artists, artworks
Idempotent: safe to re-run, uses upsert.

Uses plain requests (not supabase-py) to avoid heavy dependency and
package install failures in CI.

Insert order respects FK constraints:
  1. institutions  (no deps)
  2. artists       (self-ref student_of_qid handled in two passes)
  3. artworks      (FK → institutions, artists)
"""

import glob
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set", file=sys.stderr)
    sys.exit(1)

BATCH_SIZE = 300
REST_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates,return=minimal",
}

session = requests.Session()
session.headers.update(REST_HEADERS)


def upsert(table: str, rows: list, conflict_col: str = "id") -> None:
    if not rows:
        return
    url = f"{SUPABASE_URL}/rest/v1/{table}?on_conflict={conflict_col}"
    # Send in BATCH_SIZE chunks
    for i in range(0, len(rows), BATCH_SIZE):
        chunk = rows[i : i + BATCH_SIZE]
        try:
            resp = session.post(url, json=chunk, timeout=60)
            if resp.status_code not in (200, 201):
                print(f"  ! {table} batch {i//BATCH_SIZE}: HTTP {resp.status_code} — {resp.text[:200]}")
        except Exception as e:
            print(f"  ! {table} batch {i//BATCH_SIZE} error: {e}")


def is_valid_qid(qid) -> bool:
    if not qid:
        return False
    if str(qid).startswith("http"):
        return False
    return str(qid).startswith("Q")


# ============================================================
# STEP 1: Institutions
# ============================================================
print("\n[1/3] Migrating institutions...")
inst_path = Path("output/wikidata/institutions.json")
if not inst_path.exists():
    print(f"  ! Not found: {inst_path}")
    inst_rows = []
else:
    with open(inst_path) as f:
        institutions_raw = json.load(f)

    inst_rows = []
    for i in institutions_raw:
        qid = i.get("qid") or i.get("wikidata_qid") or i.get("id")
        if not qid:
            continue
        inst_rows.append({
            "id": qid,
            "name": i.get("name") or "Unknown institution",
            "wikidata_qid": qid,
            "country": i.get("country"),
            "city": i.get("city"),
            "lat": i.get("lat"),
            "lng": i.get("lng"),
        })

    print(f"  Found {len(inst_rows)} institutions")
    for i in tqdm(range(0, len(inst_rows), BATCH_SIZE), desc="  Institutions"):
        upsert("institutions", inst_rows[i : i + BATCH_SIZE])


# ============================================================
# STEP 2a: Scan all files, collect unique artists
# ============================================================
print("\n[2a/3] Scanning ndjson files for artists...")

ndjson_paths = sorted(
    glob.glob("output/wikidata/artworks/*.ndjson")
    + glob.glob("output/wikidata/artworks.ndjson")
    + glob.glob("output/met/artworks.ndjson")
)
print(f"  Found {len(ndjson_paths)} ndjson files")

artists_seen: dict[str, dict] = {}
total_lines = 0
skipped = 0

for path in ndjson_paths:
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                a = json.loads(line)
            except json.JSONDecodeError:
                skipped += 1
                continue
            total_lines += 1
            artist = a.get("artist") or {}
            artist_qid = artist.get("wikidata_qid")
            artist_name = artist.get("display_name") or artist.get("name")
            if is_valid_qid(artist_qid) and artist_qid not in artists_seen:
                if artist_name and not str(artist_name).startswith("http"):
                    artists_seen[artist_qid] = {
                        "wikidata_qid": artist_qid,
                        "name": artist_name,
                        "display_name": artist_name,
                        "nationality": artist.get("nationality"),
                        "student_of_qid": (
                            artist.get("student_of_qid")
                            if is_valid_qid(artist.get("student_of_qid"))
                            else None
                        ),
                    }

print(f"  Scanned {total_lines} records → {len(artists_seen)} artists (skipped {skipped})")


# ============================================================
# STEP 2b: Upsert artists (pass 1 — no teacher links to avoid self-FK)
# ============================================================
print(f"\n[2b/3] Upserting {len(artists_seen)} artists...")
artists_list = [{**a, "student_of_qid": None} for a in artists_seen.values()]
for i in tqdm(range(0, len(artists_list), BATCH_SIZE), desc="  Artists"):
    upsert("artists", artists_list[i : i + BATCH_SIZE], conflict_col="wikidata_qid")


# ============================================================
# STEP 3: Stream artworks file-by-file
# ============================================================
print(f"\n[3/3] Upserting artworks (streaming)...")
total_written = 0

for path in tqdm(ndjson_paths, desc="  Files"):
    batch: list[dict] = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                a = json.loads(line)
            except json.JSONDecodeError:
                continue

            if not a.get("id") or not a.get("title"):
                continue

            inst = a.get("institution") or {}
            inst_id = inst.get("id") or inst.get("wikidata_qid")
            if not is_valid_qid(inst_id):
                continue

            artist = a.get("artist") or {}
            artist_qid = artist.get("wikidata_qid")
            artist_name = artist.get("display_name") or artist.get("name")
            if not is_valid_qid(artist_qid) or artist_qid not in artists_seen:
                artist_qid = None

            date = a.get("date") or {}
            classification = a.get("classification") or {}
            images = a.get("images") or {}

            batch.append({
                "id": a["id"],
                "source": a.get("source", "unknown"),
                "source_id": str(a.get("source_id", "")),
                "title": a["title"][:500],
                "artist_qid": artist_qid,
                "artist_name": (
                    artist_name
                    if artist_name and not str(artist_name).startswith("http")
                    else None
                ),
                "institution_id": inst_id,
                "year_start": date.get("year_start"),
                "year_end": date.get("year_end"),
                "date_display": date.get("display"),
                "classification": classification.get("type"),
                "genre": classification.get("genre"),
                "movement": classification.get("period"),
                "image_url": images.get("primary"),
                "image_thumb_url": images.get("primary_small"),
                "source_url": a.get("source_url"),
                "is_public_domain": a.get("is_public_domain", True),
                "license": a.get("license", "CC0"),
            })

            if len(batch) >= BATCH_SIZE:
                upsert("artworks", batch)
                total_written += len(batch)
                batch = []

    if batch:
        upsert("artworks", batch)
        total_written += len(batch)

print(f"  Upserted {total_written} artworks total")


# ============================================================
# STEP 4: Teacher links (pass 2)
# ============================================================
artists_with_teacher = [
    a for a in artists_seen.values()
    if a.get("student_of_qid") and a["student_of_qid"] in artists_seen
]
if artists_with_teacher:
    print(f"\n  Pass 2: updating {len(artists_with_teacher)} teacher links...")
    for i in tqdm(range(0, len(artists_with_teacher), BATCH_SIZE), desc="  Teacher links"):
        upsert("artists", artists_with_teacher[i : i + BATCH_SIZE], conflict_col="wikidata_qid")


# ============================================================
# DONE
# ============================================================
print("\n✓ Migration complete.")
print(f"  institutions: {len(inst_rows)}")
print(f"  artists:      {len(artists_seen)}")
print(f"  artworks:     {total_written}")
