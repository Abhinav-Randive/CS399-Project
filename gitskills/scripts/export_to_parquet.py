#!/usr/bin/env python3
"""Stream the GitSkills SQLite tables into sharded Parquet files for Hugging Face."""
import os
import sqlite3
import sys
import time

import pyarrow as pa
import pyarrow.parquet as pq

DB_PATH = "/Users/matteovaccargiu/Downloads/agent_skills_release.db"
OUT_ROOT = "/Users/matteovaccargiu/Downloads/gitskills_hf/data"

# (sqlite column, pyarrow type)
TABLES = {
    "artifacts": {
        "shard_bytes": 500_000_000,
        "columns": [
            ("repo_full_name", pa.string()),
            ("path", pa.string()),
            ("filename", pa.string()),
            ("location_class", pa.string()),
            ("file_sha", pa.string()),
            ("discovered_at", pa.string()),
            ("content", pa.string()),
            ("content_fetched", pa.int64()),
            ("frontmatter_valid", pa.int64()),
            ("name", pa.string()),
            ("description", pa.string()),
            ("body_chars", pa.int64()),
            ("history_fetched", pa.int64()),
            ("composition_fetched", pa.int64()),
            ("dedup_primary", pa.int64()),
            ("first_commit_at", pa.string()),
            ("last_commit_at", pa.string()),
            ("commit_count", pa.int64()),
            ("sibling_count", pa.int64()),
            ("sibling_bytes", pa.int64()),
            ("has_scripts", pa.int64()),
            ("has_references", pa.int64()),
            ("content_sha_ok", pa.int64()),
            ("composition_truncated", pa.int64()),
            ("first_commit_author", pa.string()),
            ("first_commit_author_type", pa.string()),
            ("first_commit_message", pa.string()),
            ("last_commit_author", pa.string()),
            ("last_commit_author_type", pa.string()),
            ("last_commit_message", pa.string()),
        ],
    },
    "artifact_siblings": {
        "shard_bytes": 500_000_000,
        "columns": [
            ("repo_full_name", pa.string()),
            ("artifact_path", pa.string()),
            ("entry_name", pa.string()),
            ("entry_type", pa.string()),
            ("entry_size", pa.int64()),
            ("entry_sha", pa.string()),
            ("content", pa.string()),
            ("content_fetched", pa.int64()),
            ("skipped_reason", pa.string()),
        ],
    },
    "repos": {
        "shard_bytes": 2_000_000_000,
        "columns": [
            ("full_name", pa.string()),
            ("owner", pa.string()),
            ("stars", pa.int64()),
            ("forks", pa.int64()),
            ("is_fork", pa.int64()),
            ("language", pa.string()),
            ("license", pa.string()),
            ("description", pa.string()),
            ("created_at", pa.string()),
            ("pushed_at", pa.string()),
            ("metadata_fetched", pa.int64()),
        ],
    },
    "mining_runs": {
        "shard_bytes": 2_000_000_000,
        "columns": [
            ("run_id", pa.int64()),
            ("artifact_type", pa.string()),
            ("query", pa.string()),
            ("started_at", pa.string()),
            ("finished_at", pa.string()),
            ("discovered", pa.int64()),
            ("note", pa.string()),
        ],
    },
}


def export_table(conn, table_name, spec):
    col_names = [c for c, _ in spec["columns"]]
    schema = pa.schema(spec["columns"])
    out_dir = os.path.join(OUT_ROOT, table_name)
    os.makedirs(out_dir, exist_ok=True)

    cur = conn.cursor()
    cur.execute(f"SELECT {', '.join(col_names)} FROM {table_name}")

    buffers = {c: [] for c in col_names}
    buffered_bytes = 0
    shard_idx = 0
    row_count = 0
    t0 = time.time()

    def flush():
        nonlocal buffers, buffered_bytes, shard_idx
        if not buffers[col_names[0]]:
            return
        table = pa.table(buffers, schema=schema)
        out_path = os.path.join(out_dir, f"part-{shard_idx:05d}.parquet")
        pq.write_table(table, out_path, compression="zstd")
        size_mb = os.path.getsize(out_path) / 1e6
        print(
            f"  [{table_name}] wrote {out_path} "
            f"({len(buffers[col_names[0]])} rows, {size_mb:.1f} MB on disk)",
            flush=True,
        )
        shard_idx += 1
        buffers = {c: [] for c in col_names}
        buffered_bytes = 0

    for row in cur:
        for c, v in zip(col_names, row):
            buffers[c].append(v)
            if isinstance(v, str):
                buffered_bytes += len(v)
        row_count += 1
        if buffered_bytes >= spec["shard_bytes"]:
            flush()
        if row_count % 500_000 == 0:
            elapsed = time.time() - t0
            print(f"  [{table_name}] {row_count} rows in {elapsed:.0f}s", flush=True)

    flush()
    print(f"[{table_name}] done: {row_count} rows, {shard_idx} shard(s), "
          f"{time.time()-t0:.0f}s total", flush=True)


def main():
    only = sys.argv[1:] or list(TABLES.keys())
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    for name in only:
        print(f"=== exporting {name} ===", flush=True)
        export_table(conn, name, TABLES[name])
    conn.close()


if __name__ == "__main__":
    main()
