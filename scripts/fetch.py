import os
import requests
import re

SOURCE_DIR = "sources"
OUTPUT_FILE = "output/result.m3u"

def fetch_url(url):
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            return resp.text
    except:
        pass
    return ""

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
    # 删除非标准字段 t-time / v-w / v-h
    line = re.sub(r'\s+t-time="[^"]*"', "", line)
    line = re.sub(r'\s+v-w="[^"]*"', "", line)
    line = re.sub(r'\s+v-h="[^"]*"', "", line)

    # 删除逗号后的空格
    line = re.sub(r',\s+', ',', line)

    return line

def merge_and_dedup(contents):
    result = ["#EXTM3U"]  # 必须的第一行

    seen = set()
    pending_extinf = None

    for content in contents:
        for raw in content.splitlines():
            line = raw.strip()
            if not line:
                continue

            # 处理 EXTINF
            if line.startswith("#EXTINF"):
                line = clean_extinf(line)
                pending_extinf = line
                continue

            # 处理 URL
            if line.startswith("http"):
                if pending_extinf:
                    pair = pending_extinf + "\n" + line
                    if pair not in seen:
                        seen.add(pair)
                        result.append(pending_extinf)
                        result.append(line)
                pending_extinf = None

    return "\n".join(result)

def main():
    urls = load_sources()
    contents = []

    for url in urls:
        print(f"Fetching: {url}")
        data = fetch_url(url)
        if data:
            contents.append(data)

    result = merge_and_dedup(contents)

    os.makedirs("output", exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8", newline="\n") as f:
        f.write(result)

    print("Done. Output saved to", OUTPUT_FILE)

if __name__ == "__main__":
    main()
