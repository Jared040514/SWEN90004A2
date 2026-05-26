# SWEN90004 Assignment 2 — Final Report

**Group members:** Ziyu ZHOU (1558985), Fei Man (1546877), Weichen Cheng (1386731)  
**Word count:** 1494 (body §1–§8, excluding references and appendices per the assignment specification)

---

## 1. Background & Motivation

Residential segregation by ethnicity, language or income persists in most modern cities and continues to attract attention from social scientists, urban planners and policymakers (Massey & Denton, 1988). It is a textbook *complex system*: the global spatial pattern is not designed by any central planner but emerges from many local, autonomous, repeated decisions. Schelling's (1978) Segregation model is the canonical demonstration of this emergence — using only an integer grid, two visually distinct groups and a single tolerance parameter, he showed that strong macro-level clustering can arise even when every individual is, in principle, willing to live among the other group. The Info section of Wilensky's (1997) NetLogo implementation records the model's striking signature: when every agent merely requires that 30 % of its neighbours share its colour, the simulated population eventually exhibits an average same-colour neighbour share of about 70 %.

Schelling's original mechanism treats colour as the only basis for relocation, but the urban-inequality literature emphasises that economic forces — rent gradients, household income, displacement pressure — also shape residential outcomes (Glaeser & Gyourko, 2018; Australian Bureau of Statistics, 2022). We therefore ask: *can income inequality alone, with no same-colour preference, reproduce Schelling-like spatial separation, and how do the two mechanisms compound when both are active?* Our extension answers both halves of this question affirmatively.

---

## 2. Model Design

**Original NetLogo model.** Wilensky's Segregation runs on a 51 × 51 wrapped grid that holds at most one turtle per patch. Two parameters control the world: `density` (per-patch occupancy probability, 50–99 %) and `%-similar-wanted` (the satisfaction threshold, 0–100 %). At setup, each patch is independently populated and the turtle is randomly coloured blue or orange. Each tick (i) halts if every turtle is `happy?`, otherwise (ii) every unhappy turtle performs a *continuous* random walk (`rt random-float 360`, `fd random-float 10`) that recurses from the new position whenever the chosen patch is occupied, (iii) all turtles recount same- and other-coloured Moore neighbours, and (iv) the globals `percent-similar` and `percent-unhappy` are recomputed. Two non-obvious details shape interpretation: `percent-similar` is the neighbour-count-weighted ratio `Σ similar / Σ total`, not a per-agent mean; and an isolated turtle with zero occupied neighbours satisfies the rule trivially and is counted *happy*.

**Python implementation.** Our code is modular and pure standard library — `segregation/{agent,world,model,stats}.py` plus `experiments/{runner,snapshot,summarize,plotting,build_report_figures}.py` and a CLI entry `main.py`. To match the NetLogo model exactly we keep floating-point positions during the random walk, snap to the patch centre only when the search succeeds, shuffle the unhappy list before iteration (mirroring NetLogo's randomised `ask`), and use the sum-weighted definition of `percent-similar`. A single seeded `random.Random` drives every stochastic choice so each run is reproducible.

> **Figure 1**: Schelling baseline at `density=80, %-similar-wanted=30, seed=1` showing the emergence of same-colour clusters across `t = 0, 3, 7, 11` (final). Source: `results/python/snapshots/baseline_d80_s30/`.

---

## 3. Extension: Economic Constraint as a Second Trigger

The extension adds two mechanisms that turn the Schelling grid into a stylised housing market. Each patch carries a `rent` drawn from a radial profile `rent(x, y) = R_max · exp(−d/scale)` with `R_max = 100` and `scale = 14`, producing an expensive centre and a cheap periphery. Each agent draws an `income` from a group-conditional discrete three-tier distribution (low = 35, mid = 65, high = 95); a single `income_gap ∈ [0, 1]` parameter shifts probability mass between tiers so that one group skews high-income and the other low-income, and `income_gap = 0` reproduces an economically homogeneous population.

The key behavioural change is a **dual-trigger unhappiness rule**: an agent is unhappy when **either** its same-colour neighbour share is below threshold **or** the rent of its current patch exceeds its income. An unhappy agent relocates only to patches that are both vacant **and** affordable; agents finding no admissible patch within a bounded number of attempts are counted as `stuck_unhappy`. Initial placement is uniform random and income-blind, so the model frames inequality as a *post-shock* relocation pressure on a pre-existing population.

This setup lets us run three treatments — **T1 preference-only** (original Schelling, affordability disabled), **T2 income-only** (`%-similar-wanted = 0`, preference always satisfied, only economic dissatisfaction is active), and **T3 combined** (both mechanisms enabled) — and ask: *can income inequality alone reproduce Schelling-like spatial separation, and how do the two mechanisms compound?*

---

## 4. Experimental Methodology

The replication experiment sweeps `%-similar-wanted ∈ {15, 20, …, 70}` × `density ∈ {70, 80, 90, 95}` with 30 independent repetitions per cell (1,440 runs). The extension contributes 660 further runs across the three treatments: T1 reuses the threshold sweep, while T2 and T3 sweep `income_gap ∈ {0.0, 0.25, 0.5, 0.75, 1.0}`. Seeds follow `seed = base + density·10^5 + threshold·10^3 + rep` so any individual run is exactly reproducible. Every run halts when all agents are happy; the extension additionally stops after 10,000 ticks or 50 consecutive no-movement ticks. Per-cell aggregates report the mean, the normal-approximation 95 % half-width, and a `convergence_rate` column that counts only runs ending in the natural "all happy" state. NetLogo BehaviorSpace runs the identical sweep on the unmodified `Segregation.nlogox` model and exports its results to `results/netlogo/full/replication.csv`, providing the ground-truth that our Python replication is compared against.

---

## 5. Replication Results

Our Python model reproduces the NetLogo baseline statistically and visually. At `%-similar-wanted = 30, density = 80` (Wilensky's stylised setting), the Python mean `percent_similar = 72.42 ± 0.38 %` matches the NetLogo `72.56 ± 0.45 %` within their combined confidence intervals; Figure 2 overlays the two curves across the whole threshold sweep and the maximum absolute difference at any of the twelve cells is 0.49 percentage points. The same agreement holds across the other three densities (supplementary chart `results/python/figures/fig2b_replication_overlay_all_densities.svg`), confirming that the replication is faithful in the small-difference regime as well as in the high-threshold regime where percent_similar exceeds 99 %.

Convergence behaviour matches too. 1,429 of 1,440 replication runs (99.2 %) reach the natural "all happy" halting condition within `max_ticks = 10,000`; cell-level convergence is 100 % everywhere except `(d=95, s=30)`, `(d=95, s=35)` and `(d=95, s=70)`, where 96.7 %, 96.7 % and 70 % of runs respectively converge. NetLogo exhibits the same difficulty at the same cells. Despite the statistical match, individual runs at the harder cells visit different metastable spatial configurations under different seeds — for example, at `(d=80, s=70)` we observe both "small-cluster" and "large-block" arrangements that all sit at ≈ 99.5 % similar (Figure 3).

> **Figure 2** — `results/python/figures/fig2_replication_overlay_d80.svg`: Python vs NetLogo mean `percent_similar` at `density=80`.
>
> **Figure 3** — composite of `results/python/snapshots/multi_seed/seed2/snap_final_t0074.svg` and `results/netlogo/snapshots/baseline_d80_s70/snap_final.svg`.

---

## 6. Extension Results

In T2 the same-colour preference is permanently satisfied (`%-similar-wanted = 0`), yet the high-income group still pays systematically higher rent than the low-income group. Figure 4 plots the mean rent paid by each group across `income_gap ∈ {0.0, 0.25, 0.5, 0.75, 1.0}`. At `gap = 0` the two lines coincide at ≈ 25.5; as the gap grows they diverge monotonically and at `gap = 1.0` the blue group averages 27.3 while the orange averages 24.1, a 3.2-unit gap in mean rent paid. `percent_similar` stays at the random baseline of ≈ 50 % throughout the sweep, confirming that the spatial sorting we observe is purely economic.

T3 combined enables both mechanisms with `%-similar-wanted = 30`. The preference-driven `percent_similar` stabilises at ≈ 74 % regardless of `income_gap`, while the inter-group rent gap widens from 0 to 4.8 as the gap grows. The two effects therefore stack additively: preference clustering and economic centre-vs-periphery sorting operate on largely orthogonal axes without cancelling. Across all 660 extension runs no agent ends up `stuck_unhappy`, indicating that under our parameter choices the affordability constraint is never permanently binding.

> **Figure 4** — `results/python/figures/fig4_t2_rent_gap.svg`.
>
> **Figure 5** — composite of `results/python/snapshots/baseline_d80_s30/snap_final_t0011.svg`, `.../extension_t2_g1/snap_final_t0001.svg`, `.../extension_t3_g1_s30/snap_final_t0015.svg`: T1 / T2 / T3 final-state side by side.

---

## 7. Discussion

Three observations stand out. First, the Schelling emergence result is robust: two independent implementations reach the same 72 % same-colour neighbour share from a 30 % individual preference, confirming that this is a property of the rule and not of any code path. Second, the income mechanism is *sufficient* — T2 shows clear spatial separation between groups in the complete absence of same-colour preference, lending model-side support to the urban-inequality literature on "rent burden" and economic displacement. Third, the two mechanisms compose without interfering: T3's preference clustering coexists with T2-style centre-vs-periphery sorting in roughly additive fashion, so a policy that addressed income disparity alone would not by itself dissolve preference-driven clustering. A secondary finding is that the high-density, high-threshold region admits multiple metastable equilibria — different seeds settle into qualitatively different spatial topologies that all satisfy the ≥ 99 % similar criterion, which we treat as a feature of the model rather than a disagreement between implementations.

---

## 8. Conclusion

Our pure-Python Schelling model statistically matches the original NetLogo implementation across 1,440 sweep runs, and our economic extension shows that income inequality alone reproduces Schelling-like spatial separation and stacks additively with same-colour preference.

---

## References  *(NOT counted toward word/page limit)*

- Schelling, T. (1978). *Micromotives and Macrobehavior*. Norton.
- Wilensky, U. (1997). NetLogo Segregation model. http://ccl.northwestern.edu/netlogo/models/Segregation. CCL, Northwestern University.
- Massey, D. S., & Denton, N. A. (1988). The dimensions of residential segregation. *Social Forces*, 67(2), 281–315.
- Glaeser, E. L., & Gyourko, J. (2018). The economic implications of housing supply. *Journal of Economic Perspectives*, 32(1), 3–30.
- Australian Bureau of Statistics (2022). *Household Income and Wealth, Australia, 2019-20 financial year*. ABS. <https://www.abs.gov.au/statistics/economy/finance/household-income-and-wealth-australia/latest-release>

---

## Appendix A — Collaboration log

The team split the work along two parallel tracks. **Track A** (Python implementation, snapshot tooling, statistical pipeline) was led by Ziyu Zhou with code review from Weichen Cheng; this delivered the `segregation/` model package, the `experiments/` runner and renderers, and the full 30-rep sweep. **Track B** (NetLogo reference data) was led by Fei Man, who configured BehaviorSpace, ran the matching sweep on `Segregation.nlogox`, and produced four representative spatial snapshots. Weichen Cheng coordinated cross-track integration and drafted the report.

Two notable challenges shaped the project. **First**, an initial full sweep recorded one CSV row per tick and produced a 26 MB file before convergence; the team identified the cause (a missing `--final-only` flag), preserved the partial output for forensics, and re-ran with the correct configuration in 37 minutes. **Second**, the two tracks initially adopted incompatible `.gitignore` strategies (denylist vs. allowlist) that would have conflicted on merge; we resolved this with a cherry-pick into a single branch followed by a `git mv`-driven restructure into a symmetric `results/{python,netlogo}` layout (PR #2).

The only material change from the proposal was the move to a **dual-trigger unhappiness rule** in the extension, after an early review noted that the original "income-only" treatment as proposed was logically empty (with `%-similar-wanted = 0`, no agent would ever be unhappy under the unchanged rule and the extension mechanism would never fire).

## Appendix B — AI usage statement

The team used two AI tools in this project, with all suggestions reviewed by a human before being committed or included in the report.

**Claude (via Claude Code CLI)** was used to (i) draft the proposal and final report (this document), with the team revising for accuracy and tone; (ii) generate and review code in the `segregation/` and `experiments/` packages — the team specified the design, requested implementations, and verified output against NetLogo behaviour; (iii) plan and execute the `results/` restructure under plan-mode (PR #2); and (iv) produce the snapshot SVG renderer (`experiments/snapshot.py`) and the report figure builder (`experiments/build_report_figures.py`).

**Codex (via plugin)** provided independent code review at key checkpoints. Its review of the proposal caught the logical hole in the original "income-only" treatment design, which led directly to the dual-trigger unhappiness rule used in the final extension.

All AI-suggested code was tested by running the affected experiments end-to-end before commit. All AI-drafted prose was reviewed by the team and edited for factual accuracy against the actual experimental output. The team retains full responsibility for design decisions and final correctness. We followed the University's guidance at <https://www.unimelb.edu.au/ai/home/students>.

---

