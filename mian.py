#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import csv
import time
import datetime
import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_DIR = os.path.join(BASE_DIR, "sources")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

M3U_FILE = os.path.join(OUTPUT_DIR, "result.m3u")
TXT_FILE = os.path.join(OUTPUT_DIR, "result.txt")

ENABLE_HEALTH_CHECK = False
HTTP_TIMEOUT = 5

ALLOWED_COUNTRIES = {"中国", "China", "CN"}

ALLOWED_RES_KEYWORDS = [
    "1080", "1080p", "1920x1080",
    "720", "720p", "1280x720",
]


# ==========================
# 分类规则
# ==========================

def classify_channel(name: str, group: str) -> str:
    n = name.lower()

    if "贵州" in name:
        return "贵州地方频道"

    if n.startswith("cctv") or "中央电视台" in name:
        return "中央电视台"

    if "卫视" in name:
        return "卫视频道"

    if any(k in n for k in ["movie", "电影", "影视"]):
        return "影视频道"

    return "其他频道"


# ==========================
# 工具函数
# ==========================

def fetch_url(url: str) -> str:
    """抓取远程 URL 内容"""
    try:
        r = requests.get(url, timeout=HTTP_TIMEOUT)
        if r.status_code == 200:
            return r.text
    except:
        pass
    return ""


def parse_m3u_text(text: str):
    """解析 M3U 内容"""
    rows = []
    lines = text.splitlines()
    name = ""
    group = ""
    resolution = ""
    country = "中国"

    for line in lines:
        line = line.strip()
        if line.startswith("#EXTINF"):
            # 解析频道名称
            if "," in line:
                name = line.split(",")[-1].strip()
            else:
                name = "未知频道"
        elif line.startswith("http"):
            url = line
            rows.append({
                "name": name,
                "group": "",
                "country": country,
                "resolution": "",
                "url": url,
            })
    return rows


def parse_txt_text(text: str):
    """解析 TXT，每行一个 URL"""
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("http"):
            rows.append({
                "name": "未命名频道",
                "group": "",
                "country": "中国",
                "resolution": "",
                "url": line,
            })
    return rows


def read_csv_file(path: str):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for line in reader:
            if len(line) < 5:
                continue
            name, group, country, resolution, url = [x.strip() for x in line[:5]]
            if not name or not url:
                continue
            rows.append({
                "name": name,
                "group": group,
                "country": country,
                "resolution": resolution,
                "url": url,
            })
    return rows


def load_all_sources():
    """自动读取 CSV / TXT / M3U / URL"""
    all_rows = []

    for root, _, files in os.walk(SOURCE_DIR):
        for f in files:
            path = os.path.join(root, f)

            # CSV
            if f.endswith(".csv"):
                all_rows.extend(read_csv_file(path))

            # TXT
            elif f.endswith(".txt"):
                with open(path, "r", encoding="utf-8") as fp:
                    text = fp.read()
                all_rows.extend(parse_txt_text(text))

            # M3U
            elif f.endswith(".m3u") or f.endswith(".m3u8"):
                with open(path, "r", encoding="utf-8") as fp:
                    text = fp.read()
                all_rows.extend(parse_m3u_text(text))

    # 处理 sources/ 里直接写的 URL（远程源站）
    for root, _, files in os.walk(SOURCE_DIR):
        for f in files:
            path = os.path.join(root, f)
            with open(path, "r", encoding="utf-8") as fp:
                for line in fp:
                    line = line.strip()
                    if line.startswith("http"):
                        text = fetch_url(line)
                        if "#EXTM3U" in text:
                            all_rows.extend(parse_m3u_text(text))
                        else:
                            all_rows.extend(parse_txt_text(text))

    return all_rows


def filter_and_dedup(rows):
    seen = set()
    result = []

    for item in rows:
        name = item["name"]
        group = item["group"]
        country = item["country"]
        resolution = item["resolution"]
        url = item["url"]

        if not url.startswith("http"):
            continue

        new_group = classify_channel(name, group)
        item["group"] = new_group

        key = (name, url)
        if key in seen:
            continue
        seen.add(key)

        result.append(item)

    return result


def ensure_output_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR, exist_ok=True)


def generate_m3u(channels, filepath):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = ["#EXTM3U", f"# Generated at {now}"]

    for ch in channels:
        name = ch["name"]
        group = ch["group"]
        url = ch["url"]
        extinf = f'#EXTINF:-1 tvg-id="" tvg-name="{name}" group-title="{group}",{name}'
        lines.append(extinf)
        lines.append(url)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def generate_txt(channels, filepath):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [f"# 更新时间: {now}"]

    for ch in channels:
        lines.append(f"{ch['name']},{ch['group']},{ch['url']}")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    start = time.time()
    ensure_output_dir()

    rows = load_all_sources()
    channels = filter_and_dedup(rows)

    generate_m3u(channels, M3U_FILE)
    generate_txt(channels, TXT_FILE)

    print(f"完成，共 {len(channels)} 个频道，用时 {time.time() - start:.2f}s")


if __name__ == "__main__":
    main()
