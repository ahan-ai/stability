import os
import subprocess
from jinja2 import Environment
import re
import urllib.request
import urllib.parse
import hashlib
import mimetypes

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHAPTERS_DIR = os.path.join(BASE_DIR, "chapters")
BUILD_DIR = os.path.join(BASE_DIR, "build")
OUTPUT_TEX = os.path.join(BUILD_DIR, "book.tex")
OUTPUT_PDF = os.path.join(BASE_DIR, "book.pdf")
MEDIA_DIR = os.path.join(BUILD_DIR, "media")

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

def _download_image(url, media_dir):
    """下载远程图片到 media_dir，返回本地相对路径（相对于 BASE_DIR），或 None."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
            ctype = resp.headers.get("Content-Type", "")
    except Exception as e:
        print("warn: 下载图片失败:", url, e)
        return None

    # 推断扩展名
    ext = None
    if ctype:
        ctype_main = ctype.split(";")[0].strip()
        ext = mimetypes.guess_extension(ctype_main)
    # 如果从 URL path 得到扩展名优先
    path_ext = os.path.splitext(urllib.parse.urlsplit(url).path)[1]
    if path_ext and len(path_ext) <= 6:
        ext = path_ext
    if not ext:
        ext = ".png"

    # 用 URL 的 hash 生成文件名，避免非法字符
    h = hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]
    fname = f"img-{h}{ext}"
    out_path = os.path.join(media_dir, fname)
    try:
        with open(out_path, "wb") as f:
            f.write(data)
        # 返回相对于 BASE_DIR 的路径（便于 pandoc 生成的 tex 路径直接可用）
        rel = os.path.relpath(out_path, BUILD_DIR)
        return rel.replace("\\", "/")
    except Exception as e:
        print("warn: 写文件失败:", out_path, e)
        return None

def _localize_images_in_md(md_path):
    """读取 md 文件，下载所有远程图片（常见的 ![alt](url) 以及 <img src="url">），
       替换为本地路径，写入 build 下的临时 md 并返回其路径。
    """
    with open(md_path, "r", encoding="utf-8") as f:
        text = f.read()

    # 确保 media 目录存在
    os.makedirs(MEDIA_DIR, exist_ok=True)

    # 1) 处理标准 Markdown 图片语法 ![alt](url "title")
    #    这个 regex 适用于大多数情况（注意：若 url 包含未配对的括号，可能失效）
    md_img_re = re.compile(r'!\[([^\]]*)\]\((\S+?)(?:\s+"[^"]*")?\)')

    def md_repl(m):
        alt = m.group(1)
        url = m.group(2).strip()
        # 如果 url 有尖括号 <...>, 去掉
        if url.startswith("<") and url.endswith(">"):
            url = url[1:-1]
        if url.lower().startswith("http"):
            local = _download_image(url, MEDIA_DIR)
            if local:
                return f'![{alt}]({local})'
            else:
                return m.group(0)  # 下载失败，保持原样
        else:
            return m.group(0)

    text = md_img_re.sub(md_repl, text)

    # 2) 处理 HTML <img src="..."> 的情况（Notion 导出有时会用这种）
    html_img_re = re.compile(r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>')
    def html_repl(m):
        url = m.group(1).strip()
        if url.lower().startswith("http"):
            local = _download_image(url, MEDIA_DIR)
            if local:
                # 用 markdown 语法替换为普通图片引用（pandoc 更容易处理）
                return f'![]({local})'
            else:
                return m.group(0)
        else:
            return m.group(0)
    text = html_img_re.sub(html_repl, text)

    # 写入到 build 下的临时 md（文件名保持不变）
    out_md = os.path.join(BUILD_DIR, os.path.basename(md_path))
    with open(out_md, "w", encoding="utf-8") as f:
        f.write(text)
    return out_md

# Pandoc Markdown → LaTeX
def md_to_latex(md_file):
    """
    将 Markdown 转 LaTeX，保证图片路径可直接在 build/book.tex 中生成 PDF。
    """
    # 1. 下载远程图片并替换为本地路径
    tmp_md = _localize_images_in_md(md_file)

    # 2. 调用 Pandoc 转 LaTeX
    result = subprocess.run(
        [
            "pandoc", tmp_md,
            "-f", "markdown",
            "-t", "latex",
            "--metadata", "link-citations=false",
            "--no-highlight",
            "--top-level-division=section",
            "--wrap=none"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8"
    )
    if result.returncode != 0:
        print(f"Pandoc 转 LaTeX 出错: {result.stderr}")
        return ""
    tex = result.stdout

    # 3. 移除所有 \label{...} 防止中文报错
    tex = re.sub(r'\\label\{.*?\}', '', tex)

    # 4. 替换特殊符号 ▪ → \textbullet{}
    tex = tex.replace("▪", "\\textbullet{}")

    # 5. 修正 \includegraphics
    def fix_graphics(match):
        # 路径
        path = match.group(2)
        # 路径转为绝对路径再相对于 BASE_DIR
        abs_path = os.path.abspath(os.path.join(BUILD_DIR, path)) if not os.path.isabs(path) else path
        rel_path = os.path.relpath(abs_path, BASE_DIR).replace("\\", "/")

        # 使用固定选项
        options = "[keepaspectratio,width=\\linewidth]"

        # 使用 \pandocbounded 包裹
        return f"\\pandocbounded{{\\includegraphics{options}{{{rel_path}}}}}"

    tex = re.sub(
        r'\\includegraphics(\[.*?\])\{(.*?)\}',
        fix_graphics,
        tex
    )

    return tex

# 渲染 LaTeX 模板
def render_tex(parts):
    template_path = os.path.join(BASE_DIR, "template", "template.tex")
    with open(template_path, "r", encoding="utf-8") as f:
        template_content = f.read()
    env = Environment(
        block_start_string = '<%',
        block_end_string = '%>',
        variable_start_string = '<<',
        variable_end_string = '>>',
        comment_start_string = '<#',
        comment_end_string = '#>',
        autoescape = False
    )
    template = env.from_string(template_content)
    return template.render(parts=parts)

def main():
    os.makedirs(os.path.join(BASE_DIR, "build"), exist_ok=True)
    parts = collect_parts()

    # 生成 LaTeX 内容
    for part in parts:
        part["readme_tex"] = md_to_latex(part["readme"]) if part["readme"] else ""
        chapters_data = []
        for chap in part["chapters"]: # chap 是章节(md)的完整路径
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
