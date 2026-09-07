import requests
import os
import re
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
try:
    from filter_config import FILTERS
except ImportError:
    FILTERS = {}

def parse_m3u_attributes(line):
    """Extracts attributes like group-title, tvg-logo from #EXTINF line"""
    attrs = {}
    # Use regex to find key="value" patterns
    matches = re.findall(r'(\S+?)="(.+?)"', line)
    for key, value in matches:
        attrs[key] = value
    return attrs

def fetch_and_filter():
    url_file = "playlist.txt" if os.path.exists("playlist.txt") else "playlists.txt"
    merged_file = "merged.m3u"
    
    if not os.path.exists(url_file): return

    with open(url_file, "r") as f:
        lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]

    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=Retry(total=5, backoff_factor=1)))
    headers = {'User-Agent': 'TiviMate/4.7.0 (Linux; Android 11)'}

    merged_content = ["#EXTM3U"]

    for i, line in enumerate(lines):
        name_label, url = line.split("|", 1) if "|" in line else (f"list{i+1}", line)
        name_label = name_label.strip()
        url = url.strip()
        
        # Get rules for this specific playlist
        rule = FILTERS.get(name_label.lower(), {})
        
        try:
            print(f"🌀 Processing {name_label} with filters...")
            response = session.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            raw_lines = response.text.splitlines()
            filtered_lines = ["#EXTM3U"]
            
            for j in range(len(raw_lines)):
                if raw_lines[j].startswith("#EXTINF"):
                    inf_line = raw_lines[j]
                    url_line = raw_lines[j+1] if j+1 < len(raw_lines) else ""
                    
                    attrs = parse_m3u_attributes(inf_line)
                    current_group = attrs.get("group-title", "")
                    
                    # 1. Filter by Group
                    if rule.get("keep_groups") and current_group not in rule["keep_groups"]:
                        continue # Skip this channel
                    
                    # 2. Modify Group Name
                    if rule.get("rename_group"):
                        inf_line = inf_line.replace(f'group-title="{current_group}"', f'group-title="{rule["rename_group"]}"')
                    
                    # 3. Modify Logo
                    if rule.get("force_logo"):
                        old_logo = attrs.get("tvg-logo", "")
                        inf_line = inf_line.replace(f'tvg-logo="{old_logo}"', f'tvg-logo="{rule["force_logo"]}"')
                    
                    # 4. Modify Channel Name (Prefix)
                    if rule.get("name_prefix"):
                        # Find the part after the last comma
                        parts = inf_line.rsplit(",", 1)
                        if len(parts) > 1:
                            inf_line = f"{parts[0]},{rule['name_prefix']}{parts[1]}"

                    filtered_lines.append(inf_line)
                    filtered_lines.append(url_line)
                    
                    # Add to merged content (skipping header)
                    merged_content.append(inf_line)
                    merged_content.append(url_line)

            # Save individual filtered file
            with open(f"{name_label.lower().replace(' ', '_')}.m3u", "w", encoding="utf-8") as f_out:
                f_out.write("\n".join(filtered_lines))
            
        except Exception as e:
            print(f"❌ Error on {name_label}: {e}")

    with open(merged_file, "w", encoding="utf-8") as f_merge:
        f_merge.write("\n".join(merged_content))
    print("🏁 Beast Filtering Complete.")

if __name__ == "__main__":
    fetch_and_filter()
