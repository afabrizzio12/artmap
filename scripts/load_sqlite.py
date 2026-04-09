#!/usr/bin/env python3
"""
ArtMap — load enriched artworks into SQLite
Reads artworks_enriched.ndjson and writes a queryable SQLite database.

Usage:
    python load_sqlite.py
    python load_sqlite.py --input output/met/artworks_enriched.ndjson
    python load_sqlite.py --db output/artmap.db

The resulting DB has one table: artworks
Useful queries are printed at the end as examples.
"""

import argparse
import json
import logging
import sqlite3
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).parent.parent / "output"
DEFAULT_INPUT = OUTPUT_DIR / "met" / "artworks_enriched.ndjson"
DEFAULT_DB = OUTPUT_DIR / "artmap.db"

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS artworks (
    id                  TEXT PRIMARY KEY,
    source              TEXT,
    source_id           TEXT,
    source_url          TEXT,

    title               TEXT NOT NULL,
    artist_name         TEXT,
    artist_nationality  TEXT,
    artist_birth_year   INTEGER,
    artist_death_year   INTEGER,
    artist_wikidata_url TEXT,

    date_display        TEXT,
    year_start          INTEGER,
    year_end            INTEGER,

    department          TEXT,
    type                TEXT,
    medium              TEXT,
    culture             TEXT,
    period              TEXT,

    institution_id      TEXT,
    institution_name    TEXT,
    institution_city    TEXT,
    institution_country TEXT,
    institution_lat     REAL,
    institution_lng     REAL,
    gallery_number      TEXT,
    is_on_view          INTEGER,   -- 0/1

    geo_origin_country  TEXT,
    geo_origin_city     TEXT,
    geo_origin_lat      REAL,
    geo_origin_lng      REAL,
    geo_source          TEXT,      -- 'wikidata_P276', 'wikidata_culture_geocode', etc.

    image_primary       TEXT,
    image_small         TEXT,

    is_public_domain    INTEGER,
    license             TEXT,
    wikidata_url        TEXT,
    wikidata_enriched   INTEGER,

    ingested_at         TEXT,
    raw_json            TEXT       -- full record for fields not in columns
);

CREATE INDEX IF NOT EXISTS idx_artist      ON artworks(artist_name);
CREATE INDEX IF NOT EXISTS idx_period      ON artworks(period);
CREATE INDEX IF NOT EXISTS idx_institution ON artworks(institution_id);
CREATE INDEX IF NOT EXISTS idx_year        ON artworks(year_start, year_end);
CREATE INDEX IF NOT EXISTS idx_geo_inst    ON artworks(institution_lat, institution_lng);
CREATE INDEX IF NOT EXISTS idx_geo_origin  ON artworks(geo_origin_lat, geo_origin_lng);
CREATE INDEX IF NOT EXISTS idx_on_view     ON artworks(is_on_view);
"""

INSERT = """
INSERT OR REPLACE INTO artworks VALUES (
    :id, :source, :source_id, :source_url,
    :title, :artist_name, :artist_nationality, :artist_birth_year, :artist_death_year, :artist_wikidata_url,
    :date_display, :year_start, :year_end,
    :department, :type, :medium, :culture, :period,
    :institution_id, :institution_name, :institution_city, :institution_country,
    :institution_lat, :institution_lng, :gallery_number, :is_on_view,
    :geo_origin_country, :geo_origin_city, :geo_origin_lat, :geo_origin_lng, :geo_source,
    :image_primary, :image_small,
    :is_public_domain, :license, :wikidata_url, :wikidata_enriched,
    :ingested_at, :raw_json
)
"""


def flatten(artwork: dict) -> dict:
    """Flatten nested artwork dict to a SQL-ready row."""
    artist = artwork.get("artist") or {}
    date = artwork.get("date") or {}
    cls = artwork.get("classification") or {}
    inst = artwork.get("institution") or {}
    geo = artwork.get("geo_origin") or {}
    images = artwork.get("images") or {}

    # geo_source: prefer institution (display location), fall back to geo_origin
    geo_source = inst.get("geo_source") or geo.get("geo_source")

    return {
        "id": artwork.get("id"),
        "source": artwork.get("source"),
        "source_id": str(artwork.get("source_id", "")),
        "source_url": artwork.get("source_url"),
        "title": artwork.get("title"),
        "artist_name": artist.get("display_name") or artist.get("name"),
        "artist_nationality": artist.get("nationality"),
        "artist_birth_year": artist.get("birth_year"),
        "artist_death_year": artist.get("death_year"),
        "artist_wikidata_url": artist.get("wikidata_url"),
        "date_display": date.get("display"),
        "year_start": date.get("year_start"),
        "year_end": date.get("year_end"),
        "department": cls.get("department"),
        "type": cls.get("type"),
        "medium": cls.get("medium"),
        "culture": cls.get("culture"),
        "period": cls.get("period"),
        "institution_id": inst.get("id"),
        "institution_name": inst.get("name"),
        "institution_city": inst.get("city"),
        "institution_country": inst.get("country"),
        "institution_lat": inst.get("lat"),
        "institution_lng": inst.get("lng"),
        "gallery_number": inst.get("gallery_number"),
        "is_on_view": int(bool(inst.get("is_on_view"))),
        "geo_origin_country": geo.get("country"),
        "geo_origin_city": geo.get("city"),
        "geo_origin_lat": geo.get("lat"),
        "geo_origin_lng": geo.get("lng"),
        "geo_source": geo_source,
        "image_primary": images.get("primary"),
        "image_small": images.get("primary_small"),
        "is_public_domain": int(bool(artwork.get("is_public_domain"))),
        "license": artwork.get("license"),
        "wikidata_url": artwork.get("wikidata_url"),
        "wikidata_enriched": int(bool(artwork.get("wikidata_enriched"))),
        "ingested_at": artwork.get("ingested_at"),
        "raw_json": json.dumps(artwork),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--db", default=str(DEFAULT_DB))
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        log.error(f"Input not found: {input_path}. Run enrich_wikidata.py first.")
        sys.exit(1)

    db_path = Path(args.db)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    con = sqlite3.connect(db_path)
    con.executescript(CREATE_TABLE)

    batch = []
    total = 0
    BATCH_SIZE = 500

    with open(input_path) as f:
        for line in f:
            artwork = json.loads(line.strip())
            batch.append(flatten(artwork))
            total += 1

            if len(batch) >= BATCH_SIZE:
                con.executemany(INSERT, batch)
                con.commit()
                batch = []
                log.info(f"Loaded {total} rows...")

    if batch:
        con.executemany(INSERT, batch)
        con.commit()

    # Quick summary
    count = con.execute("SELECT COUNT(*) FROM artworks").fetchone()[0]
    with_coords = con.execute("SELECT COUNT(*) FROM artworks WHERE institution_lat IS NOT NULL").fetchone()[0]
    on_view = con.execute("SELECT COUNT(*) FROM artworks WHERE is_on_view = 1").fetchone()[0]
    con.close()

    log.info(f"\n{'='*50}")
    log.info(f"DB written to   : {db_path}")
    log.info(f"Total artworks  : {count}")
    log.info(f"With coordinates: {with_coords}")
    log.info(f"Currently on view: {on_view}")
    log.info(f"\nExample queries:")
    log.info(f"  sqlite3 {db_path} \"SELECT title, artist_name, institution_city FROM artworks WHERE period = 'Baroque' LIMIT 10\"")
    log.info(f"  sqlite3 {db_path} \"SELECT institution_name, COUNT(*) as n FROM artworks GROUP BY institution_name ORDER BY n DESC LIMIT 10\"")
    log.info(f"  sqlite3 {db_path} \"SELECT * FROM artworks WHERE is_on_view = 1 AND institution_lat IS NOT NULL LIMIT 5\"")


if __name__ == "__main__":
    main()
