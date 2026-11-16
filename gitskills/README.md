---
license: cc-by-4.0
task_categories:
- other
tags:
- mining-software-repositories
- msr
- llm-agents
- agent-skills
- github
- software-engineering
pretty_name: GitSkills
dataset_info:
- config_name: artifacts
  features:
  - name: repo_full_name
    dtype: string
  - name: path
    dtype: string
  - name: filename
    dtype: string
  - name: location_class
    dtype: string
  - name: file_sha
    dtype: string
  - name: discovered_at
    dtype: string
  - name: content
    dtype: string
  - name: content_fetched
    dtype: int64
  - name: frontmatter_valid
    dtype: int64
  - name: name
    dtype: string
  - name: description
    dtype: string
  - name: body_chars
    dtype: int64
  - name: history_fetched
    dtype: int64
  - name: composition_fetched
    dtype: int64
  - name: dedup_primary
    dtype: int64
  - name: first_commit_at
    dtype: string
  - name: last_commit_at
    dtype: string
  - name: commit_count
    dtype: int64
  - name: sibling_count
    dtype: int64
  - name: sibling_bytes
    dtype: int64
  - name: has_scripts
    dtype: int64
  - name: has_references
    dtype: int64
  - name: content_sha_ok
    dtype: int64
  - name: composition_truncated
    dtype: int64
  - name: first_commit_author
    dtype: string
  - name: first_commit_author_type
    dtype: string
  - name: first_commit_message
    dtype: string
  - name: last_commit_author
    dtype: string
  - name: last_commit_author_type
    dtype: string
  - name: last_commit_message
    dtype: string
  splits:
  - name: train
    num_examples: 3797117
- config_name: artifact_siblings
  features:
  - name: repo_full_name
    dtype: string
  - name: artifact_path
    dtype: string
  - name: entry_name
    dtype: string
  - name: entry_type
    dtype: string
  - name: entry_size
    dtype: int64
  - name: entry_sha
    dtype: string
  - name: content
    dtype: string
  - name: content_fetched
    dtype: int64
  - name: skipped_reason
    dtype: string
  splits:
  - name: train
    num_examples: 7264865
- config_name: repos
  features:
  - name: full_name
    dtype: string
  - name: owner
    dtype: string
  - name: stars
    dtype: int64
  - name: forks
    dtype: int64
  - name: is_fork
    dtype: int64
  - name: language
    dtype: string
  - name: license
    dtype: string
  - name: description
    dtype: string
  - name: created_at
    dtype: string
  - name: pushed_at
    dtype: string
  - name: metadata_fetched
    dtype: int64
  splits:
  - name: train
    num_examples: 282200
- config_name: mining_runs
  features:
  - name: run_id
    dtype: int64
  - name: artifact_type
    dtype: string
  - name: query
    dtype: string
  - name: started_at
    dtype: string
  - name: finished_at
    dtype: string
  - name: discovered
    dtype: int64
  - name: note
    dtype: string
  splits:
  - name: train
    num_examples: 7
configs:
- config_name: artifacts
  data_files:
  - split: train
    path: data/artifacts/*.parquet
- config_name: artifact_siblings
  data_files:
  - split: train
    path: data/artifact_siblings/*.parquet
- config_name: repos
  data_files:
  - split: train
    path: data/repos/*.parquet
- config_name: mining_runs
  data_files:
  - split: train
    path: data/mining_runs/*.parquet
---

# GitSkills: A Dataset of Agent Skills on GitHub

[Paper (arXiv:2608.10906)](https://arxiv.org/abs/2608.10906) ·
[Sample repository](https://github.com/giuseppedestefanis/gitskills-sample) ·
[Zenodo DOI: 10.5281/zenodo.21875637](https://doi.org/10.5281/zenodo.21875637)

An agent skill is a folder containing a `SKILL.md` file with instructions for
a language-model agent, optionally accompanied by scripts and reference
files. The agent loads the skill when it judges that a task matches the
skill description. Anthropic introduced the format in October 2025 as an
open specification. Nine months later, skill files in the millions sit in
public GitHub repositories — yet no dataset recorded this population before
GitSkills.

**GitSkills** contains **3,797,117 `SKILL.md` files** collected from
**282,200 public repositories** (owned by 195,841 accounts) in **July 2026**.
Files are grouped by content hash into **1,877,981 distinct contents**; one
representative per group is enriched with full text, parsed front matter,
folder contents, repository metadata, and — for a large subset — the commit
history of the file. Every occurrence is retained with its own repository
and path, so both unique contents and their copies can be studied.

## Overview

```python
from datasets import load_dataset

artifacts = load_dataset("mvaccargiu/gitskills", "artifacts", split="train")
siblings  = load_dataset("mvaccargiu/gitskills", "artifact_siblings", split="train")
repos     = load_dataset("mvaccargiu/gitskills", "repos", split="train")
runs      = load_dataset("mvaccargiu/gitskills", "mining_runs", split="train")

print(artifacts[0])
```

## Intended Uses

The dataset supports empirical research on a software artefact that, unlike
most artefacts the SE research community mines, is written in natural
language and selected probabilistically at run time rather than verified by
a compiler:

- **Adoption and linguistic evolution** — how the format spreads across
  languages, project types, and monthly cohorts; how many skills are
  themselves agent-authored.
- **Development of a shared format** — vendor-neutral vs. tool-specific
  skill locations, and whether skill text targets one tool or the open spec.
- **Reuse without a package manager** — 50.5% of collected files are
  verbatim copies; the dataset supports studying concentration of reuse and
  clone-genealogy patterns.
- **Software metrics for natural-language instructions** — size, churn,
  age, clone coverage, and readability equivalents for skills, and whether
  description properties predict reuse and maintenance.
- **Maintenance and trust** — staleness relative to described tools, and
  whether modified copies introduce command execution or network access
  absent from the original (a supply-chain-attack analogue in a registry-
  free ecosystem).

## Quick Look

| Config | Rows | Content |
|---|---|---|
| `artifacts` | 3,797,117 | One row per discovered `SKILL.md` occurrence; full text, front matter, and commit history for representatives |
| `artifact_siblings` | 7,264,865 | Scripts and reference files stored alongside a representative skill |
| `repos` | 282,200 | Repository metadata: stars, language, fork status, license, dates |
| `mining_runs` | 7 | Provenance log of each collection run |

## Dataset Structure

### `artifacts`

One row per discovered file: repository, path, exact basename, location
class, and content hash. For the representative of each distinct content:
full text, parsed front matter (`name`, `description`), body size, and — for
458,548 files in standard locations plus a size-stratified sample of the
rest — the first and last commit of the file, with anonymised author
accounts and commit count.

### `artifact_siblings`

Files stored alongside a representative skill: path, entry type (`file` or
`dir`), size, and the text of files under a size cap. Whether a skill bundles
scripts or reference material is recorded per skill in `artifacts`
(`has_scripts`, `has_references`), not per individual sibling file.

### `repos`

Repository metadata: owner, star count, primary language, fork status,
license, creation date, and last-push date.

### `mining_runs`

Query, start/end timestamps, and result count for each collection run.

## Collection Methodology

Collection is read-only, against the GitHub REST, GraphQL, and code-search
APIs and the raw-content CDN, in three stages:

1. **Discovery** — search for files matching `SKILL.md`, partitioning the
   search space by file size to work around the code-search API's
   1,000-result cap (its reported `total_count` proved unreliable — roughly
   349,000 for the filename query, against over 3.8M files ultimately
   retrieved). Every filename match is retained, including files that only
   contain the term (e.g. `coding-skill.md`) and pre-format lowercase files.
2. **Deduplication** — files are grouped by content hash; one representative
   per group is selected for enrichment (preferring a file in
   `.claude/skills/`), while all copies remain in the dataset with their own
   repository, path, and location class.
3. **Enrichment** — for each representative: content, parsed front matter,
   folder contents, repository metadata, and — for standard locations plus a
   size-stratified sample of the rest — the commit history of the file.

The dataset covers **public repositories only** and should be read as a
lower bound on the population: GitHub code search indexes only default
branches, files under 384 KB, recently active repositories with fewer than
500,000 files, and forks only when they have more stars than the parent.

## Anonymisation

Commit author accounts are replaced by keyed one-way codes, identical for
the same account throughout the dataset, so authorship can be traced without
identifying anyone; the key used to generate the codes is not distributed.
Bot accounts keep their login. Email addresses (including GitHub noreply
addresses) and personal names in commit messages are redacted with a fixed
marker; AI assistant names in `Co-authored-by` trailers are kept.

## License

The dataset's collected metadata and aggregation are released under
**CC-BY-4.0**. The `content` fields reproduce file text from public GitHub
repositories and remain subject to the license of their origin repository;
consult `repos.license` (and the origin repository itself) before reusing
specific file contents.

## Citation

This dataset accompanies a paper accepted at the MSR 2027 Mining Challenge,
also available as a preprint at
[arXiv:2608.10906](https://arxiv.org/abs/2608.10906). If you use the
GitSkills dataset, please cite:

> G. Destefanis, D. Graziotin, M. Vaccargiu, and M. Ortu, "GitSkills: A
> Dataset of Agent Skills on GitHub," in *Proceedings of the 24th IEEE/ACM
> International Conference on Mining Software Repositories (MSR '27)*.
> IEEE, Piscataway, NJ, USA, 2027, 3 pp. To appear.

```bibtex
@inproceedings{gitskills2027,
  author    = {Destefanis, Giuseppe and Graziotin, Daniel and Vaccargiu, Matteo and Ortu, Marco},
  title     = {GitSkills: A Dataset of Agent Skills on GitHub},
  year      = {2027},
  isbn      = {},
  publisher = {IEEE},
  address   = {Piscataway, NJ, USA},
  url       = {https://arxiv.org/abs/2608.10906},
  doi       = {https://doi.org/10.48550/arXiv.2608.10906},
  booktitle = {Proceedings of the 24th IEEE/ACM International Conference on Mining Software Repositories},
  pages     = {To Appear},
  numpages  = {3},
  location  = {Dublin, Ireland},
  series    = {MSR '27}
}
```

## Contact

- Giuseppe Destefanis — University College London — g.destefanis@ucl.ac.uk
- Daniel Graziotin — University of Hohenheim — graziotin@uni-hohenheim.de
- Matteo Vaccargiu — University of Hohenheim — matteo.vaccargiu@uni-hohenheim.de
- Marco Ortu — University of Cagliari — marco.ortu@unica.it
