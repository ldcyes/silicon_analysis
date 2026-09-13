# Source provenance and claim boundaries

This ledger accompanies the Flash Silicon Analyzer paper and README. The evaluated application is identified by the `index.html` SHA-256 in `paper/results/experiments.json`. External references were checked on 2026-09-13. It distinguishes published context from the actual parameter provenance available in this repository.

## Verified references used by the paper

| Reference | Supported use | What it does not establish |
| --- | --- | --- |
| Stillmaker & Baas, *Scaling equations for the accurate prediction of CMOS device performance from 180 nm to 7 nm*, Integration 58, 74–81 (2017). [Author page and corrigendum](https://vcl.ece.ucdavis.edu/pubs/2017.02.VLSIintegration.TechScale/), [DOI](https://doi.org/10.1016/j.vlsi.2017.02.002) | Context for fitted technology scaling and source/target factor ratios | Accuracy of this implementation or its advanced-node constants |
| Sarangi & Baas, *DeepScaleTool* (2021). [arXiv:2102.10195](https://arxiv.org/abs/2102.10195) | Context for fitting published area, delay, and energy trends over 130–7 nm | This repository does not implement its fitting procedure or inherit its error rates |
| Bogdanov, Bogdanova & Dshkhunyan, *Statistical Yield Modeling for IC Manufacture: Hierarchical Fault Distributions* (2003). [arXiv:physics/0303039](https://arxiv.org/abs/physics/0303039) | Context for compound and negative-binomial fault models | The app's D0/α values, synthetic wafer maps, or W2W independence assumptions |
| TSMC, *TSMC Unveils 6-nanometer Process*, 2019-04-16. [Announcement](https://pr.tsmc.com/english/news/1989) | N6's stated 18% higher logic density over N7; consistent with `7.08 / 6.00` in `DATA` | N6 defect density, wafer price, SRAM density, or the complete N12→N6 experiment |
| GlobalFoundries, *Industry's First 22nm FD-SOI Technology Platform*, 2015-07-13. [Announcement](https://investors.gf.com/news-releases/news-release-details/globalfoundries-launches-industrys-first-22nm-fd-soi-technology) | 22FDX is FD-SOI; stated 20% smaller die versus 28 nm is consistent with inverse density `1 / 1.25` | All GF power/speed fields or every library/design configuration |
| GlobalFoundries, *Reshapes Technology Portfolio*, 2018-08-27. [Announcement](https://investors.gf.com/news-releases/news-release-details/globalfoundries-reshapes-technology-portfolio-intensify-focus) | Historical decision to put the 7 nm program on hold | A current commercial process-availability survey |

## Parameters requiring calibration or missing provenance

| Parameter group | Evidence in the repository | How the manuscript treats it |
| --- | --- | --- |
| Per-node density, energy, speed, SRAM, and VDD | Embedded numeric factors and descriptive notes; no complete field-level citation set | Model inputs; published anchors checked only where explicitly cited above |
| `wafer` and `intro` cost fields | Page attributes them to two uploaded IBS-style tables; those uploads are absent | Scenario baselines, with no invented source title/date or foundry-specific price claim |
| D0 values and line yield | Numeric defaults and calibration sliders | Assumptions, not measured production yields |
| Leakage fraction 0.08, exponents 0.72 and 1.2, minimum scale 0.08 | Constants inside `calc()` | Heuristics with no claimed empirical fit |
| SRAM dynamic-power scaling | Inverse SRAM density × voltage ratio squared | Approximation, not characterized macro energy |
| Huawei raw MTR, ×2/3 conversion, effective chip density, roadmap PPA | Code and notes referring to uploaded Huawei/LogicFolding slides; slides absent | Repository roadmap scenarios, not verified product claims |
| W2W layers and bond yield | Model implementation, default 2 layers and 99.5% per-interface bonding yield | Identical-layer, independent-failure assumptions; no thermal or partitioning study |
| Confidence labels | One label per process record | Qualitative annotations, not per-field evidence or statistical confidence |

## Scope of the numerical results

`paper/results/experiments.json` records the original HTML hash, HTML defaults, process coverage, and numerical outputs. Scenario overrides, including the mixed design's SRAM and fixed-area inputs, are specified in `paper/scripts/evaluate.mjs`. The driver calls the original `calc()` and `calcWaferMap()` functions. Its source/target checks establish execution and arithmetic consistency at specified inputs. No silicon dataset, held-out calibration set, foundry quote, latency benchmark, or user study is provided.

The spatial model uses location-dependent pass probabilities and deterministic hash draws. The negative-binomial marginal yield does not make the rendered map a correlated spatial defect simulation. For stacks, the code averages per-location stack probabilities, which can differ from raising the average layer yield to the layer count.

Before making predictive claims, add retrievable source material for each field, calibration conditions, representative physical-design or measured results, and an independent evaluation dataset. Preserve the distinction between measured values, published relative claims, interpolation, and assumptions.
