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

# 快速检测直播源是否可用（极速版）
def is_alive(url):
    try:
        # 使用 HEAD 请求，不下载内容，速度极快
        resp = requests.head(url, timeout=1, allow_redirects=True)
        return resp.status_code == 200
    except:
        return False


# 读取 sources 目录中的所有 URL
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


# 清理 EXTINF
def clean_extinf(line):
    line = re.sub(r'\s+t-time="[^"]*"', "", line)
    line = re.sub(r'\s+v-w="[^"]*"', "", line)
    line = re.sub(r'\s+v-h="[^"]*"', "", line)
    line = re.sub(r',\s+', ',', line)
    return line


# 分类
def detect_category(name):
    if any(k in name for k in CCTV):
        return "中央电视台"
    if any(k in name for k in GUIZHOU):
        return "贵州频道"
    if any(k in name for k in SATELLITE):
        return "卫视频道"
    if any(k in name for k in MOVIE):
        return "电影频道"
    if any(k in name for k in DIGITAL):
        return "数字频道"
    return "其它"


# 合并、去重、过滤失效、分类
def merge_and_classify(contents):
    result = {
        "中央电视台": [],
        "卫视频道": [],
        "贵州频道": [],
        "数字频道": [],
        "电影频道": [],
        "其它": []
    }

    seen = set()
    pending_extinf = None

    for content in contents:
        for raw in content.splitlines():
            line = raw.strip()
            if not line:
                continue

            # EXTINF
            if line.startswith("#EXTINF"):
                pending_extinf = clean_extinf(line)
                continue

            # URL
            if line.startswith("http"):
                if pending_extinf:
                    name = pending_extinf.split(",")[-1]
                    pair = pending_extinf + "\n" + line

                    if pair not in seen:
                        seen.add(pair)

                        # 快速检测是否可播放
                        if not is_alive(line):
                            pending_extinf = None
                            continue

                        # 分类
                        cat = detect_category(name)

                        # 生成标准 M3U 格式 EXTINF
                        extinf = f'#EXTINF:-1 tvg-name="{name}" group-title="{cat}",{name}'

                        result[cat].append(extinf)
                        result[cat].append(line)

                pending_extinf = None

    return result


def main():
    urls = load_sources()
    contents = []

    for url in urls:
        print(f"Fetching: {url}")
        try:
            resp = requests.get(url, timeout=8)
            if resp.status_code == 200:
                contents.append(resp.text)
        except:
            pass

    categorized = merge_and_classify(contents)

    os.makedirs("output", exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8", newline="\n") as f:
        f.write("#EXTM3U\n\n")

        for cat, items in categorized.items():
            if items:
                for line in items:
                    f.write(line + "\n")
                f.write("\n")

    print("Done. Output saved to", OUTPUT_FILE)


if __name__ == "__main__":
    main()
