# Configuration for specific playlists
# Key must match the 'Name' used in your playlist.txt
FILTERS = {
    "zio": {
        "keep_groups": ["Sports", "Movies"], # Only fetch these groups. Leave empty [] to keep all.
        "rename_group": "Sflex VIP",         # Rename all kept groups to this
        "force_logo": "https://mysite.com/logo.png", # Replace all logos with this
        "name_prefix": "[VIP] "              # Add prefix to channel names
    },
    "sony": {
        "keep_groups": ["Entertainment"],
        "rename_group": "Sony Network",
        "force_logo": None,                  # Keep original logos
        "name_prefix": ""
    }
}
