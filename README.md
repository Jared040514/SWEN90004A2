# SWEN90004 Assignment 2 Code

This repository contains a standard-library-only Python implementation of the
NetLogo Segregation model and the proposed income/rent extension.

## Requirements

- Python 3.14, or a recent Python 3 version for development.
- No third-party packages are required.
- No IDE, build tool, or package manager is required.

## Run One Simulation

Baseline replication run:

```bash
python3 main.py \
  --density 80 \
  --similar-wanted 30 \
  --seed 1 \
  --output results/baseline.csv
```

Extension run:

```bash
python3 main.py \
  --mode extension \
  --density 80 \
  --similar-wanted 30 \
  --income-gap 0.5 \
  --seed 2 \
  --output results/extension.csv
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
  --out-dir results
```

Extension treatments from the proposal:

```bash
python3 experiments/runner.py \
  --experiment extension \
  --repetitions 30 \
  --out-dir results
```

For a quick smoke test:

```bash
python3 experiments/runner.py \
  --experiment all \
  --repetitions 1 \
  --max-ticks 20 \
  --final-only \
  --out-dir results/smoke
```

## Summaries and Figures

Create a summary table from an experiment CSV:

```bash
python3 experiments/summarize.py \
  results/replication.csv \
  --output results/replication_summary.csv
```

Create a simple SVG line chart from a summary CSV:

```bash
python3 experiments/plotting.py \
  results/replication_summary.csv \
  --x similar_wanted \
  --y percent_similar_mean \
  --group density \
  --output results/replication_percent_similar.svg
```

## NetLogo Reference Data

Track B uses NetLogo 7 headless BehaviorSpace to generate reference data from
the original model in `netlogo/Segregation.nlogox`.

Full reference sweep:

```bash
"/path/to/NetLogo 7.0.4/netlogo-headless.sh" \
  --model netlogo/Segregation.nlogox \
  --setup-file netlogo/segregation_reference.xml \
  --experiment segregation-reference \
  --table results/netlogo/segregation_reference_table.csv \
  --threads 4
```

Convert the raw BehaviorSpace table to a normal CSV:

```bash
python3 experiments/convert_netlogo_table.py \
  results/netlogo/segregation_reference_table.csv \
  --output results/netlogo/segregation_reference_clean.csv
```

Summarise the NetLogo reference runs:

```bash
python3 experiments/summarize_netlogo.py \
  results/netlogo/segregation_reference_clean.csv \
  --output results/netlogo/segregation_reference_summary.csv
```

Generate NetLogo-derived spatial snapshots:

```bash
"/path/to/NetLogo 7.0.4/netlogo-headless.sh" \
  --model netlogo/Segregation.nlogox \
  --setup-file netlogo/segregation_snapshot_data.xml \
  --experiment segregation-snapshot-data \
  --table results/netlogo/snapshot_data_table.csv \
  --threads 1

python3 experiments/render_netlogo_snapshots.py \
  results/netlogo/snapshot_data_table.csv \
  --out-dir results/netlogo/screenshots
```

Already generated Track B artifacts are kept under `results/netlogo/`:

- `segregation_reference_table.csv`: raw BehaviorSpace output.
- `segregation_reference_clean.csv`: one clean row per NetLogo run.
- `segregation_reference_summary.csv`: mean and 95% CI by parameter cell.
- `snapshot_data_table.csv`: final turtle coordinates for representative runs.
- `screenshots/*.svg`: NetLogo-derived final-state spatial snapshots.
- `screenshots/png/*.png`: PNG versions for direct report insertion.

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
