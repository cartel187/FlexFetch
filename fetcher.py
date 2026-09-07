import requests
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configuration
URL_FILE = "playlists.txt"
OUTPUT_DIR = "playlists"
MERGED_FILE = "merged.m3u"

def get_robust_session():
    session = requests.Session()
    # Configure Retries: 3 attempts, with increasing delay between them
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def fetch_all():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    if not os.path.exists(URL_FILE):
        print(f"Error: {URL_FILE} not found.")
        return

    with open(URL_FILE, "r") as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    session = get_robust_session()
    # Standard high-compatibility browser header
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    }

    merged_lines = ["#EXTM3U"]

    for i, url in enumerate(urls):
        try:
            print(f"Fetching {i+1}/{len(urls)}: {url}")
            # 15 second timeout to prevent hanging on dead links
            response = session.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            content = response.text
            
            # Save individual copy
            with open(f"{OUTPUT_DIR}/source_{i+1}.m3u", "w", encoding="utf-8") as f_out:
                f_out.write(content)

            # Process for merging
            lines = content.splitlines()
            for line in lines:
                clean_line = line.strip()
                # Skip the header of the sub-files so they don't break the merged file
                if clean_line and not clean_line.startswith("#EXTM3U"):
                    merged_lines.append(clean_line)

        except Exception as e:
            print(f"Skipping {url} due to error: {e}")

    # Write the master file
    with open(MERGED_FILE, "w", encoding="utf-8") as f_merged:
        f_merged.write("\n".join(merged_lines))
    print(f"Successfully merged {len(urls)} sources into {MERGED_FILE}")

if __name__ == "__main__":
    fetch_all()
