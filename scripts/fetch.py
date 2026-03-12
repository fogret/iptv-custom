import os
import requests
import re
from datetime import datetime

SOURCE_DIR = "sources"
OUTPUT_M3U = "output/result.m3u"
OUTPUT_TXT = "output/result.txt"
OUTPUT_INFO = "output/info.txt"
README = "README.md"

# 分类关键词
CCTV = ["CCTV", "CGTN"]
SATELLITE = ["卫视"]
DIGITAL = ["纪实", "都市", "新闻", "影视", "公共", "法治", "生活", "科教"]
MOVIE = ["电影", "CHC"]
LOCAL = ["贵州", "贵阳", "上海", "北京", "广东", "深圳", "湖南", "湖北", "江苏", "浙江"]

# 只保留 1080P / 720P
QUALITY_KEYWORDS = ["1080", "1080p", "720", "720p"]

def load_sources():
    urls = []
    for file in os.listdir(SOURCE_DIR):
        if file.endswith(".txt"):
            with open(os.path.join(SOURCE_DIR, file), "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        urls.append(line)
    return urls

def detect_category(name):
    if any(k in name for k in CCTV):
        return "中央电视台"
    if any(k in name for k in SATELLITE):
        return "卫视频道"
    if any(k in name for k in MOVIE):
        return "电影频道"
    if any(k in name for k in DIGITAL):
        return "数字频道"
    if any(k in name for k in LOCAL):
        return "地方频道"
    return "其它"

def parse_m3u(text):
    channels = []
    pending_extinf = None

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        if line.startswith("#EXTINF"):
            pending_extinf = line
            continue

        if line.startswith("http"):
            if pending_extinf:
                name = pending_extinf.split(",")[-1].strip()
                channels.append((name, pending_extinf, line))
            pending_extinf = None

    return channels

def add_group_title(extinf, category):
    idx = extinf.rfind(',')
    if idx == -1:
        return extinf
    return extinf[:idx] + f' group-title="{category}"' + extinf[idx:]

def is_quality_ok(name, url):
    text = (name + url).lower()
    return any(q in text for q in QUALITY_KEYWORDS)

def main():
    urls = load_sources()
    all_channels = []
    seen = set()

    for url in urls:
        try:
            resp = requests.get(url, timeout=6)
            if resp.status_code == 200:
                channels = parse_m3u(resp.text)
                for name, extinf, link in channels:
                    if link not in seen and is_quality_ok(name, link):
                        seen.add(link)
                        all_channels.append((name, extinf, link))
        except:
            pass

    categorized = {
        "中央电视台": [],
        "卫视频道": [],
        "数字频道": [],
        "电影频道": [],
        "地方频道": [],
        "其它": []
    }

    for name, extinf, link in all_channels:
        cat = detect_category(name)
        extinf2 = add_group_title(extinf, cat)
        categorized[cat].append((extinf2, link))

    os.makedirs("output", exist_ok=True)

    # 写 M3U
    with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n\n")
        for cat, items in categorized.items():
            for extinf, link in items:
                f.write(extinf + "\n")
                f.write(link + "\n")
            f.write("\n")

    # 写 TXT
    with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
        for _, items in categorized.items():
            for _, link in items:
                f.write(link + "\n")

    # 写 info.txt（只保留更新时间）
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(OUTPUT_INFO, "w", encoding="utf-8") as f:
        f.write(f"更新时间：{now}\n")

    # 更新 README（修正正则，避免误替换）
    if os.path.exists(README):
        with open(README, "r", encoding="utf-8") as f:
            readme = f.read()

        total = sum(len(v) for v in categorized.values())

        readme = re.sub(r"更新时间：.*?\n", f"更新时间：{now}\n", readme)
        readme = re.sub(r"频道总数：.*?\n", f"频道总数：{total}\n", readme)

        with open(README, "w", encoding="utf-8") as f:
            f.write(readme)

    print("Done.")

if __name__ == "__main__":
    main()
