
import duckdb

con = duckdb.connect()

a = "gitskills/data/artifacts/*.parquet"
s = "gitskills/data/artifact_siblings/*.parquet"

script_pattern = (
    r'\.(sh|bash|zsh|py|js|mjs|cjs|ts|tsx|jsx|rb|pl|php|'
    r'ps1|bat|cmd|go|rs)$'
)

query = f"""
WITH sibling_summary AS (
    SELECT
        repo_full_name,
        artifact_path,
        COUNT(*) AS sibling_entries,
        COUNT(*) FILTER (
            WHERE entry_type = 'file'
            AND regexp_matches(lower(entry_name), '{script_pattern}')
        ) AS script_files
    FROM read_parquet('{s}')
    GROUP BY repo_full_name, artifact_path
),

reuse AS (
    SELECT
        file_sha,
        COUNT(DISTINCT repo_full_name) AS repo_count
    FROM read_parquet('{a}')
    WHERE file_sha IS NOT NULL
    GROUP BY file_sha
),

primary_skills AS (
    SELECT
        art.file_sha,
        art.repo_full_name,
        art.path,
        reuse.repo_count,
        CASE
            WHEN ss.repo_full_name IS NULL THEN 'Unknown'
            WHEN ss.script_files > 0 THEN 'Script-bearing'
            ELSE 'No script-like files observed'
        END AS script_group
    FROM read_parquet('{a}') art
    JOIN reuse ON art.file_sha = reuse.file_sha
    LEFT JOIN sibling_summary ss
        ON art.repo_full_name = ss.repo_full_name
        AND art.path = ss.artifact_path
    WHERE art.dedup_primary = 1
)

SELECT
    script_group,
    COUNT(*) AS unique_skills,
    COUNT(*) FILTER (WHERE repo_count > 1) AS reused_skills,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE repo_count > 1) / COUNT(*), 2
    ) AS reuse_rate_pct,
    ROUND(AVG(repo_count), 2) AS mean_repositories,
    MEDIAN(repo_count) AS median_repositories,
    QUANTILE_CONT(repo_count, 0.90) AS p90_repositories,
    MAX(repo_count) AS maximum_repositories
FROM primary_skills
GROUP BY script_group
ORDER BY script_group
"""

print("\nRQ1: REUSE COMPARISON BY SCRIPT-BUNDLING STATUS")
print(con.execute(query).fetchdf().to_string(index=False))
