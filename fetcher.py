import requests
import os

URL_FILE = "playlists.txt"
OUTPUT_DIR = "playlists"
MERGED_FILE = "merged.m3u"

def fetch_playlists():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Read URLs from file
    with open(URL_FILE, "r") as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    merged_content = ["#EXTM3U"]
    headers = {'User-Agent': 'Mozilla/5.0'}

    for i, url in enumerate(urls):
        try:
            print(f"Fetching: {url}")
            r = requests.get(url, headers=headers, timeout=30)
            r.raise_for_status()
            
            # Save individual copy
            with open(f"{OUTPUT_DIR}/playlist_{i+1}.m3u", "w", encoding="utf-8") as f_out:
                f_out.write(r.text)

            # Add to merged list (skipping the header of each file)
            lines = r.text.splitlines()
            for line in lines:
                if line.strip() and not line.startswith("#EXTM3U"):
                    merged_content.append(line)
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")

    # Write the final combined file
    with open(MERGED_FILE, "w", encoding="utf-8") as f_merged:
        f_merged.write("\n".join(merged_content))

if __name__ == "__main__":
    fetch_playlists()
