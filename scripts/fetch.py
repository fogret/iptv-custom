import os
from datetime import datetime

sources_dir = "sources"
output_dir = "output"

os.makedirs(output_dir, exist_ok=True)

m3u_path = os.path.join(output_dir, "result.m3u")
txt_path = os.path.join(output_dir, "result.txt")
info_path = os.path.join(output_dir, "info.txt")
index_path = os.path.join(output_dir, "index.html")

channels = []

# 读取 sources 目录下所有 txt/m3u 文件
for filename in os.listdir(sources_dir):
    filepath = os.path.join(sources_dir, filename)

    if filename.endswith(".txt"):
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and "," in line:
                    name, url = line.split(",", 1)
                    channels.append((name.strip(), url.strip()))

    elif filename.endswith(".m3u"):
        with open(filepath, "r", encoding="utf-8") as f:
            name = None
            for line in f:
                line = line.strip()
                if line.startswith("#EXTINF"):
                    parts = line.split(",", 1)
                    if len(parts) == 2:
                        name = parts[1].strip()
                elif line.startswith("http") and name:
                    channels.append((name, line))
                    name = None

# 生成 result.m3u
with open(m3u_path, "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n")
    for name, url in channels:
        f.write(f'#EXTINF:-1,{name}\n{url}\n')

# 生成 result.txt
with open(txt_path, "w", encoding="utf-8") as f:
    for name, url in channels:
        f.write(f"{name},{url}\n")

# 生成 info.txt
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
with open(info_path, "w", encoding="utf-8") as f:
    f.write(f"更新时间：{now}\n")
    f.write(f"频道数量：{len(channels)}\n")

# 自动生成 index.html（解决 GitHub Pages 404 的关键）
html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>IPTV Output</title>
</head>
<body>
    <h1>IPTV 自动更新目录</h1>
    <p>更新时间：{now}</p>

    <ul>
        <li><a href="result.m3u">result.m3u（M3U 播放列表）</a></li>
        <li><a href="result.txt">result.txt（TXT 链接列表）</a></li>
        <li><a href="info.txt">info.txt（频道信息）</a></li>
    </ul>

    <p>本页面由 GitHub Actions 自动生成。</p>
</body>
</html>
"""

with open(index_path, "w", encoding="utf-8") as f:
    f.write(html_content)
