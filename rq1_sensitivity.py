
import glob
import math
import duckdb

# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

ARTIFACTS_DIR = "gitskills/data/artifacts"
SIBLINGS_DIR = "gitskills/data/artifact_siblings"

# Original, broader definition
BROAD_EXTENSIONS = {
    "py", "ts", "sh", "js", "go", "tsx", "mjs",
    "rs", "jsx", "ps1", "php", "cjs", "rb",
    "bat", "cmd", "bash", "zsh", "pl"
}

# Narrower definition: commonly used runnable scripts
NARROW_EXTENSIONS = {
    "py", "sh", "bash", "zsh", "js", "mjs",
    "cjs", "ps1", "bat", "cmd", "rb", "pl"
}


def parquet_list(directory):
    files = glob.glob(f"{directory}/**/*.parquet", recursive=True)
    if not files:
        raise FileNotFoundError(f"No Parquet files found in {directory}")
    return "[" + ", ".join(
        "'" + f.replace("\\", "/").replace("'", "''") + "'"
        for f in files
    ) + "]"


def calculate_statistics(rows, flag):
    groups = {
        "Script-bearing": [],
        "No script-like files observed": [],
        "Unknown": []
    }

    for row in rows:
        repo_count = row[1]
        has_siblings = row[2]
        has_script = row[flag]

        if not has_siblings:
            group = "Unknown"
        elif has_script:
            group = "Script-bearing"
        else:
            group = "No script-like files observed"

        groups[group].append(repo_count)

    results = {}

    for group, counts in groups.items():
        total = len(counts)
        reused = sum(x > 1 for x in counts)

        results[group] = {
            "skills": total,
            "reused": reused,
            "reuse_rate": reused / total * 100 if total else 0,
            "mean_repos": sum(counts) / total if total else 0,
            "median_repos": sorted(counts)[total // 2] if total else 0,
            "p90_repos": (
                sorted(counts)[math.ceil(0.9 * total) - 1]
                if total else 0
            ),
            "max_repos": max(counts) if total else 0
        }

    # Pearson chi-square test comparing the two known groups
    script = results["Script-bearing"]
    no_script = results["No script-like files observed"]

    a = script["reused"]
    b = script["skills"] - a
    c = no_script["reused"]
    d = no_script["skills"] - c

    n = a + b + c + d
    denominator = (a + b) * (c + d) * (a + c) * (b + d)

    if denominator:
        chi_square = (
            n * (a * d - b * c) ** 2 / denominator
        )
        p_value = math.erfc(math.sqrt(chi_square / 2))
        cramers_v = math.sqrt(chi_square / n)
        odds_ratio = (a * d) / (b * c) if b * c else float("inf")
    else:
        chi_square = p_value = cramers_v = odds_ratio = float("nan")

    return results, chi_square, p_value, cramers_v, odds_ratio


def print_results(title, results, chi, p, v, odds):
    print("\n" + "=" * 75)
    print(title)
    print("=" * 75)

    print(
        f"{'Group':35} {'Skills':>12} {'Reused':>12} "
        f"{'Reuse rate':>12}"
    )

    for group, values in results.items():
        print(
            f"{group:35} {values['skills']:12,} "
            f"{values['reused']:12,} {values['reuse_rate']:11.2f}%"
        )

    print("\nAdditional reuse statistics:")

    for group in ("Script-bearing", "No script-like files observed"):
        x = results[group]
        print(f"\n{group}")
        print(f"  Mean repositories:   {x['mean_repos']:.3f}")
        print(f"  Median repositories: {x['median_repos']}")
        print(f"  90th percentile:     {x['p90_repos']}")
        print(f"  Maximum:             {x['max_repos']}")

    print("\nStatistical comparison:")
    print(f"  Chi-square: {chi:.4f}")
    print(f"  p-value:    {p:.6e}")
    print(f"  Cramer's V: {v:.5f}")
    print(f"  Odds ratio (script vs. no-script): {odds:.4f}")


def main():
    print("Locating Parquet files...")

    artifacts = parquet_list(ARTIFACTS_DIR)
    siblings = parquet_list(SIBLINGS_DIR)

    con = duckdb.connect()
    con.execute("PRAGMA threads=4")
    con.execute("PRAGMA enable_progress_bar")

    print("Preparing artifact and sibling data...")

    query = f"""
    WITH artifacts AS (
        SELECT
            repo_full_name,
            path,
            file_sha,
            dedup_primary
        FROM read_parquet({artifacts}, union_by_name=true)
    ),

    reuse AS (
        SELECT
            file_sha,
            COUNT(DISTINCT repo_full_name) AS repo_count
        FROM read_parquet({artifacts}, union_by_name=true)
        GROUP BY file_sha
    ),

    sibling_summary AS (
        SELECT
            repo_full_name,
            artifact_path,
            COUNT(*) AS sibling_rows,

            MAX(CASE
                WHEN entry_type = 'file'
                 AND LOWER(REGEXP_EXTRACT(
                     entry_name, '[.]([^.]+)$', 1
                 )) IN ({", ".join(repr(x) for x in BROAD_EXTENSIONS)})
                THEN 1 ELSE 0
            END) AS broad_script,

            MAX(CASE
                WHEN entry_type = 'file'
                 AND LOWER(REGEXP_EXTRACT(
                     entry_name, '[.]([^.]+)$', 1
                 )) IN ({", ".join(repr(x) for x in NARROW_EXTENSIONS)})
                THEN 1 ELSE 0
            END) AS narrow_script

        FROM read_parquet({siblings}, union_by_name=true)
        GROUP BY repo_full_name, artifact_path
    )

    SELECT
        a.file_sha,
        r.repo_count,
        COALESCE(s.sibling_rows, 0) > 0 AS has_siblings,
        COALESCE(s.broad_script, 0) AS broad_script,
        COALESCE(s.narrow_script, 0) AS narrow_script

    FROM artifacts a
    JOIN reuse r ON a.file_sha = r.file_sha
    LEFT JOIN sibling_summary s
        ON a.repo_full_name = s.repo_full_name
       AND a.path = s.artifact_path
    WHERE a.dedup_primary = 1
    """

    print("Running analysis. This may take a few minutes...")

    rows = con.execute(query).fetchall()

    print(f"\nLoaded {len(rows):,} unique primary skills.")

    broad, chi, p, v, odds = calculate_statistics(rows, 3)
    print_results("ORIGINAL BROAD DEFINITION", broad, chi, p, v, odds)

    narrow, chi, p, v, odds = calculate_statistics(rows, 4)
    print_results("NARROWER SCRIPT DEFINITION", narrow, chi, p, v, odds)

    print("\n" + "=" * 75)
    print("SENSITIVITY COMPARISON")
    print("=" * 75)

    for group in ("Script-bearing", "No script-like files observed"):
        broad_rate = broad[group]["reuse_rate"]
        narrow_rate = narrow[group]["reuse_rate"]
        print(
            f"{group}: broad={broad_rate:.2f}%, "
            f"narrow={narrow_rate:.2f}%"
        )

    print("\nAnalysis complete.")
    con.close()


if __name__ == "__main__":
    main()
