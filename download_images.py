#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import requests

# 你的文档目录
DOCS_DIR = "docs"
# 本地图片保存目录
LOCAL_IMG_DIR = os.path.join(DOCS_DIR, "images_local")
os.makedirs(LOCAL_IMG_DIR, exist_ok=True)

# 匹配 Markdown / RST 图片 URL
IMG_PATTERN = re.compile(r'(!\[.*?\]\()(\s*https?://.*?)(\))')

def download_image(url, save_dir):
    try:
        filename = url.split("/")[-1].split("?")[0]
        local_path = os.path.join(save_dir, filename)
        if not os.path.exists(local_path):
            print(f"Downloading {url} -> {local_path}")
            r = requests.get(url, timeout=20)
            r.raise_for_status()
            with open(local_path, "wb") as f:
                f.write(r.content)
        else:
            print(f"Already exists: {local_path}")
        return os.path.relpath(local_path, DOCS_DIR).replace("\\", "/")
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return url  # 下载失败则保留原 URL

def process_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    new_content = content
    matches = IMG_PATTERN.findall(content)
    for full_match, url, closing in matches:
        local_path = download_image(url, LOCAL_IMG_DIR)
        new_content = new_content.replace(url, local_path)

    if new_content != content:
        print(f"Updating {filepath}")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)

def walk_docs():
    for root, _, files in os.walk(DOCS_DIR):
        for file in files:
            if file.endswith((".md", ".rst")):
                process_file(os.path.join(root, file))

if __name__ == "__main__":
    walk_docs()
    print("Done. All remote images replaced with local copies.")

