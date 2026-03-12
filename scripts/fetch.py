import os
import requests
import re

SOURCE_DIR = "sources"
OUTPUT_FILE = "output/result.m3u"

# 分类关键词
CCTV = ["CCTV", "CGTN"]
SATELLITE = ["卫视"]
GUIZHOU = ["贵州", "贵阳"]
DIGITAL = ["纪实", "都市", "新闻", "影视", "公共", "法治", "生活", "科教"]
MOVIE = ["电影", "CHC"]

def fetch_url(url):
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200 and "m3u8" in resp.text:
            return True
    except:
        pass
    return False

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

def clean_extinf(line):
    # 删除非标准字段
    line = re.sub(r'\s+t-time="[^"]*"', "", line)
    line = re.sub(r'\s+v-w="[^"]*"', "", line)
    line = re.sub(r'\s+v-h="[^"]*"', "", line)

    # 删除逗号后的空格
    line = re.sub(r',\s+', ',', line)

    return line

def detect_category(name):
    if any(k in name for k in CCTV):
        return "中央电视台"
    if any(k in name for k in GUIZHOU):
        return "贵州频道"
    if any(k in name for k in SATELLITE):
        return "卫视频道"
    if any(k in name for k in MOVIE):
        return "电影频道"
    return "数字频道"

def is_1080p(extinf, url):
    # 从 EXTINF 中判断
    if 'v-h="1080"' in extinf or 'v-w="1920"' in extinf:
        return True
    # URL 中包含 1080
    if "1080" in url:
        return True
    return False

def merge_and_dedup(contents):
    result = {"中央电视台": [], "卫视频道": [], "贵州频道": [], "数字频道": [], "电影频道": []}

    seen = set()
    pending_extinf = None

    for content in contents:
        for raw in content.splitlines():
            line = raw.strip()
            if not line:
                continue

            if line.startswith("#EXTINF"):
                line = clean_extinf(line)
                pending_extinf = line
                continue

            if line.startswith("http"):
                if pending_extinf:
                    name = pending_extinf.split(",")[-1]
                    pair = pending_extinf + "\n" + line

                    if pair not in seen:
                        seen.add(pair)

                        # 过滤非 1080P
                        if not is_1080p(pending_extinf, line):
                            pending_extinf = None
                            continue

                        # 检测是否可播放
                        if not fetch_url(line):
                            pending_extinf = None
                            continue

                        # 分类
                        cat = detect_category(name)
                        result[cat].append(pending_extinf)
                        result[cat].append(line)

                pending_extinf = None

    return result

def main():
    urls = load_sources()
    contents = []

    for url in urls:
        print(f"Fetching: {url}")
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                contents.append(resp.text)
        except:
            pass

    categorized = merge_and_dedup(contents)

    os.makedirs("output", exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8", newline="\n") as f:
        f.write("#EXTM3U\n\n")

        for cat, items in categorized.items():
            if items:
                f.write(f"# ------ {cat} ------\n")
                for line in items:
                    f.write(line + "\n")
                f.write("\n")

    print("Done. Output saved to", OUTPUT_FILE)

if __name__ == "__main__":
    main()
