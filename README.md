<div align="center">

# 📊 csv-profiler

**Point it at any CSV. Know everything inside it in one command.**

[![CI](https://github.com/v01dst/csv-profiler/actions/workflows/ci.yml/badge.svg)](https://github.com/v01dst/csv-profiler/actions/workflows/ci.yml)
![License](https://img.shields.io/badge/license-MIT-8A2BE2)
![Python](https://img.shields.io/badge/python-3.14-3776AB?logo=python&logoColor=white)
![Deps](https://img.shields.io/badge/dependencies-stdlib%20only-00c853)
![Tests](https://img.shields.io/badge/tests-13%20passing-brightgreen)

`types` · `nulls` · `uniques` · `numeric stats` · `top values` · `tsv too`
</div>

---

## ✨ Features

- **🧠 Type inference** — integer, float, boolean, date, string per column
- **📈 Numeric stats** — min / max / mean / stddev / sum
- **🕳️ Data quality** — nulls, empty strings, unique counts, distinct ratio
- **🏆 Top values** — ranked frequency per column
- **📄 TSV support** — `--tsv` or any delimiter via `-d`
- **🤖 Machine-readable** — `--json` for pipelines
- **🪶 Pure stdlib** — zero pip dependencies

## 🚀 Quick Start

```bash
git clone https://github.com/v01dst/csv-profiler
cd csv-profiler
python3 -m csv_profiler data.csv
```

Or with Docker:

```bash
docker build -t csv-profiler .
docker run --rm -v "$PWD:/data" csv-profiler /data/data.csv
```

## 📖 Usage

```
csv-profiler [--json] [--tsv | -d SEP] [--top N] <file.csv>
```

### Sample output

```
file: demo.csv
rows: 4  columns: 4

[name]    type=string  nulls=0  empty=0  unique=4 (100.0%)
  length: min=3  max=3
[age]     type=integer nulls=0  empty=1  unique=3 (100.0%)
  min=24.0  max=45.0  mean=35.0  stddev=8.6023  sum=105.0
[joined]  type=date    nulls=0  empty=0  unique=4 (100.0%)
[score]   type=float   nulls=0  empty=0  unique=3 (75.0%)
  min=88.0  max=93.25  mean=90.1875  stddev=2.2733
```

### JSON mode

```bash
python3 -m csv_profiler data.csv --json | jq '.profiles[0]'
```

## 🧱 Tech Stack

| Layer     | Tech                        |
|-----------|-----------------------------|
| Runtime   | Python ≥ 3.10 (stdlib only) |
| Testing   | unittest                    |
| Packaging | Docker                      |
| CI        | GitHub Actions              |

---

<div align="center">

Built with ⚡ by **v01dst**

[![GitHub](https://img.shields.io/badge/github-v01dst-181717?logo=github)](https://github.com/v01dst)
[![Discord](https://img.shields.io/badge/discord-9p.1-5865F2?logo=discord&logoColor=white)](https://discord.com/users/9p.1)

</div>
