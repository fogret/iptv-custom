import os
import requests
import re
from datetime import datetime

SOURCE_DIR = "sources"
OUTPUT_M3U = "output/result.m3u"
OUTPUT_TXT = "output/result.txt"
OUTPUT_INFO = "output/info.txt"

# 分类关键词
CCTV = ["CCTV", "CGTN"]
SATELLITE = ["卫视"]
GUIZHOU = ["贵州", "贵阳"]
DIGITAL = ["纪实", "都市", "新闻", "影视", "公共", "法治", "生活", "科教"]
MOVIE = ["电影", "CHC"]

# 极速检测直播源是否可用（HEAD + 0.5 秒超时）
def is_alive(url):
    try:
        resp = requests.head(url, timeout=0.5, allow_redirects=True)
        return resp.status_code == 200
    except:
        return False


# 读取 sources 目录中的所有 URL
def load_sources():
    urls = []

    # ① 保留原有 sources/*.txt（原逻辑不变）
    for file in os.listdir(SOURCE_DIR):
        if file.endswith(".txt"):
            with open(os.path.join(SOURCE_DIR, file), "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        urls.append(line)

    # ② 在原有逻辑中追加抓取源（只加地址，不改逻辑）
    urls += [
        "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/cn.m3u",
        "https://raw.githubusercontent.com/iptv-org/iptv/master/index.m3u",
        "https://raw.githubusercontent.com/fanmingming/live/main/tv/m3u/global.m3u",
        "https://raw.githubusercontent.com/ChiSheng9/iptv/master/TV.m3u",
        "https://raw.githubusercontent.com/YueChan/Live/main/IPTV.m3u",
        "https://raw.githubusercontent.com/zhanghong1983/TVBOX/main/live.txt",
        "https://raw.githubusercontent.com/Ftindy/IPTV-URL/main/live.txt",
        "https://raw.githubusercontent.com/wwb521/live/main/tv.txt",
        "https://live.fanmingming.com/tv/m3u/global.m3u",
        "https://live.fanmingming.com/tv/m3u/ipv6.m3u"
    ]

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


# 合并、去重、过滤失效、分类（智能加速版 + TXT 支持）
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
    tested_channels = set()
    pending_extinf = None

    for content in contents:
        for raw in content.splitlines():
            line = raw.strip()
            if not line:
                continue

            # ① 支持 TXT 格式：频道名,URL
            if "," in line and not line.startswith("#EXTINF"):
                try:
                    name, url = line.split(",", 1)
                    name = name.strip()
                    url = url.strip()

                    if url.startswith("http"):
                        if name not in tested_channels:
                            if not is_alive(url):
                                continue
                            tested_channels.add(name)

                        cat = detect_category(name)
                        extinf = f'#EXTINF:-1 tvg-name="{name}" group-title="{cat}",{name}'
                        result[cat].append(extinf)
                        result[cat].append(url)
                        continue
                except:
                    pass

            # ② 标准 EXTINF
            if line.startswith("#EXTINF"):
                pending_extinf = clean_extinf(line)
                continue

            # ③ URL
            if line.startswith("http"):
                if pending_extinf:
                    name = pending_extinf.split(",")[-1]
                    pair = pending_extinf + "\n" + line

                    if pair not in seen:
                        seen.add(pair)

                        if name not in tested_channels:
