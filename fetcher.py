import requests
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def fetch_all():
    url_file = "playlists.txt"
    output_dir = "playlists"
    merged_file = "merged.m3u"

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if not os.path.exists(url_file):
        print(f"CRITICAL ERROR: {url_file} not found in the root directory.")
        return

    with open(url_file, "r") as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    if not urls:
        print("No URLs found in playlists.txt")
        return

    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    merged_lines = ["#EXTM3U"]

    for i, url in enumerate(urls):
        try:
            print(f"Attempting to fetch: {url}")
            response = session.get(url, headers=headers, timeout=20)
            response.raise_for_status()
            
            content = response.text
            print(f"Success! Received {len(content)} bytes.")

            # Save individual
            filename = f"source_{i+1}.m3u"
            with open(os.path.join(output_dir, filename), "w", encoding="utf-8") as f_out:
                f_out.write(content)

            # Process lines
            for line in content.splitlines():
                if line.strip() and not line.strip().startswith("#EXTM3U"):
                    merged_lines.append(line.strip())

        except Exception as e:
            print(f"FAILED to fetch {url}: {e}")

    # Write merged file
    with open(merged_file, "w", encoding="utf-8") as f_merged:
        f_merged.write("\n".join(merged_lines))
    
    print(f"DONE! Created {merged_file} with {len(merged_lines)} lines.")

if __name__ == "__main__":
    fetch_all()
