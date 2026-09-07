import requests
import os
import re
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def fetch_all():
    # Supports both names
    url_file = "playlist.txt" if os.path.exists("playlist.txt") else "playlists.txt"
    merged_file = "merged.m3u"
    
    if not os.path.exists(url_file):
        print(f"❌ Error: {url_file} not found.")
        return

    with open(url_file, "r") as f:
        lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]

    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))
    
    # "Beast" Headers: Mimics a high-end IPTV Player (TiviMate/OTT Navigator style)
    headers = {
        'User-Agent': 'TiviMate/4.7.0 (Linux; Android 11; Nvidia Shield TV Pro)',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        'X-Requested-With': 'ar.tvplayer.tv'
    }

    merged_content = ["#EXTM3U"]

    for i, line in enumerate(lines):
        # Support "Name | URL" or just "URL"
        if "|" in line:
            name, url = line.split("|", 1)
            name = name.strip().replace(" ", "_").lower()
            url = url.strip()
        else:
            name = f"playlist{i+1}"
            url = line.strip()

        filename = f"{name}.m3u"

        try:
            print(f"🚀 Fetching {name}: {url}")
            response = session.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            raw_text = response.text
            
            # 1. Save Individual File (e.g., sony.m3u)
            with open(filename, "w", encoding="utf-8") as f_ind:
                f_ind.write(raw_text)
            print(f"✅ Saved individual: {filename}")

            # 2. Prepare for Merged File
            # We strip the #EXTM3U header from sub-files to keep the merge clean
            for content_line in raw_text.splitlines():
                if content_line.strip() and not content_line.startswith("#EXTM3U"):
                    merged_content.append(content_line.strip())

        except Exception as e:
            print(f"❌ Failed {name}: {e}")

    # 3. Save Master Merged File
    with open(merged_file, "w", encoding="utf-8") as f_merge:
        f_merge.write("\n".join(merged_content))
    
    print(f"🏁 Process Complete. Merged file: {merged_file}")

if __name__ == "__main__":
    fetch_all()
