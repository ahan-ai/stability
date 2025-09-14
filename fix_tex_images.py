import re
import os
import urllib.request

# 路径设置
tex_file = "docs/_build/latex/stability.tex"   # Sphinx 生成的 tex 文件
img_dir = "docs/_build/latex/images_local"     # 本地图片保存目录
os.makedirs(img_dir, exist_ok=True)

# 读取 tex 文件
with open(tex_file, "r", encoding="utf-8") as f:
    content = f.read()

# 匹配所有 \includegraphics[...]{} 里的 URL
pattern = re.compile(r'\\includegraphics(?:\[.*?\])?\{(https?://.*?)\}')
matches = pattern.findall(content)

for i, url in enumerate(matches, start=1):
    # 本地文件名
    ext = os.path.splitext(url)[-1].split('?')[0] or ".png"
    local_name = f"img_{i}{ext}"
    local_path = os.path.join(img_dir, local_name)

    print(f"Downloading {url} -> {local_path}")
    try:
        urllib.request.urlretrieve(url, local_path)
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        continue

    # 替换 tex 中的路径
    content = content.replace(url, os.path.join("images_local", local_name).replace("\\", "/"))

# 写回 tex 文件
with open(tex_file, "w", encoding="utf-8") as f:
    f.write(content)

print("替换完成，请重新 make latexpdf")

