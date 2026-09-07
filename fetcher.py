import requests
import os
import re
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Attempt to load filters, fallback to empty if not found
try:
    from filter_config import FILTERS
except ImportError:
    FILTERS = {}

def get_session():
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))
    # Using a high-compatibility header
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Connection': 'keep-alive'
    })
    return session

def process_m3u(raw_text, rules):
    """
    Parses M3U while preserving exact URL integrity.
    """
    input_lines = raw_text.splitlines()
    output_lines = ["#EXTM3U"]
    
    current_inf = None
    
    for line in input_lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith("#EXTM3U"):
            continue
            
        if line.startswith("#EXTINF"):
            current_inf = line
            continue
            
        # If the line doesn't start with #, it is the URL
        if not line.startswith("#") and current_inf:
            # We have a pair: current_inf (metadata) + line (URL)
            
            # --- APPLY FILTERS HERE ---
            keep = True
            inf_to_save = current_inf
            
            # Extract group for filtering
            group_match = re.search(r'group-title="(.+?)"', inf_to_save)
            current_group = group_match.group(1) if group_match else ""
            
            # 1. Filter by Group
            if rules.get("keep_groups") and current_group not in rules["keep_groups"]:
                keep = False
            
            if keep:
                # 2. Rename Group
                if rules.get("rename_group"):
                    inf_to_save = re.sub(r'group-title=".+?"', f'group-title="{rules["rename_group"]}"', inf_to_save)
                
                # 3. Replace Logo
                if rules.get("force_logo"):
                    inf_to_save = re.sub(r'tvg-logo=".+?"', f'tvg-logo="{rules["force_logo"]}"', inf_to_save)
                
                # 4. Add Prefix to Name
                if rules.get("name_prefix"):
                    # The name is always after the last comma
                    parts = inf_to_save.rsplit(',', 1)
                    if len(parts) > 1:
                        inf_to_save = f"{parts[0]},{rules['name_prefix']}{parts[1]}"
                
                # Save the modified INF and the EXACT URL
                output_lines.append(inf_to_save)
                output_lines.append(line) # Exact URL preservation
            
            current_inf = None # Reset for next pair

    return "\n".join(output_lines)

def main():
    url_file = "playlist.txt" if os.path.exists("playlist.txt") else "playlists.txt"
    if not os.path.exists(url_file):
        print("No source file found.")
        return

    session = get_session()
    with open(url_file, "r") as f:
        sources = [l.strip() for l in f if l.strip() and not l.startswith("#")]

    all_merged_channels = []

    for i, source in enumerate(sources):
        name_label, url = source.split("|", 1) if "|" in source else (f"playlist{i+1}", source)
        name_label = name_label.strip().lower().replace(" ", "_")
        url = url.strip()
        
        rules = FILTERS.get(name_label, {})
        
        try:
            print(f"📡 Fetching: {name_label}")
            resp = session.get(url, timeout=30)
            resp.raise_for_status()
            
            # Process content
            filtered_data = process_m3u(resp.text, rules)
            
            # Save individual
            with open(f"{name_label}.m3u", "w", encoding="utf-8") as f_out:
                f_out.write(filtered_data)
                
            # Add to merge list (skip header for merging)
            merge_lines = filtered_data.splitlines()
            if len(merge_lines) > 1:
                all_merged_channels.extend(merge_lines[1:])
                
        except Exception as e:
            print(f"❌ Error on {name_label}: {e}")

    # Save merged
    with open("merged.m3u", "w", encoding="utf-8") as f_merge:
        f_merge.write("#EXTM3U\n" + "\n".join(all_merged_channels))
    
    print("✅ All playlists processed and URLs preserved.")

if __name__ == "__main__":
    main()
