def fetch_url(url):
    try:
        resp = requests.get(url, timeout=5, stream=True, allow_redirects=True)

        if resp.status_code != 200:
            return False

        ctype = resp.headers.get("Content-Type", "").lower()
        if "mpegurl" in ctype or "m3u8" in ctype:
            return True

        first_bytes = resp.raw.read(20, decode_content=True)
        if b"#EXTM3U" in first_bytes:
            return True

        if b".ts" in first_bytes:
            return True

    except:
        pass

    return False
