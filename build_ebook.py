import os
import subprocess
from jinja2 import Template

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHAPTERS_DIR = os.path.join(BASE_DIR, "chapters")
OUTPUT_TEX = os.path.join(BASE_DIR, "build", "book.tex")
OUTPUT_PDF = os.path.join(BASE_DIR, "book.pdf")

# 遍历 Part + Chapter
def collect_parts():
    parts = []
    for item in sorted(os.listdir(CHAPTERS_DIR)):
        part_path = os.path.join(CHAPTERS_DIR, item)
        if os.path.isdir(part_path) and not item.startswith("_"):
            part = {"title": item, "readme": "", "chapters": []}
            for f in sorted(os.listdir(part_path)):
                if f.lower() == "readme.md":
                    part["readme"] = os.path.join(part_path, f)
                elif f.endswith(".md"):
                    part["chapters"].append(os.path.join(part_path, f))
            parts.append(part)
    return parts

# Pandoc Markdown → LaTeX
def md_to_latex(md_file):
    result = subprocess.run(
        ["pandoc", md_file, "-f", "markdown", "-t", "latex", "--metadata", "link-citations=false", "--no-highlight", "--top-level-division=chapter", "--wrap=none"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8"
    )
    if result.returncode != 0:
        print(f"Pandoc 转 LaTeX 出错: {result.stderr}")
        return ""
    tex = result.stdout

    # 移除所有 \label{...} 防止中文导致报错
    import re
    tex = re.sub(r'\\label\{.*?\}', '', tex)
    return tex

# 渲染 LaTeX 模板
def render_tex(parts):
    template_path = os.path.join(BASE_DIR, "template", "template.tex")
    with open(template_path, "r", encoding="utf-8") as f:
        template_content = f.read()
    template = Template(template_content)
    return template.render(parts=parts)

def main():
    os.makedirs(os.path.join(BASE_DIR, "build"), exist_ok=True)
    parts = collect_parts()

    # 生成 LaTeX 内容
    for part in parts:
        part["readme_tex"] = md_to_latex(part["readme"]) if part["readme"] else ""
        chapters_data = []
        for chap in part["chapters"]:
            tex = md_to_latex(chap)
            # 获取章节标题
            first_line = tex.strip().split("\n")[0]
            title = first_line.replace("\\section{", "").replace("}", "") if first_line.startswith("\\section") else os.path.basename(chap)
            chapters_data.append({"title": title, "tex": tex})
        part["chapters_data"] = chapters_data

    tex_content = render_tex(parts)
    with open(OUTPUT_TEX, "w", encoding="utf-8") as f:
        f.write(tex_content)

    # XeLaTeX 生成 PDF
    subprocess.run([
        "xelatex",
        "-interaction=nonstopmode",
        "-output-directory", os.path.join(BASE_DIR, "build"),
        OUTPUT_TEX
    ])
    generated_pdf = os.path.join(BASE_DIR, "build", "book.pdf")
    if os.path.exists(generated_pdf):
        os.replace(generated_pdf, OUTPUT_PDF)
        print(f"PDF 已生成: {OUTPUT_PDF}")

if __name__ == "__main__":
    main()
