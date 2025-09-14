# Makefile for Sphinx documentation

# 目录
SPHINXBUILD   = sphinx-build
SOURCEDIR     = docs
BUILDDIR      = $(SOURCEDIR)/_build

# 默认构建 HTML
html:
	$(SPHINXBUILD) -b html $(SOURCEDIR) $(BUILDDIR)/html
	@echo "Build finished. HTML files are in $(BUILDDIR)/html"

# 构建 LaTeX 再生成 PDF (强制使用 xelatex)
latexpdf:
	$(SPHINXBUILD) -b latex $(SOURCEDIR) $(BUILDDIR)/latex
	latexmk -xelatex -f -cd $(BUILDDIR)/latex/stability.tex
	@echo "Build finished. PDF file is in $(BUILDDIR)/latex"

# 清理构建目录
clean:
	rm -rf $(BUILDDIR)
	@echo "Cleaned build directory."
