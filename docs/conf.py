# conf.py
import os
import sys
sys.path.insert(0, os.path.abspath('.'))

# 基本项
project = '稳定性架构：分布式系统的设计与实践'
author = '阿涵'
release = '1.0'
master_doc = 'index'

# 扩展
extensions = [
    # 'recommonmark',   # 支持 Markdown
    "myst_parser",
]

# HTML 主题
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# PDF 配置
latex_engine = 'xelatex'
latex_elements = {
    'papersize': 'a4paper',
    'pointsize': '12pt',

    # 强制覆盖字体设置
    'fontpkg': r'''
\usepackage{xeCJK}
\setCJKmainfont{Songti SC}          % 中文正文
\setCJKsansfont{Heiti SC}           % 中文无衬线
\setCJKmonofont{PingFang SC}        % 中文等宽

\setmainfont{Times New Roman}       % 英文正文
\setsansfont{Arial}                 % 英文无衬线
\setmonofont{Courier New}           % 英文等宽
''',

    'preamble': r'''
\usepackage{indentfirst}
\setlength{\parindent}{2em}

\usepackage{fancyhdr}
\pagestyle{fancy}
\fancyhead{}
\fancyfoot{}
\fancyfoot[C]{\thepage}
''',
}

# latex_use_xindy = True
# latex_elements = {
#     # The paper size ('letterpaper' or 'a4paper').
#     'papersize': 'a4paper',

#     # The font size ('10pt', '11pt' or '12pt').
#     # 'pointsize': '12pt',
#     'pointsize': '10pt',
#     # 'classoptions': ',english',
#     'inputenc': '',
#     'utf8extra': '',
#     'extraclassoptions': 'openany',

#     # Additional stuff for the LaTeX preamble.
#     'preamble': r'''
# \usepackage{xeCJK}
# \usepackage{indentfirst}
# \setlength{\parindent}{2em}
# \setCJKmainfont[BoldFont=SimHei, ItalicFont=STKaiti]{SimSun}
# \setCJKmonofont[Scale=0.9]{SimSun}
# \setCJKfamilyfont{song}[BoldFont=SimSun]{SimSun}
# \setCJKfamilyfont{sf}[BoldFont=SimSun]{SimSun}
# ''',
#     # 'fncychap': r'\usepackage[Bjornstrup]{fncychap}',
#     # 'printindex': r'\footnotesize\raggedright\printindex',
# }
# latex_elements['preamble'] = r"""
# \usepackage{xeCJK}
# \usepackage{indentfirst}
# \setlength{\parindent}{2em}
# \setCJKmainfont[BoldFont=SimHei, ItalicFont=STKaiti]{SimSun}
# \setCJKmonofont[Scale=0.9]{SimSun}
# \setCJKfamilyfont{song}[BoldFont=SimSun]{SimSun}
# \setCJKfamilyfont{sf}[BoldFont=SimSun]{SimSun}
# \XeTeXlinebreaklocale "zh"
# \XeTeXlinebreakskip = 0pt plus 1pt
# \parindent 2em
# \definecolor{VerbatimColor}{rgb}{0.95,0.95,0.95}
# \setcounter{tocdepth}{3}
# \renewcommand\familydefault{\ttdefault}
# \renewcommand\CJKfamilydefault{\CJKrmdefault}
# """

latex_documents = [
    ('index', 'stability.tex', project, author, 'manual'),
]


myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "html_admonition",
    "html_image",
    "linkify",
    "replacements",
    "smartquotes",
    "substitution",
    "tasklist",
    "strikethrough",
    #"tables",  # 关键
]
