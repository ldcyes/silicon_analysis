#!/usr/bin/env python3
"""Create a self-contained TeX source ZIP; this does not submit the paper."""
from pathlib import Path
import re
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

paper = Path(__file__).resolve().parents[1]
text = (paper / "main.tex").read_text()
files = {"main.tex"}
for command, name in re.findall(r"\\(input|includegraphics)(?:\[[^\]]*\])?\{([^}]+)\}", text):
    path = name if command == "includegraphics" or name.endswith(".tex") else name + ".tex"
    files.add(path)
keys = set(re.findall(r"\\bibitem\{([^}]+)\}", text))
cited = {key.strip() for group in re.findall(r"\\cite\{([^}]+)\}", text) for key in group.split(",")}
assert cited <= keys, f"Unresolved citations: {cited - keys}"
for name in files:
    path = (paper / name).resolve()
    assert path.is_relative_to(paper), f"Source asset outside paper directory: {name}"
    assert path.is_file(), f"Missing source asset: {name}"
archive = paper / "arxiv-source.zip"
with ZipFile(archive, "w", compression=ZIP_DEFLATED) as output:
    for name in sorted(files):
        info = ZipInfo(name, date_time=(2026, 9, 13, 0, 0, 0))
        info.compress_type = ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        output.writestr(info, (paper / name).read_bytes())
with ZipFile(archive) as check:
    assert check.testzip() is None
print(f"Created {archive.name}: {len(files)} files, {len(cited)} resolved references")
for name in sorted(files):
    print(f"  {name}")
