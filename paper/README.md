# Paper source and reproduction

[Read the PDF](main.pdf) · [Edit the LaTeX](main.tex) · [Source ledger](../docs/sources.md) · [Architecture source](../docs/architecture.drawio)

**Flash Silicon Analyzer: An Inspectable Browser Tool for CMOS Power, Performance, Area, Yield, and Cost Exploration** is an arXiv-style methods manuscript describing the repository's existing implementation. It includes model equations, architectural boundaries, reproducible numerical experiments, six verified literature/vendor references, and an explicit account of missing parameter provenance.

The paper's author is **Liang Dacheng**, as confirmed by the repository owner. Affiliation and email are omitted. Review the scientific claims and resolve or retain the stated provenance limitations before submission. The paper has not been submitted to arXiv and makes no measured-silicon accuracy claim.

## Reproduce the experiments

Run from the repository root:

```bash
node paper/scripts/evaluate.mjs
```

Only Node.js is required (tested with **v22.22.1**). The driver reads the real HTML controls, runs the embedded model functions, and writes [results/experiments.json](results/experiments.json). It does not change the application.

The recorded scenarios are:

| JSON key | Scenario |
| --- | --- |
| `baseline`, `provenance`, `coverage` | HTML defaults, source SHA-256, runtime version, and selectable nodes |
| `sweep` | TSMC nodes with the default N12 reference design |
| `mixed` | Same logic plus 256 Mbit SRAM, 2 W SRAM power, and 40 mm² fixed area |
| `sensitivity` | One-at-a-time defect, wafer-cost, area, frequency, and power multipliers |
| `costBases` | Introductory price versus manufacturing cost at N6 |
| `stacks` | Two- and three-layer Huawei LogicFold 2026 roadmap scenarios |
| `mapCases` | Independent initial map, target synchronization, radial/PPM ablation, and stacks |
| `seedSummary` | Synchronized default map over seeds 1–100 |
| `checks` | 41 identity cases, 1,681 source/target combinations, and additional consistency checks |

The harness disables the final rendering bootstrap and supplies a minimal DOM adapter for controls. `calc()` and `calcWaferMap()` are executed directly from `index.html`. The manual-sync rounding is mirrored in the driver because the original sync function also renders Canvas output. Verify that adapter when changing UI initialization or synchronization behavior.

## Regenerate the figures and tables

The checked-in PDF figures and LaTeX tables let you compile the paper without installing Python packages. To regenerate them, use Python 3.10 or newer and Matplotlib; the recorded rendering environment used Python 3.10 and Matplotlib 3.10.8:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r paper/requirements.txt
node paper/scripts/evaluate.mjs
.venv/bin/python paper/scripts/render_figures.py
```

The renderer produces:

- `docs/architecture.svg` and `paper/figures/architecture.pdf`, from the editable draw.io source.
- `paper/figures/node_sweep.pdf` and `.svg`, from the numerical results.
- `paper/tables/node_sweep.tex` and `paper/tables/sensitivity.tex`, from those same results.

It checks that diagram text stays inside its boxes and that connectors do not intersect text, with a four-pixel clearance around text for connector checks. It also checks text against other text. The renderer supports the simple rectangles, plain text, and explicit connector waypoints used by this diagram; it is not a general draw.io exporter. For richer diagram features, use the editor's own SVG/PDF export and inspect the output.

To edit the architecture, open [architecture.drawio](../docs/architecture.drawio) in draw.io Desktop or [diagrams.net](https://app.diagrams.net/). Keep labels in open space, preserve connector waypoints, and regenerate both exports after edits.

## Compile the manuscript

Use a TeX distribution with pdfLaTeX and the standard packages listed at the start of `main.tex`:

```bash
cd paper
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

Or, from the repository root:

```bash
make -C paper pdf
```

An alternative is **Tectonic** (the local build used version 0.17.0):

```bash
tectonic --untrusted --keep-logs paper/main.tex
```

Tectonic may download its TeX bundle on first use. The document uses ordinary LaTeX, vector PDF figures, generated table inputs, and an inline `thebibliography`, so BibTeX, a `.bbl` file, shell escape, and on-the-fly figure conversion are unnecessary. The local Tectonic build is not a claim that arXiv's own processing has been tested.

## Package the source for arXiv

From the repository root:

```bash
python3 paper/scripts/package_source.py
```

This writes `paper/arxiv-source.zip` containing `main.tex`, both required PDF figures, and both generated table files. No build logs, application code, or unused SVG/draw.io assets are included. The script also checks citation keys and referenced assets before packaging.

Open the ZIP and review its contents before uploading. Use `main.tex` as the entry document. arXiv recompiles TeX source and requires its dependencies to be included; check its [official TeX submission guidance](https://info.arxiv.org/help/submit_tex.html) when submitting. Generating the archive does not publish or submit anything.

## Updating the results

The evaluated Flash Silicon Analyzer application is identified by its HTML SHA-256, recorded in both the paper and JSON. If the application changes, rerun the experiments, regenerate figures/tables, and update the manuscript's hash, prose values, coverage, and conclusions. Tables regenerate automatically; numerical prose requires review.

Optional Make targets:

```bash
make -C paper experiments
make -C paper figures PYTHON=../.venv/bin/python
make -C paper pdf
make -C paper source
```
