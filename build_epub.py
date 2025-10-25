import os
import yaml
import hashlib
import re
import urllib.request
from ebooklib import epub
import markdown2  # pip install markdown2

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHAPTERS_DIR = os.path.join(BASE_DIR, "chapters")
BUILD_DIR = os.path.join(BASE_DIR, "build")
MEDIA_DIR = os.path.join(BUILD_DIR, "media")
CSS_PATH = os.path.join(BASE_DIR, "css/github-markdown-light.css")
OUTPUT_EPUB = os.path.join(BASE_DIR, "book.epub")
DEFAULT_IMAGE = os.path.join(BASE_DIR, "images/empty.png")

os.makedirs(BUILD_DIR, exist_ok=True)
os.makedirs(MEDIA_DIR, exist_ok=True)

# 下载远程图片到本地 media 文件夹
def download_image(url):
    h = hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]
    fname = f"img-{h}.jpg"
    out_path = os.path.join(MEDIA_DIR, fname)
    if os.path.exists(out_path):
        return out_path
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
        with open(out_path, "wb") as f:
            f.write(data)
        return out_path
    except Exception as e:
        print("⚠️ 下载图片失败:", url, e)
        return DEFAULT_IMAGE

# 替换 Markdown 图片为本地路径
def localize_images(md_text):
    img_re = re.compile(r'!\[([^\]]*)\]\((\S+?)\)')
    def repl(m):
        alt, url = m.groups()
        if url.startswith("http"):
            local = download_image(url)
            return f'![{alt}]({local})'
        else:
            return m.group(0)
    return img_re.sub(repl, md_text)

# 读取 book.yaml
def read_book_yaml():
    yaml_path = os.path.join(BASE_DIR, "book.yaml")
    if not os.path.exists(yaml_path):
        raise FileNotFoundError("book.yaml 不存在")
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data

# 将 Markdown 转 HTML，支持表格、代码块、脚注、删除线
def md_to_html(md_text):
    extras = [
        "tables",                 # 表格
        "fenced-code-blocks",     # ``` 代码块
        "footnotes",              # 脚注
        "strike",                 # 删除线
        "cuddled-lists",          # 紧挨的列表
    ]
    return markdown2.markdown(md_text, extras=extras)

# 生成 EPUB
def build_epub(book_data):
    book = epub.EpubBook()
    book.set_identifier("id123456")
    book.set_title(book_data.get("title", "未命名书籍"))
    book.set_language("zh")
    book.add_author(book_data.get("author", "佚名"))

    # 添加 CSS
    if os.path.exists(CSS_PATH):
        with open(CSS_PATH, "r", encoding="utf-8") as f:
            style = epub.EpubItem(
                uid="style_nav",
                file_name="style/style.css",
                media_type="text/css",
                content=f.read()
            )
            book.add_item(style)

    spine = ["nav"]
    toc = []

    for part_idx, part in enumerate(book_data.get("parts", []), 1):
        part_title = part.get("name", f"Part {part_idx}")
        part_path = os.path.join(CHAPTERS_DIR, part["path"])

        # Part 前言
        readme_file = os.path.join(part_path, "readme.md")
        part_content = ""
        if os.path.exists(readme_file):
            part_content = localize_images(open(readme_file, "r", encoding="utf-8").read())
        part_html = md_to_html(f"# {part_title}\n\n{part_content}")
        part_item = epub.EpubHtml(title=part_title, file_name=f"part{part_idx}_intro.xhtml", content=part_html)
        book.add_item(part_item)
        spine.append(part_item)

        # Chapters
        part_chapters = []
        for ch_idx, ch in enumerate(part.get("chapters", []), 1):
            ch_file = os.path.join(part_path, ch["file"])
            ch_name = ch.get("name", os.path.splitext(ch["file"])[0])
            if os.path.exists(ch_file):
                ch_md = localize_images(open(ch_file, "r", encoding="utf-8").read())
                ch_html = md_to_html(f"# {ch_name}\n\n{ch_md}")
                ch_item = epub.EpubHtml(title=ch_name, file_name=f"part{part_idx}_ch{ch_idx}.xhtml", content=ch_html)
                book.add_item(ch_item)
                spine.append(ch_item)
                part_chapters.append(ch_item)

        # 将 Part + Chapters 添加到 TOC
        toc.append((part_item, part_chapters))  # 元组表示嵌套

    # 设置 TOC 和 spine
    book.toc = toc
    book.spine = spine

    # 导航
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # 封面
    cover_path = os.path.join(BASE_DIR, "images/cover.png")
    if os.path.exists(cover_path):
        book.set_cover("cover.png", open(cover_path, "rb").read())

    # 写入 EPUB 文件
    epub.write_epub(OUTPUT_EPUB, book, {})
    print(f"\n✅ EPUB 已生成：{OUTPUT_EPUB}")

def main():
    book_data = read_book_yaml()
    build_epub(book_data)

if __name__ == "__main__":
    main()
