
import duckdb

con = duckdb.connect()

a = "gitskills/data/artifacts/*.parquet"
s = "gitskills/data/artifact_siblings/*.parquet"

# 1. Understand deduplication
print("\n1. DEDUPLICATION CHECK")
print(con.execute(f"""
SELECT
    dedup_primary,
    COUNT(*) AS rows,
    COUNT(DISTINCT file_sha) AS unique_file_shas,
    COUNT(DISTINCT repo_full_name) AS unique_repos
FROM read_parquet('{a}')
GROUP BY dedup_primary
ORDER BY dedup_primary
""").fetchdf().to_string(index=False))

# 2. Check whether file_sha identifies repeated contents
print("\n2. FILE SHA FREQUENCY")
print(con.execute(f"""
WITH hashes AS (
    SELECT file_sha, COUNT(*) AS occurrences
    FROM read_parquet('{a}')
    WHERE file_sha IS NOT NULL
    GROUP BY file_sha
)
SELECT
    COUNT(*) AS unique_hashes,
    SUM(occurrences) AS total_occurrences,
    COUNT(*) FILTER (WHERE occurrences = 1) AS single_occurrence_hashes,
    COUNT(*) FILTER (WHERE occurrences > 1) AS reused_hashes,
    MAX(occurrences) AS maximum_occurrences
FROM hashes
""").fetchdf().to_string(index=False))

# 3. Check whether primary artifacts have unique hashes
print("\n3. PRIMARY ARTIFACT HASH CHECK")
print(con.execute(f"""
SELECT
    COUNT(*) AS primary_rows,
    COUNT(DISTINCT file_sha) AS distinct_hashes,
    COUNT(*) - COUNT(DISTINCT file_sha) AS duplicate_hash_rows
FROM read_parquet('{a}')
WHERE dedup_primary = 1
""").fetchdf().to_string(index=False))

# 4. Correct extension extraction
print("\n4. SIBLING FILE EXTENSIONS")
print(con.execute(f"""
SELECT
    CASE
        WHEN contains(entry_name, '.')
        THEN lower(split_part(entry_name, '.', -1))
        ELSE '[no extension]'
    END AS extension,
    COUNT(*) AS total
FROM read_parquet('{s}')
WHERE entry_type = 'file'
GROUP BY extension
ORDER BY total DESC
LIMIT 35
""").fetchdf().to_string(index=False))

# 5. Script-like file counts among primary artifacts
print("\n5. SCRIPT-LIKE SIBLING FILES")
print(con.execute(f"""
SELECT
    COUNT(DISTINCT repo_full_name || '|' || artifact_path)
        AS skills_with_script_files,
    COUNT(*) AS script_file_entries
FROM read_parquet('{s}')
WHERE entry_type = 'file'
AND lower(entry_name) SIMILAR TO
    '%\\.(sh|bash|zsh|py|js|ts|rb|pl|php|ps1|bat|cmd|go|rs)%'
""").fetchdf().to_string(index=False))
