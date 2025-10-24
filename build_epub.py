import os
import subprocess
import yaml
import hashlib
import re
import urllib.request
import urllib.parse
import mimetypes

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHAPTERS_DIR = os.path.join(BASE_DIR, "chapters")
BUILD_DIR = os.path.join(BASE_DIR, "build")
MEDIA_DIR = os.path.join(BUILD_DIR, "media")
CSS_PATH = os.path.join(BASE_DIR, "css/github-markdown-light.css")
OUTPUT_EPUB = os.path.join(BASE_DIR, "book.epub")
DEFAULT_IMAGE = os.path.join(BASE_DIR, "images/empty.png")

os.makedirs(BUILD_DIR, exist_ok=True)
os.makedirs(MEDIA_DIR, exist_ok=True)

# 从 book.yaml 读取章节结构
def collect_parts_from_yaml():
    yaml_path = os.path.join(BASE_DIR, "book.yaml")
    if not os.path.exists(yaml_path):
        raise FileNotFoundError("book.yaml 不存在")

    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    parts = []
    for part in data.get("parts", []):
        part_title = part.get("name", "")
        part_path = os.path.join(CHAPTERS_DIR, part["path"])
        chapters = []
        for ch in part.get("chapters", []):
            ch_file = os.path.join(part_path, ch["file"])
            ch_name = ch.get("name", os.path.splitext(ch["file"])[0])
            if os.path.exists(ch_file):
                chapters.append((ch_name, ch_file))
            else:
                print(f"⚠️ 找不到章节文件: {ch_file}")
        parts.append((part_title, chapters))
    return data.get("title", "未命名书籍"), data.get("author", "佚名"), parts


# 下载图片（可选）
def _download_image_with_cache(url):
    """下载远程图片到 media 目录"""
    h = hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]
    fname = f"img-{h}.jpg"
    out_path = os.path.join(MEDIA_DIR, fname)
    if os.path.exists(out_path):
        return os.path.relpath(out_path, BUILD_DIR)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
        with open(out_path, "wb") as f:
            f.write(data)
        return os.path.relpath(out_path, BUILD_DIR)
    except Exception as e:
        print("⚠️ 下载图片失败:", url, e)
        return os.path.relpath(DEFAULT_IMAGE, BUILD_DIR)


# 替换 MD 图片为本地路径
def _localize_images_in_md(md_path):
    with open(md_path, "r", encoding="utf-8") as f:
        text = f.read()

    img_re = re.compile(r'!\[([^\]]*)\]\((\S+?)\)')
    def repl(m):
        alt, url = m.groups()
        if url.startswith("http"):
            local = _download_image_with_cache(url)
            return f'![{alt}]({local})'
        else:
            return m.group(0)

    text = img_re.sub(repl, text)
    return text


# 拼接所有章节
def combine_all_markdown(parts):
    combined_md = os.path.join(BUILD_DIR, "combined.md")
    with open(combined_md, "w", encoding="utf-8") as out:
        for part_title, chapters in parts:
            out.write(f"# {part_title}\n\n")
            for ch_name, ch_path in chapters:
                out.write(f"## {ch_name}\n\n")
                md_text = _localize_images_in_md(ch_path)
                out.write(md_text)
                out.write("\n\n")
    return combined_md


def main():
    title, author, parts = collect_parts_from_yaml()
    combined_md = combine_all_markdown(parts)

    # 先检查内容是否真的写入
    with open(combined_md, "r", encoding="utf-8") as f:
        preview = f.read(500)
        print("\n✅ 预览前500字符：\n", preview[:500])

    # Pandoc 转 EPUB
    cmd = [
        "pandoc",
        combined_md,
        "-f", "markdown",
        "-t", "epub3",
        "-o", OUTPUT_EPUB,
        "--toc",
        "--toc-depth=2",
        "--metadata", f"title={title}",
        "--metadata", f"author={author}",
    ]

    if os.path.exists(CSS_PATH):
        cmd.append(f"--css={CSS_PATH}")
    if os.path.exists(os.path.join(BASE_DIR, "images/cover.png")):
        cmd.append("--epub-cover-image=images/cover.png")

    print("\n📘 正在执行命令：", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print("❌ Pandoc 错误：", result.stderr)
    else:
        print(f"\n✅ EPUB 已生成：{OUTPUT_EPUB}")


if __name__ == "__main__":
    main()
