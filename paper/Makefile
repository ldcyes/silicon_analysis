PYTHON ?= python3
NODE ?= node
PDFLATEX ?= pdflatex

.PHONY: experiments figures pdf source

experiments:
	$(NODE) scripts/evaluate.mjs

figures: experiments
	$(PYTHON) scripts/render_figures.py

pdf:
	$(PDFLATEX) -interaction=nonstopmode -halt-on-error main.tex
	$(PDFLATEX) -interaction=nonstopmode -halt-on-error main.tex

source:
	$(PYTHON) scripts/package_source.py
