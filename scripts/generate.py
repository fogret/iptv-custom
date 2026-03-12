#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import csv
import time
import datetime
import requests

# ==========================
# 仓库适配配置
# ==========================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SOURCE_DIR = os.path.join(BASE_DIR, "sources")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

M3U_FILE = os.path.join(OUTPUT_DIR, "result.m3u")
TXT_FILE = os.path.join(OUTPUT_DIR, "result.txt")

ENABLE_HEALTH_CHECK = False
HTTP_TIMEOUT = 3

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

    return ""


# ==========================
# 工具函数
# ==========================

def is_url_alive(url: str) -> bool:
    if not ENABLE_HEALTH_CHECK:
        return True
    try:
        r = requests.get(url, timeout=HTTP_TIMEOUT, stream=True)
        return r.status_code < 400
    except:
        return False


def match_resolution(resolution: str, url: str) -> bool:
    text = (resolution or "") + " " + url
    text = text.lower()
    return any(k in text for k in ALLOWED_RES_KEYWORDS)


def read_csv_file(path: str):
    rows = []
    if not os.path.exists(path):
        return rows

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
    all_rows = []
    for root, _, files in os.walk(SOURCE_DIR):
        for f in files:
            if f.endswith(".csv"):
                path = os.path.join(root, f)
                all_rows.extend(read_csv_file(path))
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

        if country not in ALLOWED_COUNTRIES:
            continue

        new_group = classify_channel(name, group)
        if not new_group:
            continue

        if not match_resolution(resolution, url):
            continue

        key = (name, url)
        if key in seen:
            continue
        seen.add(key)

        if not is_url_alive(url):
            continue

        item["group"] = new_group
        result.append(item)

    return result


def ensure_output_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR, exist_ok=True)


def generate_m3u(channels, filepath):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = []
    lines.append("#EXTM3U")
    lines.append(f"# Generated at {now}")

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
