import os
import sys
sys.path.insert(0, os.path.abspath('.'))

project = 'Stability Book'
author = 'Your Name'
release = '1.0'

extensions = [
    'recommonmark',  # 支持 Markdown
]

templates_path = ['_templates']
exclude_patterns = []

# HTML 输出
html_theme = 'alabaster'

# LaTeX / PDF 配置
latex_engine = 'xelatex'

FONTS_DIR = os.path.join(os.path.abspath('.'), "fonts")

latex_elements = {
    'papersize': 'a4paper',
    'pointsize': '12pt',
    'preamble': r'''
\usepackage{xeCJK}
\setCJKmainfont[BoldFont={%s}]{%s}
''' % (
    os.path.join(FONTS_DIR, "NotoSansCJKsc-Bold.otf"),
    os.path.join(FONTS_DIR, "NotoSansCJKsc-Regular.otf"),
),
}

latex_documents = [
    ('index', 'book.tex', 'Stability Book', 'Author', 'manual'),
]
