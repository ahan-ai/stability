import os
import subprocess
from jinja2 import Environment
import re
import urllib.request
import urllib.parse
import hashlib
import mimetypes
import yaml

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHAPTERS_DIR = os.path.join(BASE_DIR, "chapters")
BUILD_DIR = os.path.join(BASE_DIR, "build")
OUTPUT_TEX = os.path.join(BUILD_DIR, "book.tex")
OUTPUT_PDF = os.path.join(BASE_DIR, "book.pdf")
MEDIA_DIR = os.path.join(BUILD_DIR, "media")
DEFAULT_IMAGE = os.path.join(BASE_DIR, "images/empty.png")
IMAGE_CACHE = os.path.join(BASE_DIR, "images/cache")

def collect_parts_from_yaml():
    yaml_path = os.path.join(BASE_DIR, "book.yaml")
    if not os.path.exists(yaml_path):
        return None

    with open(yaml_path, "r", encoding="utf-8") as f:
        book_data = yaml.safe_load(f)

    parts = []
    for part in book_data.get("parts", []):
        part_name = part.get("name") or os.path.basename(part["path"])
        part_path = os.path.join(CHAPTERS_DIR, part["path"])
        readme_path = os.path.join(part_path, "README.md")
        readme = readme_path if os.path.exists(readme_path) else ""

        chapters = []
        for ch in part.get("chapters", []):
            ch_name = ch.get("name") or os.path.splitext(os.path.basename(ch["file"]))[0]
            print("ch_name:", ch_name)
            ch_file = os.path.join(part_path, ch["file"])
            if os.path.exists(ch_file):
                chapters.append({"title": ch_name, "path": ch_file})
            else:
                print(f"⚠️  警告: 找不到章节文件 {ch_file}")

        parts.append({
            "title": part_name,
            "readme": readme,
            "chapters": [c["path"] for c in chapters],
            "chapter_titles": [c["title"] for c in chapters]
        })

    return parts

def collect_parts_auto():
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

# ✅ 统一接口：优先从 book.yaml 读取，否则扫描
def collect_parts():
    parts = collect_parts_from_yaml()
    if parts:
        print("📘 使用 book.yaml 中定义的章节结构")
        return parts
    else:
        print("📗 未找到 book.yaml，自动扫描 chapters 目录结构")
        return collect_parts_auto()


def _download_image_with_cache(url, media_dir):
    """下载远程图片到 media_dir，返回本地相对路径（相对于BUILD_DIR），或 None。"""

    os.makedirs(IMAGE_CACHE, exist_ok=True)
    os.makedirs(media_dir, exist_ok=True)

    # 根据 URL 生成 hash
    h = hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]

    # -------- (1) 尝试从缓存目录中找到相同 hash 的文件（不论扩展名）--------
    cached_file = None
    for f in os.listdir(IMAGE_CACHE):
        if f.startswith(f"img-{h}"):
            cached_file = os.path.join(IMAGE_CACHE, f)
            break

    if cached_file and os.path.exists(cached_file):
        ext = os.path.splitext(cached_file)[1]
        out_path = os.path.join(media_dir, f"img-{h}{ext}")
        if not os.path.exists(out_path):
            try:
                with open(cached_file, "rb") as src, open(out_path, "wb") as dst:
                    dst.write(src.read())
            except Exception as e:
                print("warn: 复制缓存图片失败:", cached_file, e)
                return None
        rel = os.path.relpath(out_path, BUILD_DIR).replace("\\", "/")
        print("使用缓存图片:", url, "->", rel)
        return rel

    # -------- (2) 下载图片 --------
    default_image_path = os.path.relpath(DEFAULT_IMAGE, BUILD_DIR).replace("\\", "/")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
            ctype = resp.headers.get("Content-Type", "")
    except Exception as e:
        print("warn: 下载图片失败:", url, e)
        return default_image_path

    # -------- (3) 自动推断扩展名 --------
    # 优先从 Content-Type 判断
    ext = mimetypes.guess_extension(ctype.split(";")[0].strip()) if ctype else None
    # 如果没有，尝试从 URL 后缀判断
    if not ext:
        parsed = urllib.parse.urlparse(url)
        path_ext = os.path.splitext(parsed.path)[1]
        if path_ext and len(path_ext) <= 5:
            ext = path_ext
    # 如果仍无扩展名，默认 jpg
    if not ext:
        ext = ".jpg"

    fname = f"img-{h}{ext}"
    out_path = os.path.join(media_dir, fname)
    cached_path = os.path.join(IMAGE_CACHE, fname)

    # -------- (4) 写入文件并缓存 --------
    try:
        with open(out_path, "wb") as f, open(cached_path, "wb") as cache_f:
            f.write(data)
            cache_f.write(data)
        rel = os.path.relpath(out_path, BUILD_DIR).replace("\\", "/")
        print("下载新图片:", url, "->", rel)
        return rel
    except Exception as e:
        print("warn: 写文件失败:", out_path, e)
        return default_image_path


def _localize_images_in_md(md_path):
    """
    读取 md 文件：
      - 下载远程图片
      - 复制本地图片到 build/media
      - 替换为本地路径
    返回新 md 的路径（位于 build/ 下）。
    """
    with open(md_path, "r", encoding="utf-8") as f:
        text = f.read()

    # 确保 media 目录存在
    os.makedirs(MEDIA_DIR, exist_ok=True)
    md_dir = os.path.dirname(md_path)

    def _copy_local_image(src_path):
        """
        复制本地图片到 MEDIA_DIR 下，返回相对 build 的路径。
        """
        if not os.path.isabs(src_path):
            src_path = os.path.join(md_dir, src_path)
        src_path = os.path.normpath(src_path)

        if not os.path.exists(src_path):
            print(f"⚠️  找不到本地图片: {src_path}")
            return None

        # 保留文件名，用哈希避免冲突
        h = hashlib.sha1(src_path.encode("utf-8")).hexdigest()[:8]
        fname = f"local-{h}{os.path.splitext(src_path)[1]}"
        dst_path = os.path.join(MEDIA_DIR, fname)

        try:
            if not os.path.exists(dst_path):
                os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                with open(src_path, "rb") as src, open(dst_path, "wb") as dst:
                    dst.write(src.read())
            rel = os.path.relpath(dst_path, BUILD_DIR).replace("\\", "/")
            print(f"📸 本地图片已复制: {src_path} -> {rel}")
            return rel
        except Exception as e:
            print("⚠️  复制本地图片失败:", src_path, e)
            return None

    # 1) 处理标准 Markdown 图片语法 ![alt](url "title")
    #    这个 regex 适用于大多数情况（注意：若 url 包含未配对的括号，可能失效）
    md_img_re = re.compile(r'!\[([^\]]*)\]\((\S+?)(?:\s+"[^"]*")?\)')

    def md_repl(m):
        alt = m.group(1)
        url = m.group(2).strip()
        if url.startswith("<") and url.endswith(">"):
            url = url[1:-1]

        if url.lower().startswith("http"):
            local = _download_image_with_cache(url, MEDIA_DIR)
        else:
            local = _copy_local_image(url)
        return f'![{alt}]({local or url})'

    text = md_img_re.sub(md_repl, text)

    # 2) 处理 HTML <img src="..."> 的情况（Notion 导出有时会用这种）
    md_img_re = re.compile(r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>')
    def html_repl(m):
        url = m.group(1).strip()
        if url.lower().startswith("http"):
            local = _download_image_with_cache(url, MEDIA_DIR)
            if local:
                # 用 markdown 语法替换为普通图片引用（pandoc 更容易处理）
                return f'![]({local})'
            else:
                return m.group(0)
        else:
            return m.group(0)
    text = md_img_re.sub(html_repl, text)

    # 处理 HTML 图片 <img src="...">
    html_img_re = re.compile(r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>')
    def html_repl(m):
        url = m.group(1).strip()
        if url.lower().startswith("http"):
            local = _download_image_with_cache(url, MEDIA_DIR)
        else:
            local = _copy_local_image(url)
        return f'![]({local or url})'

    text = html_img_re.sub(html_repl, text)
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
            "--wrap=none",
            "--listings"
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

    # 5. 修正 \includegraphics，统一包裹一层 \pandocbounded
    def fix_graphics(match):
        # 原路径
        path = match.group(2).strip()

        # 路径转为绝对路径再相对于 BASE_DIR
        abs_path = os.path.abspath(os.path.join(BUILD_DIR, path)) if not os.path.isabs(path) else path
        rel_path = os.path.relpath(abs_path, BASE_DIR).replace("\\", "/")
        # 转义下划线
        rel_path = rel_path.replace("_", "\\_")

        # 固定选项
        options = "[keepaspectratio,width=\\linewidth]"

        # 返回单层 pandocbounded 包裹
        return f"\\includegraphics{options}{{{rel_path}}}"

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
        for i in range(len(part["chapters"])):
            chap = part["chapters"][i]# chap 是章节(md)的完整路径
            if part["chapter_titles"]:
                title = part["chapter_titles"][i]
            else:
                file_name = os.path.splitext(os.path.basename(chap))[0]
                title = file_name
            tex = md_to_latex(chap)
            # 获取章节标题
            # first_line = tex.strip().split("\n")[0]
            # title = first_line.replace("\\section{", "").replace("}", "") if first_line.startswith("\\section") else file_name
            
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
