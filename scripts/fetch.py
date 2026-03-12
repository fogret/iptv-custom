import os
import requests

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

def merge_and_dedup(contents):
    lines = []
    seen = set()
    for content in contents:
        for line in content.splitlines():
            if line.startswith("#EXTINF") or line.startswith("http"):
                if line not in seen:
                    seen.add(line)
                    lines.append(line)
    return "\n".join(lines)

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
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(result)

    print("Done. Output saved to", OUTPUT_FILE)

if __name__ == "__main__":
    main()
