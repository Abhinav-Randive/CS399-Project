
import duckdb

con = duckdb.connect()

a = "gitskills/data/artifacts/*.parquet"
s = "gitskills/data/artifact_siblings/*.parquet"

# Extensions treated as script-like for this initial analysis
script_pattern = r'\.(sh|bash|zsh|py|js|mjs|cjs|ts|tsx|jsx|rb|pl|php|ps1|bat|cmd|go|rs)$'

# 1. Count script-like files and distinct skills containing them
print("\n1. SCRIPT-LIKE FILES")
print(con.execute(f"""
SELECT
    COUNT(*) AS script_file_entries,
    COUNT(DISTINCT repo_full_name || '|' || artifact_path)
        AS skills_with_script_files
FROM read_parquet('{s}')
WHERE entry_type = 'file'
AND regexp_matches(lower(entry_name), '{script_pattern}')
""").fetchdf().to_string(index=False))

# 2. Script-like files by extension
print("\n2. SCRIPT FILE EXTENSIONS")
print(con.execute(f"""
SELECT
    lower(split_part(entry_name, '.', -1)) AS extension,
    COUNT(*) AS total_files
FROM read_parquet('{s}')
WHERE entry_type = 'file'
AND regexp_matches(lower(entry_name), '{script_pattern}')
GROUP BY extension
ORDER BY total_files DESC
""").fetchdf().to_string(index=False))

# 3. Primary artifact composition coverage
print("\n3. PRIMARY ARTIFACT COMPOSITION COVERAGE")
print(con.execute(f"""
WITH sibling_keys AS (
    SELECT DISTINCT repo_full_name, artifact_path
    FROM read_parquet('{s}')
)
SELECT
    COUNT(*) AS primary_artifacts,
    COUNT(sk.artifact_path) AS with_composition_records,
    COUNT(*) - COUNT(sk.artifact_path) AS unknown_composition,
    ROUND(
        100.0 * COUNT(sk.artifact_path) / COUNT(*), 2
    ) AS observed_coverage_pct
FROM read_parquet('{a}') art
LEFT JOIN sibling_keys sk
    ON art.repo_full_name = sk.repo_full_name
    AND art.path = sk.artifact_path
WHERE art.dedup_primary = 1
""").fetchdf().to_string(index=False))

# 4. Reuse distribution by distinct repositories
print("\n4. REUSE DISTRIBUTION")
print(con.execute(f"""
WITH reuse AS (
    SELECT
        file_sha,
        COUNT(DISTINCT repo_full_name) AS repo_count
    FROM read_parquet('{a}')
    WHERE file_sha IS NOT NULL
    GROUP BY file_sha
)
SELECT
    CASE
        WHEN repo_count = 1 THEN '1 repository'
        WHEN repo_count BETWEEN 2 AND 5 THEN '2-5 repositories'
        WHEN repo_count BETWEEN 6 AND 10 THEN '6-10 repositories'
        WHEN repo_count BETWEEN 11 AND 50 THEN '11-50 repositories'
        WHEN repo_count BETWEEN 51 AND 100 THEN '51-100 repositories'
        ELSE 'More than 100 repositories'
    END AS reuse_group,
    COUNT(*) AS distinct_skills
FROM reuse
GROUP BY reuse_group
ORDER BY MIN(repo_count)
""").fetchdf().to_string(index=False))
