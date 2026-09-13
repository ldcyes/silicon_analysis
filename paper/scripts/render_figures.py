#!/usr/bin/env python3
"""Render paper figures and the simple shapes in docs/architecture.drawio.

The draw.io file is the editable source. This renderer supports the rectangles,
plain text, explicit waypoints and arrows used in that file, not arbitrary draw.io.
For richer edits, export SVG/PDF directly from diagrams.net instead.
"""
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET

os.environ.setdefault("MPLCONFIGDIR", "/tmp/flash-silicon-analyzer-matplotlib")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

PAPER = Path(__file__).resolve().parents[1]
ROOT = PAPER.parent
FIGURES = PAPER / "figures"
FIGURES.mkdir(exist_ok=True)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                     "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none"})


def save_svg(fig, path):
    fig.savefig(path, metadata={"Date": None})
    # Matplotlib puts trailing spaces in multiline path attributes; keep Git diffs clean.
    path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")


def architecture():
    graph = ET.parse(ROOT / "docs/architecture.drawio").find(".//mxGraphModel")
    width, height = float(graph.get("pageWidth")), float(graph.get("pageHeight"))
    cells = {c.get("id"): c for c in graph.findall("root/mxCell")}

    def style(cell):
        return dict(part.split("=", 1) for part in cell.get("style", "").split(";") if "=" in part)

    def bounds(cell):
        g = cell.find("mxGeometry")
        return tuple(float(g.get(k, 0)) for k in ("x", "y", "width", "height"))

    fig = plt.figure(figsize=(width / 100, height / 100), facecolor="white")
    ax = fig.add_axes([0, 0, 1, 1], xlim=(0, width), ylim=(height, 0))
    ax.axis("off")
    segments, text_artists = [], []
    # Paint boxes, then connectors, then text to preserve labels above edges.
    for cell in cells.values():
        if cell.get("vertex") != "1" or cell.get("style", "").startswith("text;"):
            continue
        x, y, w, h = bounds(cell)
        s = style(cell)
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=12",
                     facecolor=s.get("fillColor", "white"), edgecolor=s.get("strokeColor", "#334155"),
                     linewidth=float(s.get("strokeWidth", 1.5)), zorder=1))
    for cell in cells.values():
        if cell.get("edge") != "1":
            continue
        s = style(cell)
        source, target = cells[cell.get("source")], cells[cell.get("target")]
        sx, sy, sw, sh = bounds(source)
        tx, ty, tw, th = bounds(target)
        points = [(sx + sw * float(s.get("exitX", .5)), sy + sh * float(s.get("exitY", 1)))]
        points += [(float(p.get("x")), float(p.get("y"))) for p in cell.findall(".//mxPoint")]
        points += [(tx + tw * float(s.get("entryX", .5)), ty + th * float(s.get("entryY", 0)))]
        segments.extend((cell.get("id"), a, b) for a, b in zip(points, points[1:]))
        color = s.get("strokeColor", "#64748b")
        ls = "--" if s.get("dashed") == "1" else "-"
        ax.plot(*zip(*points[:-1]), color=color, linewidth=1.5, linestyle=ls, zorder=2)
        ax.add_patch(FancyArrowPatch(points[-2], points[-1], arrowstyle="-|>", mutation_scale=15,
                     color=color, linewidth=1.5, linestyle=ls, shrinkA=0, shrinkB=1, zorder=2))
    for cell in cells.values():
        value = cell.get("value", "")
        if cell.get("vertex") != "1" or not value:
            continue
        s = style(cell)
        x, y, w, h = bounds(cell)
        align = s.get("align", "center")
        # Draw.io font sizes are CSS pixels; Matplotlib uses points.
        size = float(s.get("fontSize", 19)) * .72
        lines = value.splitlines()
        step = float(s.get("fontSize", 19)) * 1.38
        for i, line in enumerate(lines):
            artist = ax.text(x if align == "left" else x + w / 2,
                    y + h / 2 + (i - (len(lines) - 1) / 2) * step,
                    line, ha=align, va="center", fontsize=size,
                    color=s.get("fontColor", "#0f172a"),
                    fontweight="bold" if s.get("fontStyle") == "1" or (len(lines) > 1 and i == 0) else "normal",
                    zorder=3)
            text_artists.append((cell, artist))
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    boxes = []
    for cell, artist in text_artists:
        bbox = artist.get_window_extent(renderer).transformed(ax.transData.inverted())
        left, right = sorted([bbox.x0, bbox.x1])
        top, bottom = sorted([bbox.y0, bbox.y1])
        boxes.append((cell.get("id"), left, top, right, bottom))
        if not cell.get("style", "").startswith("text;"):
            x, y, w, h = bounds(cell)
            assert x + 10 <= left and right <= x + w - 10, f"Text exceeds box width: {cell.get('id')}"
            assert y + 8 <= top and bottom <= y + h - 8, f"Text exceeds box height: {cell.get('id')}"

    def intersects(a, b, box):
        _, left, top, right, bottom = box
        left, top, right, bottom = left - 4, top - 4, right + 4, bottom + 4
        low, high = 0., 1.
        for start, delta, mn, mx in [(a[0], b[0] - a[0], left, right), (a[1], b[1] - a[1], top, bottom)]:
            if abs(delta) < 1e-9:
                if start < mn or start > mx:
                    return False
            else:
                t1, t2 = sorted(((mn - start) / delta, (mx - start) / delta))
                low, high = max(low, t1), min(high, t2)
                if low > high:
                    return False
        return True

    for edge_id, a, b in segments:
        for box in boxes:
            assert not intersects(a, b, box), f"Connector {edge_id} overlaps text in {box[0]}"
    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            overlap = max(a[1], b[1]) < min(a[3], b[3]) and max(a[2], b[2]) < min(a[4], b[4])
            assert not overlap, f"Text overlap: {a[0]} / {b[0]}"
    print(f"Architecture layout: {len(text_artists)} text lines checked; no text/connector overlaps.")
    save_svg(fig, ROOT / "docs/architecture.svg")
    fig.savefig(FIGURES / "architecture.pdf", metadata={"CreationDate": None, "ModDate": None})
    plt.close(fig)


def results():
    data = json.loads((PAPER / "results/experiments.json").read_text())
    simple, mixed = data["sweep"], data["mixed"]
    x = list(range(len(simple)))
    labels = [str(r["node"]) for r in simple]
    plt.rcParams["font.size"] = 11
    fig, axes = plt.subplots(1, 2, figsize=(8.5, 3.4), layout="constrained")
    for ax, key, ylabel in zip(axes, ["totalArea", "cost"], ["Total area (mm²)", "Cost per good die (USD)"]):
        for values, color, label in [(simple, "#2563eb", "Logic only"), (mixed, "#c2410c", "Logic + SRAM + fixed area")]:
            ax.plot(x, [r[key] for r in values], "o-", color=color, label=label, markersize=4, linewidth=1.7)
        ax.set(xticks=x, xticklabels=labels, xlabel="TSMC nominal node label (nm)", ylabel=ylabel)
        ax.grid(alpha=.18)
        ax.spines[["top", "right"]].set_visible(False)
        ax.legend(fontsize=10)
    fig.savefig(FIGURES / "node_sweep.pdf", metadata={"CreationDate": None, "ModDate": None})
    save_svg(fig, FIGURES / "node_sweep.svg")
    plt.close(fig)

    tables = PAPER / "tables"
    tables.mkdir(exist_ok=True)
    lines = []
    for r in simple:
        lines.append(f"{r['node']} & {r['totalArea']:.2f} & {r['freq']:.3f} & {r['powerConv']:.3f} & {r['finalYield'] * 100:.2f} & {r['cost']:.2f} " + r"\\")
    (tables / "node_sweep.tex").write_text(
        "% Generated by scripts/render_figures.py\n"
        + r"\begin{tabular}{rrrrrr}" + "\n" + r"\toprule" + "\n"
        + r"Label (nm) & Area (mm$^2$) & Frequency (GHz) & Power (W) & Yield (\%) & Cost (\$)\\" + "\n"
        + r"\midrule" + "\n" + "\n".join(lines) + "\n"
        + r"\bottomrule" + "\n" + r"\end{tabular}" + "\n")
    lines = []
    names = {"d0Mult": r"Defect multiplier $m_D$", "costMult": r"Wafer multiplier $m_C$",
             "areaOverhead": r"Area overhead $h_A$", "freqRealization": r"Frequency realization $h_f$",
             "powerGuard": r"Power guardband $h_P$"}
    for r in data["sensitivity"]:
        if r["value"] == 1:
            continue
        lines.append(f"{names[r['parameter']]} & {r['value']:.1f} & {r['totalArea']:.2f} & {r['freq']:.2f} & {r['powerConv']:.3f} & {r['finalYield'] * 100:.2f} & {r['cost']:.2f} " + r"\\")
    (tables / "sensitivity.tex").write_text(
        "% Generated by scripts/render_figures.py\n"
        + r"\begin{tabular}{lrrrrrr}" + "\n" + r"\toprule" + "\n"
        + r"Parameter & Value & Area & GHz & W & Yield (\%) & Cost (\$)\\" + "\n"
        + r"\midrule" + "\n" + "\n".join(lines) + "\n"
        + r"\bottomrule" + "\n" + r"\end{tabular}" + "\n")


if __name__ == "__main__":
    architecture()
    results()
    print("Rendered draw.io preview, paper PDF figures, and result tables.")
