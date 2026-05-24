# SWEN90004 Assignment 2 Code

This repository contains a standard-library-only Python implementation of the
NetLogo Segregation model and the proposed income/rent extension, together with
matching NetLogo reference runs used for replication validation.

## Requirements

- Python 3.14, or a recent Python 3 version for development.
- No third-party packages are required.
- No IDE, build tool, or package manager is required.
- NetLogo 7.0.4 headless for regenerating reference data (Track B only).

## Repository layout

```
segregation/         Python model package
experiments/         Batch runners, summary, plotting, snapshot utilities
netlogo/             NetLogo Segregation.nlogox + BehaviorSpace XML configs
results/
├── python/          All Python-side outputs (mirror of netlogo/ where applicable)
│   ├── full/        30-rep parameter sweep CSVs + summaries
│   ├── smoke/       Fast 1-rep verification CSVs
│   ├── snapshots/   Per-config SVG snapshots (snap_t####.svg / snap_final_t####.svg)
│   └── trajectories/ Per-tick CSVs for a few representative configs
└── netlogo/         All NetLogo-side outputs (mirror of python/ where applicable)
    ├── full/        30-rep BehaviorSpace sweep, cleaned + summary
    ├── snapshots/   Per-config SVG + PNG snapshots (snap_final.svg)
    └── raw/         BehaviorSpace table exports (pre-cleaning)
```

## Run One Simulation

Baseline replication run:

```bash
python3 main.py \
  --density 80 \
  --similar-wanted 30 \
  --seed 1 \
  --output results/python/baseline.csv
```

Extension run:

```bash
python3 main.py \
  --mode extension \
  --density 80 \
  --similar-wanted 30 \
  --income-gap 0.5 \
  --seed 2 \
  --output results/python/extension.csv
```

Useful options:

- `--max-ticks`: maximum simulation ticks before stopping.
- `--final-only`: write only the final row instead of one row per tick.
- `--size`: world width and height. The NetLogo-compatible default is `51`.
- `--max-relocation-attempts`: bounded random-walk attempts per unhappy agent.
- `--stall-limit`: extension stop condition after repeated no-movement ticks.
- `--disable-affordability`: keep extension rents/incomes but ignore affordability.

## Run Experiments

Replication sweep from the proposal:

```bash
python3 experiments/runner.py \
  --experiment replication \
  --repetitions 30 \
  --out-dir results/python/full
```

Extension treatments from the proposal:

```bash
python3 experiments/runner.py \
  --experiment extension \
  --repetitions 30 \
  --out-dir results/python/full
```

For a quick smoke test:

```bash
python3 experiments/runner.py \
  --experiment all \
  --repetitions 1 \
  --max-ticks 20 \
  --final-only \
  --out-dir results/python/smoke
```

## Summaries and Figures

Create a summary table from an experiment CSV (Python side):

```bash
python3 experiments/summarize.py \
  results/python/full/replication.csv \
  --output results/python/full/replication_summary.csv
```

Create a simple SVG line chart from a summary CSV:

```bash
python3 experiments/plotting.py \
  results/python/full/replication_summary.csv \
  --x similar_wanted \
  --y percent_similar_mean \
  --group density \
  --output results/python/replication_percent_similar.svg
```

Render Python spatial snapshots:

```bash
python3 experiments/snapshot.py \
  --mode baseline --density 80 --similar-wanted 30 --seed 1 \
  --snap-at 0,3,7,15 --also-final \
  --output-dir results/python/snapshots/baseline_d80_s30
```

## NetLogo Reference Data (Track B)

Track B uses NetLogo 7 headless BehaviorSpace to generate reference data from
the original model in `netlogo/Segregation.nlogox`.

Full reference sweep:

```bash
"/path/to/NetLogo 7.0.4/netlogo-headless.sh" \
  --model netlogo/Segregation.nlogox \
  --setup-file netlogo/segregation_reference.xml \
  --experiment segregation-reference \
  --table results/netlogo/raw/reference_table.csv \
  --threads 4
```

Convert the raw BehaviorSpace table to a normal CSV:

```bash
python3 experiments/convert_netlogo_table.py \
  results/netlogo/raw/reference_table.csv \
  --output results/netlogo/full/replication.csv
```

Summarise the NetLogo reference runs:

```bash
python3 experiments/summarize_netlogo.py \
  results/netlogo/full/replication.csv \
  --output results/netlogo/full/replication_summary.csv
```

Generate NetLogo-derived spatial snapshots:

```bash
"/path/to/NetLogo 7.0.4/netlogo-headless.sh" \
  --model netlogo/Segregation.nlogox \
  --setup-file netlogo/segregation_snapshot_data.xml \
  --experiment segregation-snapshot-data \
  --table results/netlogo/raw/snapshot_data_table.csv \
  --threads 1

python3 experiments/render_netlogo_snapshots.py \
  results/netlogo/raw/snapshot_data_table.csv \
  --out-dir results/netlogo/snapshots
```

This emits one `snap_final.svg` under `results/netlogo/snapshots/baseline_d<D>_s<S>/`
per cell, mirroring the Python snapshot layout.

Already generated Track B artifacts are kept under `results/netlogo/`:

- `raw/reference_table.csv`: raw BehaviorSpace output.
- `raw/snapshot_data_table.csv`: final turtle coordinates for representative runs.
- `full/replication.csv`: one clean row per NetLogo run.
- `full/replication_summary.csv`: mean and 95% CI by parameter cell.
- `snapshots/baseline_d<D>_s<S>/snap_final.svg`: NetLogo-derived final-state SVGs.
- `snapshots/baseline_d<D>_s<S>/png/snap_final.png`: PNG versions for report insertion.

## Model Notes

The baseline model uses a 51 x 51 wrapped grid. Initial patches are populated
independently according to `density`, and each agent is assigned to `blue` or
`orange` with equal probability. Each tick, unhappy agents are processed in a
random order and use a NetLogo-style continuous random walk until they find a
valid patch or exceed the configured attempt bound.

The key baseline metrics are:

- `percent_similar`: neighbour-count-weighted same-group contact percentage.
- `percent_unhappy`: percentage of agents currently unhappy.
- `tick`: convergence tick or capped final tick.

The extension adds an exponential rent surface and group-conditional income.
When affordability is enabled, an agent is unhappy when either the neighbourhood
preference fails or the current patch rent exceeds income. Extension movement
is then restricted to vacant and affordable patches. T1 in `runner.py` disables
affordability so that it remains a true preference-only comparison. Additional
metrics include:

- `stuck_unhappy_fraction`
- `isolation_blue` and `isolation_orange`
- `dissimilarity`
- `mean_rent_blue` and `mean_rent_orange`
