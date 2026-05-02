#!/usr/bin/env python3
"""
One-shot migration: NDJSON files → Supabase Postgres.

Reads:
  - output/wikidata/institutions.json
  - output/wikidata/artworks/*.ndjson
  - output/met/artworks.ndjson  (if present)

Writes to Supabase tables: institutions, artists, artworks
Idempotent: safe to re-run, uses upsert.

Insert order respects FK constraints:
  1. institutions  (no deps)
  2. artists       (self-ref student_of_qid handled in two passes)
  3. artworks      (FK → institutions, artists)
"""

import glob
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client
from tqdm import tqdm

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
BATCH_SIZE = 500

sb = create_client(SUPABASE_URL, SUPABASE_KEY)


def chunked(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def upsert_batch(table: str, rows: list, conflict_col: str = "id"):
    if not rows:
        return
    for chunk in chunked(rows, BATCH_SIZE):
        try:
            sb.table(table).upsert(chunk, on_conflict=conflict_col).execute()
        except Exception as e:
            print(f"  ! Batch failed on {table}: {e}")
            for row in chunk:
                try:
                    sb.table(table).upsert(row, on_conflict=conflict_col).execute()
                except Exception as e2:
                    print(f"    skipped {row.get('id', row.get('wikidata_qid'))}: {e2}")


def is_valid_qid(qid):
    if not qid:
        return False
    if qid.startswith("http://") or qid.startswith("https://"):
        return False
    return qid.startswith("Q")


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
        # institutions.json uses "qid" as the key
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
    for chunk in tqdm(list(chunked(inst_rows, BATCH_SIZE)), desc="  Inserting"):
        upsert_batch("institutions", chunk)


# ============================================================
# STEP 2: Stream all NDJSON — collect artists + build artwork rows
# ============================================================
print("\n[2/3] Streaming artworks, collecting artists...")

ndjson_paths = (
    glob.glob("output/wikidata/artworks/*.ndjson")
    + glob.glob("output/wikidata/artworks.ndjson")
    + glob.glob("output/met/artworks.ndjson")
)
print(f"  Found {len(ndjson_paths)} ndjson files")

artists_seen: dict[str, dict] = {}
artwork_rows: list[dict] = []
skipped = 0

for path in ndjson_paths:
    with open(path) as f:
        for line in tqdm(f, desc=f"  {Path(path).name}", leave=False):
            line = line.strip()
            if not line:
                continue
            try:
                a = json.loads(line)
            except json.JSONDecodeError:
                skipped += 1
                continue

            if not a.get("id") or not a.get("title"):
                skipped += 1
                continue

            inst = a.get("institution") or {}
            inst_id = inst.get("id") or inst.get("wikidata_qid")
            if not is_valid_qid(inst_id):
                skipped += 1
                continue

            artist = a.get("artist") or {}
            artist_qid = artist.get("wikidata_qid")
            artist_name = artist.get("display_name") or artist.get("name")

            if is_valid_qid(artist_qid) and artist_qid not in artists_seen:
                if artist_name and not artist_name.startswith("http"):
                    artists_seen[artist_qid] = {
                        "wikidata_qid": artist_qid,
                        "name": artist_name,
                        "display_name": artist_name,
                        "nationality": artist.get("nationality"),
                        "student_of_qid": artist.get("student_of_qid")
                            if is_valid_qid(artist.get("student_of_qid")) else None,
                    }

            if not is_valid_qid(artist_qid):
                artist_qid = None

            date = a.get("date") or {}
            classification = a.get("classification") or {}
            images = a.get("images") or {}

            artwork_rows.append({
                "id": a["id"],
                "source": a.get("source", "unknown"),
                "source_id": a.get("source_id", ""),
                "title": a["title"][:500],
                "artist_qid": artist_qid if is_valid_qid(artist_qid) and artist_qid in artists_seen else None,
                "artist_name": artist_name if artist_name and not artist_name.startswith("http") else None,
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

print(f"  Collected {len(artwork_rows)} artworks, {len(artists_seen)} artists (skipped {skipped})")


# ============================================================
# STEP 3a: Insert artists — pass 1 (no teacher links, avoids self-FK violation)
# ============================================================
print(f"\n[3/3] Migrating {len(artists_seen)} artists...")

artists_no_teacher = [{**a, "student_of_qid": None} for a in artists_seen.values()]
for chunk in tqdm(list(chunked(artists_no_teacher, BATCH_SIZE)), desc="  Pass 1 (artists)"):
    upsert_batch("artists", chunk, conflict_col="wikidata_qid")


# ============================================================
# STEP 3b: Insert artworks (artists + institutions already exist)
# ============================================================
print(f"\n  Inserting {len(artwork_rows)} artworks...")
for chunk in tqdm(list(chunked(artwork_rows, BATCH_SIZE)), desc="  Artworks"):
    upsert_batch("artworks", chunk)


# ============================================================
# STEP 3c: Update artist teacher links (pass 2)
# ============================================================
artists_with_teacher = [
    a for a in artists_seen.values()
    if a.get("student_of_qid") and a["student_of_qid"] in artists_seen
]
print(f"\n  Pass 2: updating {len(artists_with_teacher)} teacher links...")
for chunk in tqdm(list(chunked(artists_with_teacher, BATCH_SIZE)), desc="  Teacher links"):
    upsert_batch("artists", chunk, conflict_col="wikidata_qid")


# ============================================================
# DONE
# ============================================================
print("\n✓ Migration complete.")
print("\nRun sanity checks in Supabase SQL Editor:")
print("  select count(*) from institutions;")
print("  select count(*) from artists;")
print("  select count(*) from artworks;")
print("  select count(*) from artworks where artist_qid is not null;")
